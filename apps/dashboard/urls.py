"""
apps/dashboard/urls.py
Panel interno (RF-14 a RF-20). Cuelga de /dashboard/.
"""

from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),

    path('productos/', views.product_list, name='product_list'),
    path('productos/nuevo/', views.product_create, name='product_create'),
    path('productos/<int:pk>/editar/', views.product_edit, name='product_edit'),
    path('productos/<int:pk>/activar/', views.product_toggle_active, name='product_toggle_active'),
    path('productos/<int:pk>/eliminar/', views.product_delete, name='product_delete'),

    path('pedidos/', views.order_list, name='order_list'),
    path('pedidos/<str:order_number>/avanzar/', views.order_update_status, name='order_update_status'),

    path('trabajadores/', views.worker_list, name='worker_list'),
    path('trabajadores/nuevo/', views.worker_create, name='worker_create'),
    path('trabajadores/<int:pk>/editar/', views.worker_edit, name='worker_edit'),
    path('trabajadores/<int:pk>/resetear-password/', views.worker_reset_password, name='worker_reset_password'),

    path('horas-extras/', views.overtime_list, name='overtime_list'),

    path('ajustes/', views.adjustment_list, name='adjustment_list'),

    path('liquidaciones/', views.payroll_list, name='payroll_list'),
    path('liquidaciones/generar/', views.payroll_generate, name='payroll_generate'),
    path('liquidaciones/<int:pk>/', views.payroll_detail, name='payroll_detail'),

    path('auditoria/', views.audit_log_view, name='audit_log'),
]
