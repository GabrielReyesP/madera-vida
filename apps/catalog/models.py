"""
apps/catalog/models.py
Category y Product: catalogo publico de Madera & Vida (RF-02, RF-03, RF-08).

El SKU de cada producto se genera automaticamente segun su categoria,
con el formato '<PREFIJO>-<NUMERO>', ej. 'MUE-0001'. El prefijo se
deriva del nombre de la categoria (editable si se quiere algo distinto).
"""

import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import models, transaction
from django.urls import reverse
from django.utils.text import slugify


def _strip_accents(text):
    normalized = unicodedata.normalize('NFD', text)
    return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')


def generate_sku_prefix(name, exclude_pk=None):
    """
    Deriva un prefijo de SKU a partir del nombre de la categoria
    (ej. 'Muebles' -> 'MUE'), evitando choques con prefijos ya usados
    por otras categorias.
    """
    base = _strip_accents(name).upper()
    base = re.sub(r'[^A-Z]', '', base) or 'CAT'

    existing_qs = Category.objects.all()
    if exclude_pk:
        existing_qs = existing_qs.exclude(pk=exclude_pk)
    existing = set(existing_qs.exclude(sku_prefix__isnull=True).values_list('sku_prefix', flat=True))

    for length in (3, 4, 5, 6):
        candidate = base[:length]
        if candidate and candidate not in existing:
            return candidate

    # Si ni con 6 letras se libera un prefijo unico, se numera.
    candidate = base[:3]
    n = 2
    while f'{candidate}{n}' in existing:
        n += 1
    return f'{candidate}{n}'


class Category(models.Model):
    name = models.CharField('Nombre', max_length=100, unique=True)
    slug = models.SlugField('Slug', max_length=120, unique=True, blank=True)
    sku_prefix = models.CharField(
        'Prefijo SKU', max_length=8, unique=True, blank=True, null=True,
        help_text='Se genera automáticamente si se deja en blanco (ej. "Muebles" → "MUE").',
    )
    next_sku_seq = models.PositiveIntegerField(default=1, editable=False)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.sku_prefix:
            self.sku_prefix = generate_sku_prefix(self.name, exclude_pk=self.pk)
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
    sku = models.CharField('SKU', max_length=30, unique=True, blank=True)
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

        if not self.sku:
            self.sku = self._generate_sku()

        super().save(*args, **kwargs)

    def _generate_sku(self):
        """
        Genera el siguiente SKU de la categoria (ej. 'MUE-0004'), usando
        un contador por categoria protegido con select_for_update para
        evitar que dos productos creados al mismo tiempo choquen.
        """
        with transaction.atomic():
            category = Category.objects.select_for_update().get(pk=self.category_id)
            if not category.sku_prefix:
                category.sku_prefix = generate_sku_prefix(category.name, exclude_pk=category.pk)
            seq = category.next_sku_seq
            category.next_sku_seq = seq + 1
            category.save(update_fields=['sku_prefix', 'next_sku_seq'])
        return f'{category.sku_prefix}-{seq:04d}'

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
