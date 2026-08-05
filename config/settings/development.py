"""
config/settings/development.py
Configuración para entorno de desarrollo local / VM.
"""

from .base import *  # noqa: F401,F403

# ============================================
# DEBUG Y HOSTS
# ============================================
DEBUG = True

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')  # noqa: F405

# ============================================
# EMAIL: Se imprime en consola (no se envía)
# ============================================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ============================================
# DEBUG TOOLBAR (opcional, muy útil)
# ============================================
# pip install django-debug-toolbar
# INSTALLED_APPS += ['debug_toolbar']  # noqa: F405
# MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')  # noqa: F405
# INTERNAL_IPS = ['127.0.0.1']

# ============================================
# SQL en consola (para ver queries durante desarrollo)
# ============================================
# LOGGING['loggers']['django.db.backends'] = {  # noqa: F405
#     'handlers': ['console'],
#     'level': 'DEBUG',
#     'propagate': False,
# }