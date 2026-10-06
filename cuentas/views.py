import logging

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from .models import Perfil
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from .serializers import LoginSerializer, RegistroSerializer, UsuarioSerializer

logger = logging.getLogger(__name__)


def _token_y_usuario(user):
    token, _ = Token.objects.get_or_create(user=user)
    return {'token': token.key, 'usuario': UsuarioSerializer(user).data}


# Cada vista pública tiene su propio límite de peticiones (`throttle_scope`,
# ver DEFAULT_THROTTLE_RATES en settings) para frenar ataques de fuerza bruta.

@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def registro(request):
    serializer = RegistroSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(_token_y_usuario(user), status=status.HTTP_201_CREATED)


registro.cls.throttle_scope = 'registro'


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email'].strip()
    # Permite iniciar sesión por email aunque el username no sea el correo.
    try:
        username = User.objects.get(email__iexact=email).username
    except (User.DoesNotExist, User.MultipleObjectsReturned):
        username = email
    user = authenticate(
        request,
        username=username,
        password=serializer.validated_data['password'],
    )
    if user is None:
        return Response({'detail': 'Credenciales incorrectas. Intenta de nuevo.'},
                        status=status.HTTP_401_UNAUTHORIZED)
    return Response(_token_y_usuario(user))


login.cls.throttle_scope = 'login'


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def google_login(request):
    """Inicia sesión (o crea la cuenta) con un token de Google Identity Services."""
    credential = request.data.get('credential')
    if not credential:
        return Response({'detail': 'Falta el token de Google.'}, status=status.HTTP_400_BAD_REQUEST)
    if not settings.GOOGLE_CLIENT_ID:
        return Response({'detail': 'El inicio con Google no está configurado en el servidor.'},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)
    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token
        # clock_skew_in_seconds tolera pequeños desfases del reloj del servidor ("Token used too early").
        info = id_token.verify_oauth2_token(credential, google_requests.Request(), settings.GOOGLE_CLIENT_ID,
                                            clock_skew_in_seconds=30)
    except Exception as e:
        # Mostramos el motivo real en consola (y en DEBUG también al cliente) para diagnosticar:
        # típicamente "wrong audience" (client_id distinto) o "Token used too early/late" (reloj desfasado).
        logger.warning('Google login: falló la verificación del token: %r', e)
        detalle = 'Token de Google inválido.'
        if settings.DEBUG:
            detalle += f' ({e})'
        return Response({'detail': detalle}, status=status.HTTP_401_UNAUTHORIZED)

    email = (info.get('email') or '').strip().lower()
    if not email:
        return Response({'detail': 'No se pudo obtener el correo de Google.'}, status=status.HTTP_400_BAD_REQUEST)
    # Solo confiamos en correos que Google ya verificó (evita entrar a cuentas ajenas).
    if not info.get('email_verified'):
        return Response({'detail': 'Tu correo de Google no está verificado.'}, status=status.HTTP_401_UNAUTHORIZED)

    # Buscamos por correo sin distinguir mayúsculas, así se reutiliza la cuenta creada con el
    # formulario normal o desde el panel admin en vez de duplicarla.
    user = (User.objects.filter(email__iexact=email).order_by('id').first()
            or User.objects.filter(username__iexact=email).order_by('id').first())
    if user is None:
        # Sin contraseña: create_user la deja inutilizable (solo entra con Google o tras recuperarla).
        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=info.get('given_name', ''),
            last_name=info.get('family_name', ''),
        )
    if not user.is_active:
        return Response({'detail': 'Tu cuenta está desactivada. Contacta al administrador.'},
                        status=status.HTTP_403_FORBIDDEN)
    perfil, _ = Perfil.objects.get_or_create(usuario=user)
    if not perfil.email_verificado:
        # La cuenta se creó con el formulario sin comprobar el correo: alguien pudo
        # registrarla antes que el verdadero dueño. Como Google acaba de demostrar quién
        # es el dueño, se anulan la contraseña y las sesiones que hubiera creado otra persona.
        if user.has_usable_password():
            user.set_unusable_password()
            user.save(update_fields=['password'])
        Token.objects.filter(user=user).delete()
        perfil.email_verificado = True
        perfil.save(update_fields=['email_verificado'])
    return Response(_token_y_usuario(user))


google_login.cls.throttle_scope = 'login'


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    Token.objects.filter(user=request.user).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UsuarioSerializer(request.user).data)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def password_reset(request):
    """Envía un enlace de recuperación al correo (apunta al frontend)."""
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.encoding import force_bytes
    from django.utils.http import urlsafe_base64_encode

    from tablas.correos import enviar_correo_recuperacion

    email = (request.data.get('email') or '').strip()
    if not email:
        return Response({'detail': 'Escribe tu correo.'}, status=status.HTTP_400_BAD_REQUEST)
    for user in User.objects.filter(email__iexact=email, is_active=True):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        link = f'{settings.FRONTEND_URL}/restablecer-contrasena?uid={uid}&token={token}'
        # El enlace solo se muestra en consola en desarrollo (por si el correo falla):
        # en producción daría acceso a la cuenta a quien lea los registros.
        if settings.DEBUG:
            logger.info('Recuperar contraseña (solo DEBUG): %s -> %s', user.email, link)
        try:
            enviar_correo_recuperacion(user, link)
        except Exception:
            logger.exception('Recuperar contraseña: no se pudo enviar el correo a %s', user.email)
    # Respondemos siempre OK para no revelar si el correo existe.
    return Response({'detail': 'Si el correo existe, se enviaron las instrucciones a tu bandeja.'})


password_reset.cls.throttle_scope = 'recuperar'


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def password_reset_confirm(request):
    """Confirma el cambio de contraseña con uid + token."""
    from django.contrib.auth.password_validation import validate_password
    from django.contrib.auth.tokens import default_token_generator
    from django.core.exceptions import ValidationError
    from django.utils.http import urlsafe_base64_decode

    uid = request.data.get('uid')
    token = request.data.get('token')
    password = request.data.get('password')
    if not all([uid, token, password]):
        return Response({'detail': 'Faltan datos (uid, token o contraseña).'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = User.objects.get(pk=urlsafe_base64_decode(uid).decode())
    except Exception:
        return Response({'detail': 'El enlace no es válido.'}, status=status.HTTP_400_BAD_REQUEST)
    if not default_token_generator.check_token(user, token):
        return Response({'detail': 'El enlace expiró o ya fue usado. Solicita uno nuevo.'},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        validate_password(password, user)
    except ValidationError as e:
        return Response({'detail': ' '.join(e.messages)}, status=status.HTTP_400_BAD_REQUEST)
    user.set_password(password)
    user.save()
    # Cierra las sesiones abiertas con la contraseña anterior.
    Token.objects.filter(user=user).delete()
    # Quien abrió el enlace del correo demostró ser el dueño de la cuenta.
    Perfil.objects.update_or_create(usuario=user, defaults={'email_verificado': True})
    return Response({'detail': 'Contraseña actualizada. Ya puedes iniciar sesión.'})


password_reset_confirm.cls.throttle_scope = 'recuperar'
