"""
apps/store/admin.py
"""

from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'product_sku', 'quantity', 'unit_price_net', 'unit_price_iva')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'contact_name', 'status', 'total', 'created_at')
    list_filter = ('status',)
    search_fields = ('order_number', 'contact_name', 'contact_email', 'contact_rut')
    readonly_fields = ('order_number', 'net_total', 'iva_total', 'total', 'created_at', 'updated_at', 'paid_at')
    inlines = [OrderItemInline]
