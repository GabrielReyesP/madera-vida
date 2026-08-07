"""
apps/core/audit.py
Helper para registrar entradas de auditoria (RF-20) desde las vistas
del panel interno que realizan acciones sensibles.
"""

from .middleware import get_current_request
from .models import AuditLog


def _get_client_ip(request):
    if request is None:
        return None
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_action(action, entity, entity_id='', before=None, after=None, request=None, user=None):
    """
    Crea un registro de auditoria.
    - action: uno de AuditLog.Action
    - entity: nombre del modelo afectado, ej. 'Product'
    - before/after: dicts serializables a JSON con los campos relevantes
      (no pasar objetos completos ni contraseñas/datos sensibles).
    """
    request = request or get_current_request()
    if user is None and request is not None:
        user = request.user if request.user.is_authenticated else None

    AuditLog.objects.create(
        user=user,
        action=action,
        entity=entity,
        entity_id=str(entity_id),
        before=before,
        after=after,
        ip_address=_get_client_ip(request),
    )
