from rest_framework import serializers

from datetime import timedelta

from django.utils import timezone

from .models import Arduino, DatoSuelo, Finca, Resena, TipoAbono, TipoAbonoImagen


class FincaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Finca
        fields = ['id', 'nombre', 'ubicacion', 'hectareas']


class DatoSueloSerializer(serializers.ModelSerializer):
    dispositivo = serializers.CharField(source='arduino.nombre', default=None, read_only=True)

    class Meta:
        model = DatoSuelo
        fields = ['id', 'fecha', 'humedad', 'temperatura', 'humedad_aire', 'ph', 'dispositivo']


class TipoAbonoImagenSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = TipoAbonoImagen
        fields = ('id', 'titulo', 'orden', 'es_principal', 'url')

    def get_url(self, obj):
        request = self.context.get('request')
        if obj.imagen:
            return request.build_absolute_uri(obj.imagen.url) if request else obj.imagen.url
        return None


class TipoAbonoSerializer(serializers.ModelSerializer):
    imagen_principal = serializers.SerializerMethodField()
    imagenes = TipoAbonoImagenSerializer(many=True, read_only=True)

    class Meta:
        model = TipoAbono
        fields = ('id', 'nombre', 'imagen_principal', 'imagenes')

    def get_imagen_principal(self, obj):
        request = self.context.get('request')
        img = obj.imagenes.filter(es_principal=True).first() or obj.imagenes.first()
        if img and img.imagen:
            return request.build_absolute_uri(img.imagen.url) if request else img.imagen.url
        return None


class IngestaSerializer(serializers.Serializer):
    """Datos que envía el Arduino UNO R4 WiFi."""
    arduino_id = serializers.IntegerField(min_value=1)
    # Un valor que no llega es "no disponible" (None), no una lectura de 0.
    # Los rangos descartan lecturas imposibles (sensor dañado o datos inventados).
    ph = serializers.FloatField(required=False, allow_null=True, default=None, min_value=0, max_value=14)
    humedad_suelo = serializers.FloatField(required=False, allow_null=True, default=None, min_value=0, max_value=100)
    temperatura = serializers.FloatField(required=False, allow_null=True, default=None, min_value=-40, max_value=85)
    humedad_aire = serializers.FloatField(required=False, allow_null=True, default=None, min_value=0, max_value=100)


# Si el Arduino no reporta en este tiempo se considera desconectado
# (envía una lectura cada 10 segundos).
MARGEN_EN_LINEA = timedelta(minutes=1)


class DispositivoSerializer(serializers.ModelSerializer):
    """Arduino de una finca del usuario, con su estado de conexión."""
    finca_nombre = serializers.CharField(source='finca.nombre', read_only=True)
    ultima_lectura = serializers.SerializerMethodField()
    en_linea = serializers.SerializerMethodField()
    total_lecturas = serializers.SerializerMethodField()

    class Meta:
        model = Arduino
        fields = ['id', 'nombre', 'finca', 'finca_nombre', 'clave',
                  'ultima_lectura', 'en_linea', 'total_lecturas']
        read_only_fields = ['clave']

    def validate_finca(self, finca):
        # Solo se pueden registrar dispositivos en fincas propias.
        if finca.usuario_id != self.context['request'].user.id:
            raise serializers.ValidationError('Esa finca no te pertenece.')
        return finca

    def _ultima(self, obj):
        if not hasattr(obj, '_ultima_cache'):
            obj._ultima_cache = obj.datos.exclude(fecha=None).order_by('-fecha').first()
        return obj._ultima_cache

    def get_ultima_lectura(self, obj):
        dato = self._ultima(obj)
        return DatoSueloSerializer(dato).data if dato else None

    def get_en_linea(self, obj):
        dato = self._ultima(obj)
        return bool(dato and timezone.now() - dato.fecha <= MARGEN_EN_LINEA)

    def get_total_lecturas(self, obj):
        return obj.datos.count()


class ContactoSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=150)
    apellido = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    mensaje = serializers.CharField(max_length=5000)
    autoriza = serializers.BooleanField(default=False)


class ResenaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resena
        fields = ['id', 'nombre', 'ciudad', 'comentario', 'estrellas', 'fecha']
        read_only_fields = ['id', 'fecha']
        extra_kwargs = {'comentario': {'max_length': 2000}}

    def validate_estrellas(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError('Las estrellas deben estar entre 1 y 5.')
        return value
