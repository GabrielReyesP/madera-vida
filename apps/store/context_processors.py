"""
apps/store/context_processors.py
Expone el contador de items del carrito en todos los templates
(navbar), sin tener que pasarlo manualmente en cada vista.
"""

from .cart import Cart


def cart_count(request):
    return {'cart_item_count': len(Cart(request))}
