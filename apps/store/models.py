"""
apps/store/models.py
Order y OrderItem: pedidos de la tienda online (RF-04 a RF-11, RF-18).
El carrito en si vive en la sesion (ver cart.py), no en la base de datos.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models


class Order(models.Model):
    """
    Pedido. Puede pertenecer a un cliente registrado (user) o a un
    invitado (user=None). Los datos de contacto (nombre, email, telefono,
    RUT) siempre se guardan en el pedido, sin importar si es invitado o
    cliente registrado (dato interno completo por pedido).
    """

    class Status(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        PAGADO = 'pagado', 'Pagado'
        LISTO_RETIRO = 'listo_retiro', 'Listo para retiro'
        ENTREGADO = 'entregado', 'Entregado'

    order_number = models.CharField('Numero de pedido', max_length=20, unique=True, blank=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='orders',
        verbose_name='Cliente registrado',
    )

    # Datos de contacto del pedido (snapshot, aplica a invitado y registrado).
    contact_name = models.CharField('Nombre de contacto', max_length=150)
    contact_email = models.EmailField('Correo de contacto')
    contact_phone = models.CharField('Telefono de contacto', max_length=20)
    contact_rut = models.CharField('RUT', max_length=12)

    status = models.CharField(
        'Estado', max_length=20, choices=Status.choices, default=Status.PENDIENTE,
    )

    net_total = models.DecimalField('Total neto', max_digits=10, decimal_places=0, default=0)
    iva_total = models.DecimalField('Total IVA', max_digits=10, decimal_places=0, default=0)
    total = models.DecimalField('Total', max_digits=10, decimal_places=0, default=0)

    created_at = models.DateTimeField('Creado', auto_now_add=True)
    paid_at = models.DateTimeField('Pagado', null=True, blank=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number or f'Pedido #{self.pk}'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.order_number:
            self.order_number = f'MV-{self.pk:06d}'
            super().save(update_fields=['order_number'])

    def recalculate_totals(self):
        """Recalcula neto/IVA/total en base a las lineas actuales del pedido."""
        items = self.items.all()
        self.net_total = sum((item.line_net for item in items), Decimal('0'))
        self.iva_total = sum((item.line_iva for item in items), Decimal('0'))
        self.total = self.net_total + self.iva_total
        self.save(update_fields=['net_total', 'iva_total', 'total'])

    @property
    def is_guest_order(self):
        return self.user_id is None


class OrderItem(models.Model):
    """
    Linea de un pedido. Guarda una 'foto' del precio y del producto al
    momento de la compra: si el producto cambia de precio o se elimina
    despues, este historico no se ve afectado.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Pedido')
    product = models.ForeignKey(
        'catalog.Product', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='order_items', verbose_name='Producto',
    )

    # Snapshot del producto (sobrevive aunque el producto se borre despues).
    product_name = models.CharField('Nombre del producto', max_length=150)
    product_sku = models.CharField('SKU', max_length=30)

    quantity = models.PositiveIntegerField('Cantidad')
    unit_price_net = models.DecimalField('Precio neto unitario', max_digits=10, decimal_places=0)
    unit_price_iva = models.DecimalField('IVA unitario', max_digits=10, decimal_places=0)

    class Meta:
        verbose_name = 'Linea de pedido'
        verbose_name_plural = 'Lineas de pedido'

    def __str__(self):
        return f'{self.quantity} x {self.product_name}'

    @property
    def line_net(self):
        return self.unit_price_net * self.quantity

    @property
    def line_iva(self):
        return self.unit_price_iva * self.quantity

    @property
    def line_total(self):
        return self.line_net + self.line_iva
