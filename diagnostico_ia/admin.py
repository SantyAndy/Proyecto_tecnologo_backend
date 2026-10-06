from django.contrib import admin

from .models import Diagnostico


@admin.register(Diagnostico)
class DiagnosticoAdmin(admin.ModelAdmin):
    list_display = ('diagnostico', 'estado', 'usuario', 'creado')
    list_filter = ('estado',)
