"""
apps/core/context_processors.py
Hace disponible 'company' en todos los templates (navbar, footer, etc.)
sin tener que pasarlo manualmente en cada vista.
"""

from .models import CompanyInfo


def company_info(request):
    return {'company': CompanyInfo.get_solo()}
