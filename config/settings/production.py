"""
config/settings/production.py
Configuración para entorno de producción.
"""

from .base import *  # noqa: F401,F403

# ============================================
# DEBUG Y HOSTS
# ============================================
DEBUG = False

ALLOWED_HOSTS = [h.strip() for h in os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',') if h.strip()]  # noqa: F405

# Necesario para que los formularios (POST) funcionen detras de HTTPS/Nginx.
# Debe incluir el esquema, ej: https://maderavida.cl,https://www.maderavida.cl
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()
]  # noqa: F405

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
# Nginx termina el TLS y reenvia por HTTP, asi que Django necesita este
# header para saber que la peticion original si venia por HTTPS (sin esto,
# SECURE_SSL_REDIRECT provoca un bucle infinito de redirecciones).
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
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