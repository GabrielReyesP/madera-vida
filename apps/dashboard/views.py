"""
apps/dashboard/views.py
Panel interno: dashboard, CRUD de productos, gestion de pedidos,
reset de contraseñas de trabajadores y visor de auditoria.
(RF-14 a RF-20)
"""

import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.core.paginator import Paginator
from django.db.models import F, ProtectedError, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_POST

from apps.accounts.decorators import role_required, superior_required, worker_required
from apps.accounts.models import WorkerProfile
from apps.catalog.forms import ProductForm
from apps.catalog.models import Product
from apps.core.audit import log_action
from apps.core.models import AuditLog
from apps.store.models import Order

NEXT_STATUS = {
    Order.Status.PENDIENTE: Order.Status.PAGADO,
    Order.Status.PAGADO: Order.Status.LISTO_RETIRO,
    Order.Status.LISTO_RETIRO: Order.Status.ENTREGADO,
}


# --- Dashboard (RF-19) ---

@worker_required
def index(request):
    today = timezone.localdate()
    start_date = today - timedelta(days=13)

    sales_by_day = (
        Order.objects.filter(status=Order.Status.PAGADO, paid_at__date__gte=start_date)
        .annotate(day=TruncDate('paid_at'))
        .values('day')
        .annotate(total=Sum('total'))
        .order_by('day')
    )
    sales_map = {row['day']: float(row['total']) for row in sales_by_day}

    labels, data = [], []
    for i in range(14):
        day = start_date + timedelta(days=i)
        labels.append(day.strftime('%d-%m'))
        data.append(sales_map.get(day, 0))

    low_stock_products = Product.objects.filter(
        is_active=True, stock__lte=F('low_stock_threshold'),
    )

    context = {
        'sales_labels_json': json.dumps(labels),
        'sales_data_json': json.dumps(data),
        'low_stock_products': low_stock_products,
        'worker_profile': getattr(request.user, 'worker_profile', None),
    }
    return render(request, 'dashboard/index.html', context)


# --- Productos (RF-14, RF-15) ---

@worker_required
def product_list(request):
    products = Product.objects.select_related('category').order_by('name')
    can_manage = getattr(getattr(request.user, 'worker_profile', None), 'can_manage_catalog', False)
    context = {'products': products, 'can_manage': can_manage}
    return render(request, 'dashboard/product_list.html', context)


@role_required('jefatura', 'administracion')
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            log_action(
                AuditLog.Action.PRODUCT_CREATE, 'Product', product.pk,
                after={'name': product.name, 'sku': product.sku,
                       'price_net': str(product.price_net), 'stock': product.stock},
                request=request,
            )
            messages.success(request, f'Producto "{product.name}" creado.')
            return redirect('dashboard:product_list')
    else:
        form = ProductForm()

    return render(request, 'dashboard/product_form.html', {'form': form, 'is_new': True})


@role_required('jefatura', 'administracion')
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    before = {
        'name': product.name, 'price_net': str(product.price_net),
        'stock': product.stock, 'is_active': product.is_active,
    }

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            after = {
                'name': product.name, 'price_net': str(product.price_net),
                'stock': product.stock, 'is_active': product.is_active,
            }
            log_action(AuditLog.Action.PRODUCT_UPDATE, 'Product', product.pk,
                       before=before, after=after, request=request)
            messages.success(request, f'Producto "{product.name}" actualizado.')
            return redirect('dashboard:product_list')
    else:
        form = ProductForm(instance=product)

    return render(request, 'dashboard/product_form.html', {'form': form, 'is_new': False, 'product': product})


@require_POST
@role_required('jefatura', 'administracion')
def product_toggle_active(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save(update_fields=['is_active'])

    action = AuditLog.Action.PRODUCT_ACTIVATE if product.is_active else AuditLog.Action.PRODUCT_DEACTIVATE
    log_action(action, 'Product', product.pk, after={'is_active': product.is_active}, request=request)

    messages.success(request, f'Producto "{product.name}" {"activado" if product.is_active else "desactivado"}.')
    return redirect('dashboard:product_list')


@require_POST
@role_required('jefatura', 'administracion')
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    name = product.name
    try:
        product.delete()
        log_action(AuditLog.Action.PRODUCT_DELETE, 'Product', pk, before={'name': name}, request=request)
        messages.success(request, f'Producto "{name}" eliminado.')
    except ProtectedError:
        messages.error(
            request,
            f'"{name}" no se puede eliminar porque tiene pedidos asociados. '
            f'Puedes desactivarlo en su lugar.',
        )
    return redirect('dashboard:product_list')


# --- Pedidos (RF-18) ---

@role_required('jefatura', 'administracion', 'venta')
def order_list(request):
    orders = list(Order.objects.all().order_by('-created_at'))
    for order in orders:
        next_status = NEXT_STATUS.get(order.status)
        order.next_status_label = next_status.label if next_status else None

    context = {'orders': orders}
    return render(request, 'dashboard/order_list.html', context)


@require_POST
@role_required('jefatura', 'administracion', 'venta')
def order_update_status(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    next_status = NEXT_STATUS.get(order.status)

    if not next_status:
        messages.error(request, 'Este pedido ya está en su estado final.')
        return redirect('dashboard:order_list')

    before_status = order.status
    order.status = next_status
    order.save(update_fields=['status'])

    log_action(
        AuditLog.Action.ORDER_STATUS_CHANGE, 'Order', order.order_number,
        before={'status': before_status}, after={'status': order.status}, request=request,
    )
    messages.success(request, f'Pedido {order.order_number} → {order.get_status_display()}.')
    return redirect('dashboard:order_list')


# --- Trabajadores: reset de contraseña (RF-17) ---

@superior_required
def worker_list(request):
    workers = WorkerProfile.objects.select_related('user').order_by('user__first_name')
    context = {'workers': workers}
    return render(request, 'dashboard/worker_list.html', context)


@require_POST
@superior_required
def worker_reset_password(request, pk):
    worker = get_object_or_404(WorkerProfile, pk=pk)
    user = worker.user

    new_password = get_random_string(
        length=12, allowed_chars='abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789'
    )
    user.password = make_password(new_password)
    user.save(update_fields=['password'])

    # Nunca se guarda la contraseña en el log de auditoria.
    log_action(AuditLog.Action.WORKER_PASSWORD_RESET, 'CustomUser', user.pk, request=request)

    context = {'worker': worker, 'new_password': new_password}
    return render(request, 'dashboard/worker_password_reset_result.html', context)


# --- Auditoria (RF-20) ---

@superior_required
def audit_log_view(request):
    logs = AuditLog.objects.select_related('user').all()
    paginator = Paginator(logs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'dashboard/audit_log.html', {'page_obj': page_obj})
