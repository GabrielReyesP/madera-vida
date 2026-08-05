"""
config/settings/__init__.py
Selecciona la configuración según la variable de entorno DJANGO_ENV.
Uso:
  export DJANGO_ENV=development  (default)
  export DJANGO_ENV=production
"""

import os

env = os.getenv('DJANGO_ENV', 'development')

if env == 'production':
    from .production import *  # noqa: F401,F403
else:
    from .development import *  # noqa: F401,F403