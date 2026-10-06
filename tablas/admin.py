from django.contrib import admin

from .models import Arduino, DatoSuelo, Finca, Producto, Resena, TipoAbono, TipoAbonoImagen


@admin.register(Resena)
class ResenaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ciudad', 'estrellas', 'fecha', 'usuario')
    list_filter = ('estrellas',)
    search_fields = ('nombre', 'ciudad', 'comentario')


class TipoAbonoImagenInline(admin.TabularInline):
    model = TipoAbonoImagen
    extra = 1


@admin.register(Finca)
class FincaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ubicacion', 'hectareas', 'usuario')
    list_editable = ('hectareas',)
    search_fields = ('nombre', 'ubicacion')
    list_filter = ('usuario',)


@admin.register(Arduino)
class ArduinoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'finca')
    list_filter = ('finca',)
    # La clave se muestra para copiarla en el código del Arduino (cabecera X-Arduino-Key).
    readonly_fields = ('clave',)


@admin.register(DatoSuelo)
class DatoSueloAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'ph', 'humedad', 'temperatura', 'arduino')
    list_filter = ('arduino',)
    date_hierarchy = 'fecha'


@admin.register(TipoAbono)
class TipoAbonoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)
    inlines = [TipoAbonoImagenInline]


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo_abono', 'finca')
    search_fields = ('nombre',)


admin.site.register(TipoAbonoImagen)

