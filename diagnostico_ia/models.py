import os
import uuid

from django.conf import settings
from django.db import models


def ruta_imagen_diagnostico(instance, filename):
    """Nombre aleatorio para la foto: así nadie puede adivinar la URL de la hoja de otro usuario."""
    extension = os.path.splitext(filename)[1].lower()[:10]
    return f'diagnosticos/{uuid.uuid4().hex}{extension}'


class Diagnostico(models.Model):
    """Un diagnóstico fitosanitario realizado con el modelo de IA (YOLOv8)."""
    ESTADOS = [('alert', 'Alerta'), ('healthy', 'Sano'), ('deficiency', 'Deficiencia')]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='diagnosticos')
    imagen = models.ImageField(upload_to=ruta_imagen_diagnostico, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='alert')
    diagnostico = models.CharField(max_length=255, blank=True, default='')
    nombre_cientifico = models.CharField(max_length=150, blank=True, default='')
    recomendacion = models.TextField(blank=True, default='')
    fuente = models.CharField(max_length=200, blank=True, default='')
    # Confianza visual del diagnóstico principal (0-100). Null = no registrada.
    confianza = models.FloatField(null=True, blank=True)
    # Recomendación completa en el momento del análisis (productos, imagen de
    # cada producto, razones, advertencias, nivel de confianza y contexto).
    # Se guarda tal cual para que el historial no cambie si luego cambia el catálogo.
    recomendacion_detalle = models.JSONField(default=dict, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'diagnosticos'
        ordering = ['-creado']
        verbose_name = 'Diagnóstico'
        verbose_name_plural = 'Diagnósticos'

    def __str__(self):
        return f'{self.diagnostico or "Diagnóstico"} ({self.estado})'


class Deteccion(models.Model):
    """Cada recuadro (bounding box) detectado por YOLOv8 dentro de un diagnóstico."""
    diagnostico = models.ForeignKey(Diagnostico, on_delete=models.CASCADE, related_name='detecciones')
    etiqueta = models.CharField(max_length=100)          # ej. "Roya"
    confianza = models.FloatField(default=0)             # 0-100
    x = models.FloatField(default=0)                     # posición en % (0-100)
    y = models.FloatField(default=0)
    ancho = models.FloatField(default=0)
    alto = models.FloatField(default=0)

    class Meta:
        db_table = 'diagnostico_detecciones'

    def __str__(self):
        return f'{self.etiqueta} {self.confianza}%'
