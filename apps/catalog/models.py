"""
apps/catalog/models.py
Category y Product: catalogo publico de Madera & Vida (RF-02, RF-03, RF-08).
"""

from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField('Nombre', max_length=100, unique=True)
    slug = models.SlugField('Slug', max_length=120, unique=True, blank=True)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('catalog:product_list') + f'?categoria={self.slug}'


class Product(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='products',
        verbose_name='Categoria',
    )
    name = models.CharField('Nombre', max_length=150)
    slug = models.SlugField('Slug', max_length=170, unique=True, blank=True)
    description = models.TextField('Descripcion', blank=True)
    image = models.ImageField('Imagen', upload_to='products/', blank=True, null=True)
    sku = models.CharField('SKU', max_length=30, unique=True)
    price_net = models.DecimalField('Precio neto (CLP)', max_digits=10, decimal_places=0)
    stock = models.PositiveIntegerField('Stock', default=0)
    low_stock_threshold = models.PositiveIntegerField('Umbral de alerta de stock', default=5)
    is_active = models.BooleanField('Activo (visible en tienda)', default=True)
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            i = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base_slug}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('catalog:product_detail', kwargs={'slug': self.slug})

    @property
    def price_with_iva(self):
        """Precio final mostrado al publico, con IVA incluido (RF-08, RL-01)."""
        iva_rate = Decimal(str(settings.CHILEAN_CONSTANTS['IVA_RATE']))
        total = self.price_net * (Decimal('1') + iva_rate)
        return total.quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    @property
    def iva_amount(self):
        return self.price_with_iva - self.price_net

    @property
    def is_low_stock(self):
        return self.stock <= self.low_stock_threshold

    @property
    def is_in_stock(self):
        return self.stock > 0
