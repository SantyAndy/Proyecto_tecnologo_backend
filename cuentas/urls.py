from django.urls import path

from . import views

urlpatterns = [
    path('register/', views.registro, name='registro'),
    path('login/', views.login, name='login'),
    path('google/', views.google_login, name='google_login'),
    path('logout/', views.logout, name='logout'),
    path('me/', views.me, name='me'),
    path('password-reset/', views.password_reset, name='password_reset'),
    path('password-reset-confirm/', views.password_reset_confirm, name='password_reset_confirm'),
]
