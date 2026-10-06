"""API de administración (CRUD) — equivalente al admin de Django, consumible por Angular.

Solo accesible para usuarios con is_staff=True.
"""
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAdminUser

from .models import Arduino, DatoSuelo, Finca, Producto, TipoAbono, TipoAbonoImagen


# ----------------------- Serializers -----------------------
class AdminFincaSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = Finca
        fields = ['id', 'nombre', 'ubicacion', 'hectareas', 'usuario', 'usuario_nombre']


class AdminArduinoSerializer(serializers.ModelSerializer):
    finca_nombre = serializers.CharField(source='finca.nombre', read_only=True)

    class Meta:
        model = Arduino
        # La clave la genera el servidor; el admin la copia en el código del Arduino.
        fields = ['id', 'nombre', 'finca', 'finca_nombre', 'clave']
        read_only_fields = ['clave']


class AdminDatoSueloSerializer(serializers.ModelSerializer):
    arduino_nombre = serializers.CharField(source='arduino.nombre', read_only=True, default=None)

    class Meta:
        model = DatoSuelo
        fields = ['id', 'fecha', 'ph', 'humedad', 'temperatura', 'humedad_aire', 'arduino', 'arduino_nombre']


class AdminTipoAbonoSerializer(serializers.ModelSerializer):
    # Permite subir una imagen al crear/editar el abono (opcional).
    imagen = serializers.ImageField(write_only=True, required=False)
    imagen_actual = serializers.SerializerMethodField()

    class Meta:
        model = TipoAbono
        fields = ['id', 'nombre', 'imagen', 'imagen_actual']

    def get_imagen_actual(self, obj):
        img = obj.imagenes.filter(es_principal=True).first() or obj.imagenes.first()
        request = self.context.get('request')
        if img and img.imagen:
            return request.build_absolute_uri(img.imagen.url) if request else img.imagen.url
        return None

    def create(self, validated_data):
        imagen = validated_data.pop('imagen', None)
        tipo = TipoAbono.objects.create(**validated_data)
        if imagen:
            TipoAbonoImagen.objects.create(tipo_abono=tipo, imagen=imagen, titulo=tipo.nombre, es_principal=True)
        return tipo

    def update(self, instance, validated_data):
        imagen = validated_data.pop('imagen', None)
        instance.nombre = validated_data.get('nombre', instance.nombre)
        instance.save()
        if imagen:
            # Nueva imagen principal (las anteriores dejan de serlo).
            instance.imagenes.update(es_principal=False)
            TipoAbonoImagen.objects.create(tipo_abono=instance, imagen=imagen, titulo=instance.nombre, es_principal=True)
        return instance


class AdminTipoAbonoImagenSerializer(serializers.ModelSerializer):
    tipo_abono_nombre = serializers.CharField(source='tipo_abono.nombre', read_only=True)
    url = serializers.SerializerMethodField()

    class Meta:
        model = TipoAbonoImagen
        fields = ['id', 'tipo_abono', 'tipo_abono_nombre', 'titulo', 'orden', 'es_principal', 'imagen', 'url']
        extra_kwargs = {'imagen': {'required': False}}

    def get_url(self, obj):
        request = self.context.get('request')
        if obj.imagen:
            return request.build_absolute_uri(obj.imagen.url) if request else obj.imagen.url
        return None


class AdminProductoSerializer(serializers.ModelSerializer):
    tipo_abono_nombre = serializers.CharField(source='tipo_abono.nombre', read_only=True, default=None)

    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'descripcion', 'tipo_abono', 'tipo_abono_nombre', 'finca']


class AdminUsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'password']

    def validate(self, attrs):
        password = attrs.get('password')
        if self.instance is None and not password:
            raise serializers.ValidationError({'password': 'Escribe una contraseña para el nuevo usuario.'})
        if password:
            referencia = self.instance or User(**{k: v for k, v in attrs.items() if k != 'password'})
            try:
                validate_password(password, referencia)
            except DjangoValidationError as e:
                raise serializers.ValidationError({'password': list(e.messages)})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if password:
            instance.set_password(password)
        instance.save()
        # Si cambió la contraseña o se desactivó la cuenta, se cierran sus sesiones.
        if password or not instance.is_active:
            Token.objects.filter(user=instance).delete()
        return instance


# ----------------------- ViewSets -----------------------
class _AdminBase(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]


class AdminFincaViewSet(_AdminBase):
    queryset = Finca.objects.select_related('usuario').all()
    serializer_class = AdminFincaSerializer


class AdminArduinoViewSet(_AdminBase):
    queryset = Arduino.objects.select_related('finca').all()
    serializer_class = AdminArduinoSerializer


class AdminDatoSueloViewSet(_AdminBase):
    queryset = DatoSuelo.objects.select_related('arduino').all()
    serializer_class = AdminDatoSueloSerializer


class AdminTipoAbonoViewSet(_AdminBase):
    queryset = TipoAbono.objects.all()
    serializer_class = AdminTipoAbonoSerializer


class AdminProductoViewSet(_AdminBase):
    queryset = Producto.objects.select_related('tipo_abono', 'finca').all()
    serializer_class = AdminProductoSerializer


class AdminTipoAbonoImagenViewSet(_AdminBase):
    queryset = TipoAbonoImagen.objects.select_related('tipo_abono').all()
    serializer_class = AdminTipoAbonoImagenSerializer


class AdminUsuarioViewSet(_AdminBase):
    queryset = User.objects.all().order_by('id')
    serializer_class = AdminUsuarioSerializer

    def _proteger_superusuario(self, usuario):
        # Un staff normal no puede tocar a un superusuario (por ejemplo, cambiarle la
        # contraseña para entrar con su cuenta y obtener más permisos).
        if usuario.is_superuser and not self.request.user.is_superuser:
            raise PermissionDenied('Solo un superusuario puede modificar a otro superusuario.')

    def perform_update(self, serializer):
        self._proteger_superusuario(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._proteger_superusuario(instance)
        if instance == self.request.user:
            raise PermissionDenied('No puedes eliminar tu propia cuenta desde el panel.')
        instance.delete()
