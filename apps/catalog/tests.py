"""
apps/catalog/tests.py
Tests de calculo de IVA (RL-01) y generacion automatica de SKU.
"""

from decimal import Decimal

from django.test import TestCase

from .models import Category, Product, generate_sku_prefix


class IvaCalculationTests(TestCase):
    """RL-01 / RF-08: IVA 19% calculado y desglosado correctamente."""

    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name='Muebles')

    def _crear_producto(self, price_net):
        return Product.objects.create(
            category=self.category, name=f'Producto {price_net}',
            price_net=Decimal(price_net), stock=10,
        )

    def test_iva_sobre_precio_redondo(self):
        product = self._crear_producto('10000')
        self.assertEqual(product.price_with_iva, Decimal('11900'))
        self.assertEqual(product.iva_amount, Decimal('1900'))

    def test_iva_redondea_a_peso_entero(self):
        # 12345 * 1.19 = 14690.55 -> 14691 (CLP no tiene decimales)
        product = self._crear_producto('12345')
        self.assertEqual(product.price_with_iva, Decimal('14691'))

    def test_neto_mas_iva_es_igual_al_total(self):
        product = self._crear_producto('45990')
        self.assertEqual(product.price_net + product.iva_amount, product.price_with_iva)


class StockStatusTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name='Decoracion')

    def test_producto_sin_stock_no_esta_disponible(self):
        product = Product.objects.create(
            category=self.category, name='Agotado', price_net=Decimal('5000'), stock=0,
        )
        self.assertFalse(product.is_in_stock)

    def test_stock_bajo_umbral_activa_alerta(self):
        product = Product.objects.create(
            category=self.category, name='Poco stock', price_net=Decimal('5000'),
            stock=3, low_stock_threshold=5,
        )
        self.assertTrue(product.is_low_stock)

    def test_stock_sobre_umbral_no_activa_alerta(self):
        product = Product.objects.create(
            category=self.category, name='Stock ok', price_net=Decimal('5000'),
            stock=20, low_stock_threshold=5,
        )
        self.assertFalse(product.is_low_stock)


class SkuGenerationTests(TestCase):
    """SKU automatico por categoria."""

    def test_prefijo_se_deriva_del_nombre(self):
        category = Category.objects.create(name='Muebles')
        self.assertEqual(category.sku_prefix, 'MUE')

    def test_prefijo_ignora_acentos(self):
        category = Category.objects.create(name='Decoración')
        self.assertEqual(category.sku_prefix, 'DEC')

    def test_prefijos_no_colisionan_entre_categorias_similares(self):
        c1 = Category.objects.create(name='Sillas')
        c2 = Category.objects.create(name='Sillones')
        c3 = Category.objects.create(name='Silletas')
        prefijos = {c1.sku_prefix, c2.sku_prefix, c3.sku_prefix}
        self.assertEqual(len(prefijos), 3, f'Prefijos duplicados: {prefijos}')

    def test_sku_se_genera_con_secuencia_por_categoria(self):
        category = Category.objects.create(name='Mesas')
        p1 = Product.objects.create(category=category, name='Mesa A', price_net=Decimal('50000'), stock=1)
        p2 = Product.objects.create(category=category, name='Mesa B', price_net=Decimal('60000'), stock=1)
        self.assertEqual(p1.sku, 'MES-0001')
        self.assertEqual(p2.sku, 'MES-0002')

    def test_secuencias_son_independientes_entre_categorias(self):
        cat_a = Category.objects.create(name='Estantes')
        cat_b = Category.objects.create(name='Puertas')
        pa = Product.objects.create(category=cat_a, name='Estante 1', price_net=Decimal('10000'), stock=1)
        pb = Product.objects.create(category=cat_b, name='Puerta 1', price_net=Decimal('10000'), stock=1)
        self.assertTrue(pa.sku.endswith('0001'))
        self.assertTrue(pb.sku.endswith('0001'))
        self.assertNotEqual(pa.sku, pb.sku)

    def test_sku_manual_se_respeta(self):
        category = Category.objects.create(name='Especiales')
        product = Product.objects.create(
            category=category, name='Custom', sku='MANUAL-999',
            price_net=Decimal('10000'), stock=1,
        )
        self.assertEqual(product.sku, 'MANUAL-999')
