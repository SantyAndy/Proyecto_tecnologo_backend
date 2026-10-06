from django.conf import settings
from django.db import models


class Perfil(models.Model):
    """Datos extra del usuario (la ubicación que pedía el formulario de registro)."""
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil')
    ubicacion = models.CharField(max_length=255, blank=True, default='')
    # True cuando el usuario demostró ser dueño del correo (entró con Google o
    # restableció la contraseña desde el enlace enviado a su bandeja).
    email_verificado = models.BooleanField(default=False)

    def __str__(self):
        return f'Perfil de {self.usuario.username}'
