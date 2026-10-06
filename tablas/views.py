import hmac
import socket
from datetime import datetime

from django.db.models import Avg
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from .correos import enviar_correo_contacto
from .models import (
    generar_clave_arduino,
    Arduino,
    DatoSuelo,
    Finca,
    Producto,
    Resena,
    TipoAbono,
)
from .motor_recomendacion import absolutizar_imagenes
from .recomendador import (
    construir_sugerencia_integrada,
    recomendacion_general,
    recomendar_abono,
)
from .serializers import (
    ContactoSerializer,
    DatoSueloSerializer,
    DispositivoSerializer,
    FincaSerializer,
    IngestaSerializer,
    ResenaSerializer,
    TipoAbonoSerializer,
)


def _promedio(valores):
    """
    Calcula el promedio de una lista ignorando valores None.
    """
    valores = [v for v in valores if v is not None]

    return (
        round(sum(valores) / len(valores), 2)
        if valores
        else None
    )


def _abonos_desde_sugerencia(sugerencia, generales):
    """
    Lista de abonos que muestra la página de resultados.

    Solo se muestran productos que el motor recomendó con evidencia
    (con su imagen). Si no hay evidencia suficiente se devuelven las
    notas generales (no son productos) y el motivo.
    """

    productos = (sugerencia or {}).get('productos_recomendados') or []

    if productos:
        return productos, False

    recomendacion = (sugerencia or {}).get('recomendacion') or {}

    # Fallback: recomendación visual preliminar (deficiencia detectada
    # por la IA sin datos agronómicos suficientes).
    visual = recomendacion.get('recomendacion_visual') or {}
    visuales = (visual.get('productos') or []) + (visual.get('foliares') or [])

    if visuales:
        return [
            {
                **item,
                'descripcion': f"{visual['titulo']} {item['motivo']} {item['advertencia']}",
                'imagenes': [{'url': item['imagen'], 'es_principal': True}] if item['imagen'] else [],
                'es_general': False,
                'situacion': 'normal',
            }
            for item in visuales
        ], True

    notas = [{
        'nombre': recomendacion.get('mensaje') or 'Sin fertilizante recomendado',
        'descripcion': ' '.join(
            (recomendacion.get('motivos_no_recomendacion') or [])
            + [recomendacion.get('recomendacion_validacion') or '']
        ).strip(),
        'imagenes': [],
        'es_general': True,
        'situacion': 'general',
    }]

    return notas + [a for a in generales if a.get('situacion') == 'extraordinaria'], True


def _leer_analisis(valor):
    return valor if isinstance(valor, dict) else None


def _leer_fecha(valor):
    """Convierte 'YYYY-MM-DD' en fecha; devuelve None si viene vacía o mal escrita."""
    try:
        return datetime.strptime(str(valor), '%Y-%m-%d').date() if valor else None
    except ValueError:
        return None


class FincaViewSet(viewsets.ModelViewSet):
    """
    CRUD de fincas del usuario autenticado
    + datos / historial / sugerencias.
    """

    serializer_class = FincaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Finca.objects.filter(
            usuario=self.request.user
        ).order_by('nombre')

    def perform_create(self, serializer):
        serializer.save(
            usuario=self.request.user
        )

    # ========================================================
    # DATOS DE SENSORES
    # ========================================================

    @action(detail=True, methods=['get'])
    def datos(self, request, pk=None):
        """
        Últimas lecturas de los sensores de la finca.
        """

        finca = self.get_object()

        qs = DatoSuelo.objects.filter(
            arduino__finca=finca
        )

        arduino_id = request.query_params.get(
            'arduino_id'
        )

        if arduino_id and str(arduino_id).isdigit():
            qs = qs.filter(
                arduino_id=arduino_id
            )

        qs = qs.order_by('-fecha')[:30]

        return Response(
            DatoSueloSerializer(
                qs,
                many=True
            ).data
        )

    # ========================================================
    # HISTORIAL
    # ========================================================

    @action(detail=True, methods=['get'])
    def historial(self, request, pk=None):
        """
        Historial filtrable por rango de fechas.

        ?desde=YYYY-MM-DD
        ?hasta=YYYY-MM-DD
        """

        finca = self.get_object()

        qs = DatoSuelo.objects.filter(
            arduino__finca=finca
        )

        desde = _leer_fecha(request.query_params.get(
            'desde'
        ))

        hasta = _leer_fecha(request.query_params.get(
            'hasta'
        ))

        if desde:
            qs = qs.filter(
                fecha__date__gte=desde
            )

        if hasta:
            qs = qs.filter(
                fecha__date__lte=hasta
            )

        qs = qs.order_by('-fecha')

        return Response(
            DatoSueloSerializer(
                qs,
                many=True
            ).data
        )

    # ========================================================
    # SUGERENCIAS
    # ========================================================

    @action(detail=True, methods=['post'])
    def sugerencias(self, request, pk=None):
        """
        Genera la recomendación de abono.

        Flujo:

        1. Diagnóstico de IA
        2. Variedad
        3. Temporada
        4. ¿Usar sensores?

        Si usa sensores:
            - desde
            - hasta
            - promedio pH
            - promedio humedad
            - promedio temperatura

        Si NO usa sensores:
            - no consulta DatoSuelo
            - utiliza condición climática
            - no inventa valores de sensores
        """

        finca = self.get_object()

        # ====================================================
        # DATOS GENERALES
        # ====================================================

        temporada = request.data.get(
            'temporada'
        )

        variedad = request.data.get(
            'variedad'
        )

        usar_sensores = request.data.get(
            'usar_sensores'
        )

        condicion_climatica = request.data.get(
            'condicion_climatica'
        )

        diagnostico = request.data.get(
            'diagnostico'
        )

        # ====================================================
        # CONVERTIR usar_sensores A BOOLEAN
        # ====================================================

        if isinstance(
            usar_sensores,
            str
        ):

            usar_sensores = (
                usar_sensores.lower()
                in [
                    'true',
                    '1',
                    'si',
                    'sí',
                    'yes',
                ]
            )

        elif usar_sensores is None:

            # Compatibilidad con el flujo anterior.
            # Si no viene el parámetro, asumimos sensores.
            usar_sensores = True

        else:

            usar_sensores = bool(
                usar_sensores
            )

        # ====================================================
        # VALIDAR TEMPORADA
        # ====================================================

        if not temporada:

            return Response(
                {
                    'detail':
                        'Falta el parámetro temporada.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ====================================================
        # VALIDAR VARIEDAD
        # ====================================================

        if not variedad:

            return Response(
                {
                    'detail':
                        'Falta seleccionar la variedad de café.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ====================================================
        # MODO SIN SENSORES
        # ====================================================

        if not usar_sensores:

            if not condicion_climatica:

                return Response(
                    {
                        'detail':
                            'Debes seleccionar la condición climática '
                            'cuando no utilizas los sensores.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ------------------------------------------------
            # SIN SENSORES:
            #
            # No buscamos DatoSuelo.
            # No inventamos pH.
            # No inventamos humedad.
            # No inventamos temperatura.
            # ------------------------------------------------

            ph_prom = None
            hum_prom = None
            temp_prom = None

            datos = DatoSuelo.objects.none()

            # ------------------------------------------------
            # El recomendador no utiliza las reglas basadas
            # en pH/humedad/temperatura en este modo.
            # Por eso se genera la fórmula general de acuerdo
            # con temporada + variedad + condición climática.
            # ------------------------------------------------

            recomendaciones = []

            abonos = []

            # ------------------------------------------------
            # Recomendación general
            # ------------------------------------------------

            for gen in recomendacion_general(
                ph_prom,
                hum_prom,
                temp_prom,
                temporada,
                variedad=variedad,
                usar_sensores=False,
                condicion_climatica=condicion_climatica,
            ):

                abonos.append(
                    {
                        'nombre':
                            gen['nombre'],

                        'descripcion':
                            gen['descripcion'],

                        'imagenes':
                            [],

                        'es_general':
                            True,

                        'situacion':
                            gen['situacion'],
                    }
                )

            # ------------------------------------------------
            # Sugerencia integrada con IA
            # ------------------------------------------------

            sugerencia_integrada = (
                construir_sugerencia_integrada(
                    ph_prom,
                    hum_prom,
                    temp_prom,
                    temporada,
                    abonos,
                    diagnostico,
                    variedad=variedad,
                    usar_sensores=False,
                    condicion_climatica=condicion_climatica,
                    analisis_suelo=_leer_analisis(request.data.get('analisis_suelo')),
                    analisis_foliar=_leer_analisis(request.data.get('analisis_foliar')),
                )
            )

            abonos, es_general = _abonos_desde_sugerencia(
                sugerencia_integrada,
                abonos,
            )

            return Response(absolutizar_imagenes(
                {
                    'desde': None,

                    'hasta': None,

                    'temporada':
                        temporada,

                    'variedad':
                        variedad,

                    'usar_sensores':
                        False,

                    'condicion_climatica':
                        condicion_climatica,

                    'lecturas':
                        [],

                    'cantidad_lecturas':
                        0,

                    'ph_promedio':
                        None,

                    'humedad_promedio':
                        None,

                    'temperatura_promedio':
                        None,

                    'abonos_recomendados':
                        abonos,

                    'recomendacion_general':
                        es_general,

                    'sugerencia_integrada':
                        sugerencia_integrada,
                },
                request
            ))

        # ====================================================
        # MODO CON SENSORES
        # ====================================================

        desde = request.data.get(
            'desde'
        )

        hasta = request.data.get(
            'hasta'
        )

        # ----------------------------------------------------
        # Validar fechas
        # ----------------------------------------------------

        if not desde or not hasta:

            return Response(
                {
                    'detail':
                        'Cuando utilizas los sensores debes '
                        'seleccionar las fechas desde y hasta.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            f_desde = datetime.strptime(
                desde,
                '%Y-%m-%d'
            ).date()

            f_hasta = datetime.strptime(
                hasta,
                '%Y-%m-%d'
            ).date()

        except ValueError:

            return Response(
                {
                    'detail':
                        'Formato de fecha inválido '
                        '(use YYYY-MM-DD).'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ----------------------------------------------------
        # Validar rango
        # ----------------------------------------------------

        if f_desde > f_hasta:

            return Response(
                {
                    'detail':
                        'La fecha de inicio no puede ser '
                        'mayor a la fecha final.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ====================================================
        # CONSULTAR SENSORES
        # ====================================================

        datos = DatoSuelo.objects.filter(
            arduino__finca=finca,
            fecha__date__gte=f_desde,
            fecha__date__lte=f_hasta,
        ).order_by(
            'fecha'
        )

        # ====================================================
        # VERIFICAR SI HAY DATOS
        # ====================================================

        cantidad_lecturas = datos.count()

        if cantidad_lecturas == 0:

            return Response(
                {
                    'detail':
                        'No existen datos de sensores '
                        'en el rango de fechas seleccionado.',

                    'desde':
                        desde,

                    'hasta':
                        hasta,

                    'temporada':
                        temporada,

                    'variedad':
                        variedad,

                    'usar_sensores':
                        True,

                    'condicion_climatica':
                        condicion_climatica,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ====================================================
        # PROMEDIOS
        # ====================================================

        ph_prom = _promedio(
            [
                d.ph
                for d in datos
            ]
        )

        hum_prom = _promedio(
            [
                d.humedad
                for d in datos
            ]
        )

        temp_prom = _promedio(
            [
                d.temperatura
                for d in datos
            ]
        )

        # ====================================================
        # RECOMENDACIÓN SEGÚN SENSORES
        # ====================================================

        recomendaciones = recomendar_abono(
            ph_prom,
            hum_prom,
            temp_prom,
            temporada,
            variedad=variedad,
            usar_sensores=True,
            condicion_climatica=condicion_climatica,
        )

        # ====================================================
        # PREPARAR ABONOS
        # ====================================================

        abonos = []

        for rec in recomendaciones:

            tipo = rec[
                'tipo_abono'
            ]

            descripcion = rec[
                'descripcion'
            ]

            imagenes = []

            # ------------------------------------------------
            # Imágenes del tipo de abono
            # ------------------------------------------------

            if tipo:

                imagenes = TipoAbonoSerializer(
                    tipo,
                    context={
                        'request':
                            request
                    }
                ).data[
                    'imagenes'
                ]

                # --------------------------------------------
                # Si el tipo no tiene descripción,
                # buscamos un producto asociado.
                # --------------------------------------------

                if not descripcion:

                    prod = (
                        Producto.objects

                        .filter(
                            tipo_abono=tipo
                        )

                        .exclude(
                            descripcion=''
                        )

                        .first()
                    )

                    if prod:

                        descripcion = (
                            prod.descripcion
                        )

            abonos.append(
                {
                    'nombre':
                        rec['nombre'],

                    'descripcion':
                        descripcion,

                    'imagenes':
                        imagenes,
                }
            )

        # ====================================================
        # RECOMENDACIÓN GENERAL
        # ====================================================

        es_general = False

        if not abonos:

            es_general = True

            for gen in recomendacion_general(
                ph_prom,
                hum_prom,
                temp_prom,
                temporada,
                variedad=variedad,
                usar_sensores=True,
                condicion_climatica=condicion_climatica,
            ):

                abonos.append(
                    {
                        'nombre':
                            gen['nombre'],

                        'descripcion':
                            gen['descripcion'],

                        'imagenes':
                            [],

                        'es_general':
                            True,

                        'situacion':
                            gen['situacion'],
                    }
                )

        # ====================================================
        # SUGERENCIA INTEGRADA
        # ====================================================

        sugerencia_integrada = (
            construir_sugerencia_integrada(
                ph_prom,
                hum_prom,
                temp_prom,
                temporada,
                abonos,
                diagnostico,
                variedad=variedad,
                usar_sensores=True,
                condicion_climatica=condicion_climatica,
                analisis_suelo=_leer_analisis(request.data.get('analisis_suelo')),
                analisis_foliar=_leer_analisis(request.data.get('analisis_foliar')),
                fuente_datos='sensores Arduino',
            )
        )

        # Los abonos que coinciden con las reglas por pH/humedad/
        # temperatura ya participan en el motor como factor
        # secundario; aquí solo se muestran los que el motor
        # recomendó con evidencia.
        abonos, es_general = _abonos_desde_sugerencia(
            sugerencia_integrada,
            abonos,
        )

        # ====================================================
        # RESPUESTA
        # ====================================================

        return Response(absolutizar_imagenes(
            {
                'desde':
                    desde,

                'hasta':
                    hasta,

                'temporada':
                    temporada,

                'variedad':
                    variedad,

                'usar_sensores':
                    True,

                'condicion_climatica':
                    condicion_climatica,

                # --------------------------------------------
                # Todas las lecturas del rango seleccionado.
                # --------------------------------------------

                'lecturas':
                    DatoSueloSerializer(
                        datos,
                        many=True
                    ).data,

                'cantidad_lecturas':
                    cantidad_lecturas,

                # --------------------------------------------
                # Promedios utilizados para recomendar.
                # --------------------------------------------

                'ph_promedio':
                    ph_prom,

                'humedad_promedio':
                    hum_prom,

                'temperatura_promedio':
                    temp_prom,

                'abonos_recomendados':
                    abonos,

                'recomendacion_general':
                    es_general,

                'sugerencia_integrada':
                    sugerencia_integrada,
            },
            request
        ))


# ============================================================
# TIPOS DE ABONO
# ============================================================

class TipoAbonoViewSet(
    viewsets.ReadOnlyModelViewSet
):

    queryset = (
        TipoAbono.objects
        .all()
        .prefetch_related('imagenes')
    )

    serializer_class = TipoAbonoSerializer
    permission_classes = [AllowAny]


# ============================================================
# DISPOSITIVOS (ARDUINOS) DEL USUARIO
# ============================================================

def _ips_del_servidor():
    """IPs de red local de este computador (las que debe usar el Arduino)."""
    ips = []
    try:
        # Conectar un socket UDP no envía paquetes: solo pregunta al sistema
        # qué interfaz usaría para salir a la red.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('8.8.8.8', 80))
            ips.append(s.getsockname()[0])
    except OSError:
        pass
    try:
        for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
            if ip not in ips:
                ips.append(ip)
    except OSError:
        pass
    return [ip for ip in ips if not ip.startswith('127.')]


class DispositivoViewSet(viewsets.ModelViewSet):
    """
    Arduinos de las fincas del usuario: registrar, renombrar, eliminar,
    ver su clave y su estado de conexión.

    ?finca=<id> filtra por finca.
    """

    serializer_class = DispositivoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = []

    def get_queryset(self):
        qs = Arduino.objects.filter(
            finca__usuario=self.request.user
        ).select_related('finca').order_by('id')

        finca = self.request.query_params.get('finca')

        if finca and str(finca).isdigit():
            qs = qs.filter(finca_id=finca)

        return qs

    @action(detail=True, methods=['post'], url_path='regenerar-clave')
    def regenerar_clave(self, request, pk=None):
        """Crea una clave nueva; la anterior deja de funcionar al instante."""
        arduino = self.get_object()
        arduino.clave = generar_clave_arduino()
        arduino.save(update_fields=['clave'])
        return Response(self.get_serializer(arduino).data)

    @action(detail=False, methods=['get'])
    def conexion(self, request):
        """Datos que necesita el código del Arduino para llegar a este servidor."""
        return Response({
            'ips': _ips_del_servidor(),
            'puerto': int(request.get_port() or 8000),
            'ruta': '/api/ingesta/',
        })


# ============================================================
# INGESTA ARDUINO
# ============================================================

@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def ingesta(request):
    """
    Endpoint para que el Arduino envíe lecturas de los sensores.

    El Arduino se identifica con su clave secreta en la cabecera
    `X-Arduino-Key` (se ve en el panel de administración).
    """

    serializer = IngestaSerializer(
        data=request.data
    )

    serializer.is_valid(
        raise_exception=True
    )

    data = serializer.validated_data

    arduino = Arduino.objects.filter(
        id=data['arduino_id']
    ).first()

    clave = request.headers.get('X-Arduino-Key', '')

    # Misma respuesta si el Arduino no existe o la clave no coincide, para no
    # revelar qué IDs existen. compare_digest evita ataques por tiempo de respuesta.
    if arduino is None or not hmac.compare_digest(clave.encode(), arduino.clave.encode()):
        return Response(
            {
                'detail':
                    'Arduino o clave inválidos.'
            },
            status=status.HTTP_403_FORBIDDEN
        )

    DatoSuelo.objects.create(
        arduino=arduino,
        ph=data['ph'],
        humedad=data['humedad_suelo'],
        temperatura=data['temperatura'],
        humedad_aire=data['humedad_aire'],
        fecha=timezone.now(),
    )

    return Response(
        {
            'status':
                'ok'
        },
        status=status.HTTP_201_CREATED
    )


ingesta.cls.throttle_scope = 'ingesta'


# ============================================================
# RESEÑAS
# ============================================================

class ResenaViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):

    """
    Opiniones de los caficultores.
    Listado público.
    Crear requiere sesión.
    """

    queryset = Resena.objects.all()

    serializer_class = ResenaSerializer

    def get_permissions(self):

        if (
            self.action == 'create'
            or self.action == 'mia'
        ):

            return [
                IsAuthenticated()
            ]

        return [
            AllowAny()
        ]

    def create(
        self,
        request,
        *args,
        **kwargs
    ):

        if Resena.objects.filter(
            usuario=request.user
        ).exists():

            return Response(
                {
                    'detail':
                        'Ya dejaste tu opinión. '
                        'Solo se permite una por usuario.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save(
            usuario=request.user
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[AllowAny]
    )
    def resumen(
        self,
        request
    ):

        qs = Resena.objects.all()

        total = qs.count()

        promedio = (
            qs.aggregate(
                p=Avg('estrellas')
            )['p']
            or 0
        )

        distribucion = {
            str(i):
                qs.filter(
                    estrellas=i
                ).count()

            for i in range(
                5,
                0,
                -1
            )
        }

        return Response(
            {
                'total':
                    total,

                'promedio':
                    round(
                        promedio,
                        1
                    ),

                'porcentaje':
                    round(
                        (promedio / 5) * 100
                    ),

                'distribucion':
                    distribucion,
            }
        )

    @action(
        detail=False,
        methods=['get']
    )
    def mia(
        self,
        request
    ):

        resena = (
            Resena.objects
            .filter(
                usuario=request.user
            )
            .first()
        )

        return Response(
            ResenaSerializer(
                resena
            ).data
            if resena
            else None
        )


# ============================================================
# CONTACTO
# ============================================================

@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def contacto(request):
    """
    Formulario de contacto público.
    """

    serializer = ContactoSerializer(
        data=request.data
    )

    serializer.is_valid(
        raise_exception=True
    )

    d = serializer.validated_data

    enviar_correo_contacto(
        d['nombre'],
        d['apellido'],
        d['email'],
        d['mensaje'],
        d['autoriza']
    )

    return Response(
        {
            'detail':
                'Mensaje enviado correctamente.'
        }
    )


contacto.cls.throttle_scope = 'contacto'
