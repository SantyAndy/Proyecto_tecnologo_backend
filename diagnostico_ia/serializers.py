from django.conf import settings
from rest_framework import serializers

from .models import Deteccion, Diagnostico


class DeteccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deteccion
        fields = ['etiqueta', 'confianza', 'x', 'y', 'ancho', 'alto']


class DiagnosticoSerializer(serializers.ModelSerializer):
    detecciones = DeteccionSerializer(many=True, required=False)

    class Meta:
        model = Diagnostico
        fields = [
            'id', 'imagen', 'estado', 'diagnostico', 'nombre_cientifico',
            'recomendacion', 'fuente', 'creado', 'detecciones',
            'confianza', 'recomendacion_detalle',
        ]
        read_only_fields = ['id', 'creado']

    def to_representation(self, instance):
        """
        Las imágenes de los productos se guardaron como URL absoluta del
        servidor de ese momento; se reescriben con el host actual para que
        el historial siga mostrándolas si cambia el dominio o el puerto.
        """

        datos = super().to_representation(instance)
        request = self.context.get('request')

        if request is not None and datos.get('recomendacion_detalle'):
            datos['recomendacion_detalle'] = self._reubicar_media(
                datos['recomendacion_detalle'], request
            )

        return datos

    def _reubicar_media(self, valor, request):
        if isinstance(valor, dict):
            return {k: self._reubicar_media(v, request) for k, v in valor.items()}
        if isinstance(valor, list):
            return [self._reubicar_media(v, request) for v in valor]
        if isinstance(valor, str) and settings.MEDIA_URL in valor:
            ruta = valor[valor.index(settings.MEDIA_URL):]
            return request.build_absolute_uri(ruta)
        return valor

    def create(self, validated_data):
        detecciones = validated_data.pop('detecciones', [])
        diagnostico = Diagnostico.objects.create(
            usuario=self.context['request'].user, **validated_data)
        for d in detecciones:
            Deteccion.objects.create(diagnostico=diagnostico, **d)
        return diagnostico
