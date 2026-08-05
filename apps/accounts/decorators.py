"""
apps/accounts/decorators.py
Decoradores de control de acceso por rol para vistas de Madera & Vida.
(Sección 10 de la documentación: "Permisos por rol aplicados en vistas")
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def worker_required(view_func):
    """
    Exige que el usuario esté autenticado y sea un trabajador
    (tenga worker_profile). Cualquier rol de trabajador pasa.
    """
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not hasattr(request.user, 'worker_profile'):
            raise PermissionDenied('Esta sección es solo para trabajadores.')
        return view_func(request, *args, **kwargs)
    return _wrapped


def role_required(*roles):
    """
    Exige que el trabajador tenga uno de los roles indicados.
    Uso: @role_required('jefatura', 'administracion')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            profile = getattr(request.user, 'worker_profile', None)
            if profile is None or profile.role not in roles:
                raise PermissionDenied('No tienes permiso para acceder a esta sección.')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def superior_required(view_func):
    """Solo Jefatura o Administración (nivel superior, acceso completo)."""
    return role_required('jefatura', 'administracion')(view_func)
