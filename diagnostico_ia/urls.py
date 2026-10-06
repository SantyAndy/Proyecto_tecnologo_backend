from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DiagnosticoViewSet

router = DefaultRouter()
router.register(r'', DiagnosticoViewSet, basename='diagnostico')

urlpatterns = [path('', include(router.urls))]
