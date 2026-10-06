import secrets
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Finca(models.Model):
    nombre = models.CharField(max_length=150)
    ubicacion = models.CharField(max_length=150, blank=True, default='')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='fincas')
    # Área de la finca en hectáreas.
    hectareas = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0'),
                                    validators=[MinValueValidator(Decimal('0'))])

    class Meta:
        db_table = 'fincas'
        verbose_name_plural = 'Fincas'

    def __str__(self):
        return f'{self.nombre} — {self.ubicacion}'


def generar_clave_arduino():
    return secrets.token_urlsafe(32)


class Arduino(models.Model):
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, related_name='arduinos')
    nombre = models.CharField(max_length=100, blank=True, default='')
    # Clave secreta que el Arduino envía en la cabecera X-Arduino-Key al reportar
    # lecturas; sin ella cualquiera podría inventar datos de una finca ajena.
    clave = models.CharField(max_length=64, unique=True, default=generar_clave_arduino, editable=False)

    class Meta:
        db_table = 'arduinos'

    def __str__(self):
        return self.nombre or f'Arduino {self.pk}'


class DatoSuelo(models.Model):
    arduino = models.ForeignKey(Arduino, on_delete=models.CASCADE, related_name='datos', null=True, blank=True)
    ph = models.FloatField(null=True, blank=True)
    humedad = models.FloatField(null=True, blank=True)        # humedad del suelo (%)
    temperatura = models.FloatField(null=True, blank=True)
    humedad_aire = models.FloatField(null=True, blank=True)   # humedad del aire (%) del DHT11
    fecha = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'datos_suelos'
        ordering = ['-fecha']
        verbose_name = 'Dato de suelo'
        verbose_name_plural = 'Datos de suelo'

    def __str__(self):
        return f'pH {self.ph} · {self.fecha}'


class TipoAbono(models.Model):
    nombre = models.CharField(max_length=150)

    class Meta:
        db_table = 'tipo_abono'
        verbose_name = 'Tipo de abono'
        verbose_name_plural = 'Tipos de abono'

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, default='')
    tipo_abono = models.ForeignKey(TipoAbono, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos')
    finca = models.ForeignKey(Finca, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos')

    class Meta:
        db_table = 'productos'

    def __str__(self):
        return self.nombre


class TipoAbonoImagen(models.Model):
    tipo_abono = models.ForeignKey(TipoAbono, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='abonos/')
    titulo = models.CharField(max_length=150, blank=True, default='')
    orden = models.PositiveIntegerField(default=0)
    es_principal = models.BooleanField(default=False)

    class Meta:
        db_table = 'tipo_abono_imagenes'
        ordering = ['orden', 'id']

    def __str__(self):
        return f'{self.tipo_abono_id} — {self.titulo or self.imagen.name}'


class Resena(models.Model):
    """Opinión/reseña de un usuario sobre la página (una por usuario)."""
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resena')
    nombre = models.CharField(max_length=150)
    ciudad = models.CharField(max_length=150, blank=True, default='')
    comentario = models.TextField()
    estrellas = models.PositiveSmallIntegerField(default=5)  # 1 a 5
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'resenas'
        ordering = ['-fecha']
        verbose_name = 'Reseña'
        verbose_name_plural = 'Reseñas'

    def __str__(self):
        return f'{self.nombre} ({self.estrellas}★)'

