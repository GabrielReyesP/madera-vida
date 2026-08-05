"""
config/settings/production.py
Configuración para entorno de producción.
"""

from .base import *  # noqa: F401,F403

# ============================================
# DEBUG Y HOSTS
# ============================================
DEBUG = False

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')  # noqa: F405

# ============================================
# SEGURIDAD
# ============================================
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# CSRF
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

# Sesiones
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Redirección HTTPS
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ============================================
# EMAIL: SMTP real
# ============================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# ============================================
# STATIC FILES: WhiteNoise (si no usas Nginx)
# ============================================
# pip install whitenoise
# MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')  # noqa: F405
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'  # noqa: F405