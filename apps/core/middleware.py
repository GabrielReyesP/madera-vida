"""
apps/core/middleware.py
AuditLogMiddleware: guarda el request actual en un thread-local para
que apps.core.audit.log_action() pueda obtener IP/usuario aunque no
se le pase 'request' explicitamente (util para señales a futuro).
En las vistas de este proyecto se pasa 'request' explicitamente a
log_action(), asi que este middleware es un respaldo, no la via
principal de captura.
"""

import threading

_local = threading.local()


class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.request = request
        try:
            response = self.get_response(request)
        finally:
            _local.request = None
        return response


def get_current_request():
    return getattr(_local, 'request', None)
