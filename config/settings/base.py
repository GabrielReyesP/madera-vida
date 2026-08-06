"""
config/settings/base.py
Configuración base para Madera & Vida.
Compartida entre desarrollo y producción.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ============================================
# RUTAS Y VARIABLES DE ENTORNO
# ============================================
# BASE_DIR apunta a la raíz del proyecto (donde está manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Cargar variables de entorno desde .env
load_dotenv(os.path.join(BASE_DIR, '.env'))

# ============================================
# SEGURIDAD
# ============================================
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

if not SECRET_KEY:
    raise ValueError(
        "DJANGO_SECRET_KEY no está definida. "
        "Agrega la variable en tu archivo .env antes de iniciar el proyecto."
    )

# ALLOWED_HOSTS se configura en development.py / production.py
ALLOWED_HOSTS = []

# CSRF_TRUSTED_ORIGINS: necesario en producción con HTTPS y formularios HTMX.
# Sobrescribir en production.py con el(los) dominio(s) real(es), ej:
# CSRF_TRUSTED_ORIGINS = ['https://maderavida.cl']
CSRF_TRUSTED_ORIGINS = []

# ============================================
# APPS INSTALADAS
# ============================================
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  # Formateo de números (miles, millones)
]

THIRD_PARTY_APPS = [
    'django_htmx',           # Integración HTMX
    'widget_tweaks',         # Estilizar formularios en templates
]

LOCAL_APPS = [
    'apps.core',             # Debe ir PRIMERO: modelos base, audit log, configs
    'apps.accounts',         # Custom User, WorkerProfile, CustomerProfile
    'apps.catalog',          # Category, Product
    'apps.store',            # Order, OrderItem, Cart
    'apps.hr',               # Overtime, Payroll, Adjustments
    'apps.dashboard',        # Métricas y gráficos
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ============================================
# MIDDLEWARE
# ============================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',  # HTMX: detecta requests HTMX
    # 'apps.core.middleware.AuditLogMiddleware',  # Se activa en Fase 4
]

# ============================================
# URLS Y TEMPLATES
# ============================================
ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
              
               
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ============================================
# BASE DE DATOS - MySQL
# ============================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'madera_vida'),
        'USER': os.getenv('DB_USER', 'root'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# ============================================
# MODELO DE USUARIO PERSONALIZADO
# ============================================
# CRÍTICO: Debe definirse ANTES de la primera migración.
# Cambiarlo después requiere recrear la base de datos.
AUTH_USER_MODEL = 'accounts.CustomUser'

# ============================================
# VALIDACIÓN DE CONTRASEÑAS
# ============================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ============================================
# INTERNACIONALIZACIÓN
# ============================================
LANGUAGE_CODE = 'es-cl'  # Español de Chile

TIME_ZONE = 'America/Santiago'

USE_I18N = True
USE_TZ = True

# Formato de fechas y números chileno
DATE_FORMAT = 'd-m-Y'
DATETIME_FORMAT = 'd-m-Y H:i'
SHORT_DATE_FORMAT = 'd-m-Y'
TIME_FORMAT = 'H:i'

# ============================================
# ARCHIVOS ESTÁTICOS Y MEDIA
# ============================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Para producción

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Tamaño máximo de imágenes de productos (5 MB)
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

# ============================================
# SESIONES (para el carrito de compras)
# ============================================
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 7 días
SESSION_SAVE_EVERY_REQUEST = True  # Mantiene carrito activo

# ============================================
# EMAIL
# ============================================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Default: consola
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Madera & Vida <noreply@maderavida.cl>')

# ============================================
# AUTENTICACIÓN Y LOGIN
# ============================================
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:index'
LOGOUT_REDIRECT_URL = 'catalog:home'

# ============================================
# CONSTANTES CHILENAS (Madera & Vida)
# ============================================
# NOTA: MINIMUM_WAGE y otros valores legales cambian periódicamente.
# Estos valores son un fallback vía .env; para producción real de payroll
# (apps.hr) considera moverlos a un modelo en base de datos administrable
# desde el panel, para no depender de un deploy cada vez que cambia la ley.
CHILEAN_CONSTANTS = {
    'IVA_RATE': float(os.getenv('IVA_RATE', 0.19)),
    'MINIMUM_WAGE': float(os.getenv('MINIMUM_WAGE', 539000)),
    'WEEKLY_HOURS': int(os.getenv('WEEKLY_HOURS', 44)),
    'OVERTIME_MULTIPLIER': 1.5,  # Art. 32 Código del Trabajo
    'HEALTH_PERCENTAGE': 7.0,    # Fonasa / mínimo Isapre
    'CURRENCY': 'CLP',
    'CURRENCY_SYMBOL': '$',
}

# ============================================
# LOGGING
# ============================================
# Nivel configurable por entorno (ej: WARNING en producción)
DJANGO_LOG_LEVEL = os.getenv('DJANGO_LOG_LEVEL', 'INFO')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': DJANGO_LOG_LEVEL,
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': DJANGO_LOG_LEVEL,
            'propagate': False,
        },
    },
}

# Crear carpeta de logs si no existe.
# NOTA: si despliegas en un entorno con filesystem efímero o de solo lectura
# (algunos hosts serverless/contenedores), asegúrate de que exista un volumen
# persistente para 'logs/', o reemplaza el handler 'file' por uno compatible
# (ej. enviar logs a stdout/servicio externo) en production.py.
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# ============================================
# DEFAULT PRIMARY KEY
# ============================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'