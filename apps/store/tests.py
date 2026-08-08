"""
apps/store/tests.py
Tests del carrito (RF-04), checkout y descuento de stock (RF-07).
"""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Category, Product

from .models import Order, OrderItem


class CartTests(TestCase):
    """RF-04: carrito en sesion, respetando stock disponible."""

    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name='Muebles')
        cls.product = Product.objects.create(
            category=cls.category, name='Silla', price_net=Decimal('10000'), stock=5,
        )

    def test_agregar_producto_al_carrito(self):
        self.client.post(reverse('store:cart_add', args=[self.product.id]), {'quantity': 2})
        response = self.client.get(reverse('store:cart_detail'))
        self.assertContains(response, 'Silla')

    def test_no_permite_agregar_mas_del_stock_disponible(self):
        self.client.post(reverse('store:cart_add', args=[self.product.id]), {'quantity': 99})
        session_cart = self.client.session.get('cart', {})
        self.assertEqual(session_cart[str(self.product.id)], 5)

    def test_actualizar_cantidad_se_limita_al_stock(self):
        self.client.post(reverse('store:cart_add', args=[self.product.id]), {'quantity': 1})
        self.client.post(reverse('store:cart_update', args=[self.product.id]), {'quantity': 50})
        session_cart = self.client.session.get('cart', {})
        self.assertEqual(session_cart[str(self.product.id)], 5)

    def test_eliminar_producto_del_carrito(self):
        self.client.post(reverse('store:cart_add', args=[self.product.id]), {'quantity': 1})
        self.client.post(reverse('store:cart_remove', args=[self.product.id]))
        session_cart = self.client.session.get('cart', {})
        self.assertNotIn(str(self.product.id), session_cart)


class CheckoutTests(TestCase):
    """RF-07, RF-09: pedido, descuento de stock y desglose neto/IVA."""

    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name='Muebles')
        cls.product = Product.objects.create(
            category=cls.category, name='Mesa', price_net=Decimal('100000'), stock=10,
        )

    def _datos_checkout(self):
        return {
            'contact_name': 'Ana Perez',
            'contact_email': 'ana@test.cl',
            'contact_phone': '+56912345678',
            'contact_rut': '11.111.111-1',
        }

    def test_checkout_crea_pedido_y_descuenta_stock(self):
        self.client.post(reverse('store:cart_add', args=[self.product.id]), {'quantity': 3})
        self.client.post(reverse('store:checkout'), self._datos_checkout())

        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.status, Order.Status.PAGADO)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 7)

    def test_totales_del_pedido_desglosan_neto_e_iva(self):
        self.client.post(reverse('store:cart_add', args=[self.product.id]), {'quantity': 2})
        self.client.post(reverse('store:checkout'), self._datos_checkout())

        order = Order.objects.first()
        self.assertEqual(order.net_total, Decimal('200000'))
        self.assertEqual(order.iva_total, Decimal('38000'))
        self.assertEqual(order.total, Decimal('238000'))
        self.assertEqual(order.net_total + order.iva_total, order.total)

    def test_checkout_con_rut_invalido_no_crea_pedido(self):
        self.client.post(reverse('store:cart_add', args=[self.product.id]), {'quantity': 1})
        datos = self._datos_checkout()
        datos['contact_rut'] = '12.345.678-9'  # DV incorrecto
        self.client.post(reverse('store:checkout'), datos)

        self.assertEqual(Order.objects.count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

    def test_carrito_queda_vacio_tras_el_checkout(self):
        self.client.post(reverse('store:cart_add', args=[self.product.id]), {'quantity': 1})
        self.client.post(reverse('store:checkout'), self._datos_checkout())
        self.assertEqual(self.client.session.get('cart', {}), {})

    def test_linea_de_pedido_guarda_precio_al_momento_de_la_compra(self):
        self.client.post(reverse('store:cart_add', args=[self.product.id]), {'quantity': 1})
        self.client.post(reverse('store:checkout'), self._datos_checkout())

        item = OrderItem.objects.first()
        precio_original = item.unit_price_net

        # Si el precio del producto cambia despues, la linea historica no cambia.
        self.product.price_net = Decimal('999999')
        self.product.save()
        item.refresh_from_db()
        self.assertEqual(item.unit_price_net, precio_original)
