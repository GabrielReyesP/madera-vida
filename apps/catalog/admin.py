"""
apps/catalog/admin.py
"""

from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'sku', 'category', 'price_net', 'display_price_with_iva',
        'stock', 'display_is_low_stock', 'is_active',
    )
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'sku')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(boolean=True, description='Stock bajo')
    def display_is_low_stock(self, obj):
        return obj.is_low_stock

    @admin.display(description='Precio c/IVA')
    def display_price_with_iva(self, obj):
        return f"${obj.price_with_iva:,.0f}".replace(',', '.')
