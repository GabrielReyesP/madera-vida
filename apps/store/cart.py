"""
apps/store/cart.py
Carrito de compras basado en sesion (RF-04). No se guarda en la base
de datos: vive en request.session hasta que se confirma el pedido.
"""

from decimal import Decimal

from apps.catalog.models import Product

CART_SESSION_KEY = 'cart'


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if cart is None:
            cart = {}
            self.session[CART_SESSION_KEY] = cart
        self.cart = cart

    def _save(self):
        self.session[CART_SESSION_KEY] = self.cart
        self.session.modified = True

    def add(self, product, quantity=1):
        """
        Agrega 'quantity' unidades del producto. Nunca deja que la
        cantidad total en el carrito supere el stock disponible.
        Devuelve (ok: bool, mensaje: str).
        """
        product_id = str(product.id)
        current_qty = self.cart.get(product_id, 0)
        new_qty = current_qty + quantity

        if new_qty > product.stock:
            # Se ajusta al maximo disponible en vez de rechazar en seco.
            new_qty = product.stock
            if new_qty <= current_qty:
                return False, f'No hay más stock disponible de "{product.name}".'
            self.cart[product_id] = new_qty
            self._save()
            return True, f'Se agregó "{product.name}" (ajustado al stock disponible: {new_qty}).'

        self.cart[product_id] = new_qty
        self._save()
        return True, f'"{product.name}" agregado al carrito.'

    def update_quantity(self, product, quantity):
        product_id = str(product.id)
        if quantity <= 0:
            self.remove(product)
            return True, 'Producto eliminado del carrito.'
        if quantity > product.stock:
            quantity = product.stock
            self.cart[product_id] = quantity
            self._save()
            return True, f'Cantidad ajustada al stock disponible ({quantity}).'
        self.cart[product_id] = quantity
        self._save()
        return True, 'Cantidad actualizada.'

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self._save()

    def clear(self):
        # Hay que reasignar self.cart, no solo la sesion: _save() vuelve a
        # escribir self.cart, y si sigue apuntando al diccionario anterior
        # el carrito viejo se reescribe encima del vacio.
        self.cart = {}
        self._save()

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        products_map = {str(p.id): p for p in products}

        for product_id, quantity in self.cart.items():
            product = products_map.get(product_id)
            if not product:
                continue
            yield {
                'product': product,
                'quantity': quantity,
                'unit_price_net': product.price_net,
                'unit_price_with_iva': product.price_with_iva,
                'line_net': product.price_net * quantity,
                'line_total': product.price_with_iva * quantity,
            }

    def __len__(self):
        return sum(self.cart.values())

    def get_net_total(self):
        return sum((item['line_net'] for item in self), Decimal('0'))

    def get_total_price(self):
        return sum((item['line_total'] for item in self), Decimal('0'))

    def get_iva_total(self):
        return self.get_total_price() - self.get_net_total()

    def is_empty(self):
        return len(self.cart) == 0
