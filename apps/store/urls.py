"""
apps/store/urls.py
Cuelga de /store/ (definido en config/urls.py).
"""

from django.urls import path

from . import views

app_name = 'store'

urlpatterns = [
    path('carrito/', views.cart_detail, name='cart_detail'),
    path('carrito/agregar/<int:product_id>/', views.cart_add, name='cart_add'),
    path('carrito/actualizar/<int:product_id>/', views.cart_update, name='cart_update'),
    path('carrito/eliminar/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('pedido/<str:order_number>/', views.order_detail, name='order_detail'),
    path('mis-pedidos/', views.order_history, name='order_history'),
]
