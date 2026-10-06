from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import admin_api, views

router = DefaultRouter()
router.register(r'fincas', views.FincaViewSet, basename='finca')
router.register(r'tipo-abonos', views.TipoAbonoViewSet, basename='tipoabono')
router.register(r'resenas', views.ResenaViewSet, basename='resena')
router.register(r'dispositivos', views.DispositivoViewSet, basename='dispositivo')

# Router del panel de administración (solo staff)
admin_router = DefaultRouter()
admin_router.register(r'fincas', admin_api.AdminFincaViewSet, basename='admin-finca')
admin_router.register(r'arduinos', admin_api.AdminArduinoViewSet, basename='admin-arduino')
admin_router.register(r'datos', admin_api.AdminDatoSueloViewSet, basename='admin-dato')
admin_router.register(r'tipo-abonos', admin_api.AdminTipoAbonoViewSet, basename='admin-tipoabono')
admin_router.register(r'productos', admin_api.AdminProductoViewSet, basename='admin-producto')
admin_router.register(r'abono-imagenes', admin_api.AdminTipoAbonoImagenViewSet, basename='admin-abonoimg')
admin_router.register(r'usuarios', admin_api.AdminUsuarioViewSet, basename='admin-usuario')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/', include(admin_router.urls)),
    path('ingesta/', views.ingesta, name='ingesta'),
    path('contacto/', views.contacto, name='contacto'),
]
