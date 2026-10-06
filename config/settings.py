"""
Django settings for config project — API REST del sistema de monitoreo de café.

Backend desacoplado (solo API) que se comunica con el frontend Angular.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _cargar_env(ruta):
    """Carga variables desde un archivo .env (CLAVE=valor) sin pisar las del sistema."""
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding='utf-8').splitlines():
        linea = linea.strip()
        if not linea or linea.startswith('#') or '=' not in linea:
            continue
        clave, valor = linea.split('=', 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


_cargar_env(BASE_DIR / '.env')


def _env_lista(nombre, defecto=''):
    return [v.strip() for v in os.environ.get(nombre, defecto).split(',') if v.strip()]


def _env_requerida(nombre):
    valor = os.environ.get(nombre)
    if not valor:
        raise ImproperlyConfigured(
            f'Falta la variable de entorno {nombre}. Copia .env.example a .env y complétalo.'
        )
    return valor


# Las credenciales viven en el archivo .env (no se sube a git). Ver .env.example.
SECRET_KEY = _env_requerida('DJANGO_SECRET_KEY')

# Apagado por defecto: solo se enciende con DJANGO_DEBUG=True en el .env de desarrollo.
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('1', 'true', 'si', 'sí', 'yes')

# En desarrollo se acepta cualquier host (para probar desde el celular por WiFi).
ALLOWED_HOSTS = _env_lista('DJANGO_ALLOWED_HOSTS') or (['*'] if DEBUG else ['localhost', '127.0.0.1'])


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Terceros
    'rest_framework',
    'rest_framework.authtoken',
    'drf_spectacular',
    'corsheaders',
    'django_filters',

    # Apps del proyecto
    'cuentas',
    'tablas',
    'diagnostico_ia',  # Diagnóstico fitosanitario con IA (YOLOv8)
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATE_FORMAT': '%Y-%m-%d',
    # Límite de peticiones para frenar fuerza bruta y abuso de los formularios públicos.
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '120/min',
        'user': '600/min',
        'login': '10/min',
        'registro': '10/hour',
        'recuperar': '5/hour',
        'contacto': '5/hour',
        'ingesta': '120/min',
        'diagnostico': '30/min',
    },
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'API — Monitoreo del café',
    'DESCRIPTION': 'API REST para análisis y monitoreo de la planta del café (pH, humedad y temperatura).',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # Fuera de desarrollo la documentación de la API solo la ven los administradores.
    'SERVE_PERMISSIONS': (
        ['rest_framework.permissions.AllowAny'] if DEBUG
        else ['rest_framework.permissions.IsAdminUser']
    ),
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',          # CORS primero
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# --- CORS: permitir al frontend Angular ---
CORS_ALLOWED_ORIGINS = _env_lista(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:4200,http://127.0.0.1:4200,http://192.168.100.20:4200',
) + [
    # App nativa generada con Capacitor (Ionic)
    'https://localhost',       # Android
    'capacitor://localhost',   # iOS
]
# Solo en desarrollo: acepta cualquier IP de red local (WiFi) en el puerto 4200,
# útil para abrir la app desde el celular aunque la IP del computador cambie.
CORS_ALLOWED_ORIGIN_REGEXES = [
    r'^http://192\.168\.\d{1,3}\.\d{1,3}:4200$',
    r'^http://10\.\d{1,3}\.\d{1,3}\.\d{1,3}:4200$',
    r'^http://172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}:4200$',
] if DEBUG else []
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = _env_lista(
    'CSRF_TRUSTED_ORIGINS',
    'http://localhost:4200,http://127.0.0.1:4200,http://192.168.100.20:4200',
)

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'Proyecto'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': _env_requerida('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    },
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True


# Static & media
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- Email (recuperación de contraseña / contacto) ---
# SMTP de Gmail (usa una "contraseña de aplicación", no la normal).
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_TIMEOUT = 15
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
CONTACTO_EMAIL = EMAIL_HOST_USER
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:4200')
# El enlace de "recuperar contraseña" caduca en 1 hora (Django usa 3 días por defecto).
PASSWORD_RESET_TIMEOUT = 60 * 60

# --- Inicio de sesión con Google ---
# Pega aquí el "Client ID" de tu credencial OAuth de Google Cloud Console.
# (APIs y servicios → Credenciales → ID de cliente de OAuth 2.0 → Aplicación web)
GOOGLE_CLIENT_ID = os.environ.get(
    'GOOGLE_CLIENT_ID',
    '331789073953-o16oruanc99hpbeo9h0usih1r5cufk62.apps.googleusercontent.com',
)


# --- Subida de archivos ---
# Tamaño máximo de una foto para el diagnóstico IA (bytes).
MAX_IMAGEN_BYTES = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024


# --- Cabeceras y cookies seguras ---
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_HTTPONLY = True

if not DEBUG:
    # En producción todo va por HTTPS.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SSL_REDIRECT', 'True').lower() == 'true'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True


# --- Registro de eventos (en vez de print) ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
}
