"""
apps/store/views.py
Carrito, checkout, boleta e historial de pedidos (RF-04 a RF-11, RF-29).
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.catalog.models import Product

from .cart import Cart
from .forms import CheckoutForm
from .models import Order, OrderItem


def cart_detail(request):
    cart = Cart(request)
    context = {'cart': cart}
    return render(request, 'store/cart.html', context)


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = int(request.POST.get('quantity', 1))

    cart = Cart(request)
    ok, message = cart.add(product, quantity)
    messages.success(request, message) if ok else messages.error(request, message)

    next_url = request.POST.get('next') or reverse('catalog:product_list')
    return redirect(next_url)


@require_POST
def cart_update(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))

    cart = Cart(request)
    ok, message = cart.update_quantity(product, quantity)
    messages.info(request, message)
    return redirect('store:cart_detail')


@require_POST
def cart_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.remove(product)
    messages.info(request, f'"{product.name}" eliminado del carrito.')
    return redirect('store:cart_detail')


def checkout(request):
    cart = Cart(request)

    if cart.is_empty():
        messages.info(request, 'Tu carrito está vacío.')
        return redirect('store:cart_detail')

    initial = {}
    if request.user.is_authenticated:
        initial['contact_name'] = request.user.get_full_name()
        initial['contact_email'] = request.user.email
        customer_profile = getattr(request.user, 'customer_profile', None)
        if customer_profile:
            initial['contact_phone'] = customer_profile.phone
            initial['contact_rut'] = customer_profile.rut

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = _create_order_from_cart(request, cart, form.cleaned_data)
            if order is None:
                # _create_order_from_cart ya dejo el mensaje de error
                # (stock insuficiente detectado al confirmar).
                return redirect('store:cart_detail')

            cart.clear()
            _send_order_confirmation_email(order)
            messages.success(request, f'¡Pedido {order.order_number} confirmado!')
            return redirect('store:order_detail', order_number=order.order_number)
    else:
        form = CheckoutForm(initial=initial)

    context = {'cart': cart, 'form': form}
    return render(request, 'store/checkout.html', context)


def _create_order_from_cart(request, cart, contact_data):
    """
    Crea el pedido y sus lineas dentro de una transaccion, revalidando
    el stock en ese mismo instante (evita sobreventa por dos checkouts
    simultaneos). Descuenta el stock aqui (al confirmar el pedido).
    Como el pago es simulado, el pedido queda 'pagado' de inmediato.
    """
    product_ids = [item['product'].id for item in cart]

    with transaction.atomic():
        locked_products = {
            p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids)
        }

        for item in cart:
            product = locked_products.get(item['product'].id)
            if product is None or product.stock < item['quantity']:
                disponible = product.stock if product else 0
                messages.error(
                    request,
                    f'"{item["product"].name}" ya no tiene stock suficiente '
                    f'(disponible: {disponible}). Ajusta tu carrito.',
                )
                return None

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            contact_name=contact_data['contact_name'],
            contact_email=contact_data['contact_email'],
            contact_phone=contact_data['contact_phone'],
            contact_rut=contact_data['contact_rut'],
            status=Order.Status.PENDIENTE,
        )

        for item in cart:
            product = locked_products[item['product'].id]
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                product_sku=product.sku,
                quantity=item['quantity'],
                unit_price_net=product.price_net,
                unit_price_iva=product.price_with_iva - product.price_net,
            )
            product.stock -= item['quantity']
            product.save(update_fields=['stock'])

        order.recalculate_totals()

        # Pago simulado: siempre se aprueba en el mismo paso (RF-07).
        from django.utils import timezone
        order.status = Order.Status.PAGADO
        order.paid_at = timezone.now()
        order.save(update_fields=['status', 'paid_at'])

        return order


def _send_order_confirmation_email(order):
    subject = render_to_string('emails/order_confirmation_subject.txt', {'order': order}).strip()
    body = render_to_string('emails/order_confirmation_email.txt', {'order': order})
    send_mail(
        subject=subject,
        message=body,
        from_email=None,  # usa DEFAULT_FROM_EMAIL
        recipient_list=[order.contact_email],
        fail_silently=True,
    )


def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    # Un cliente registrado solo puede ver sus propios pedidos.
    # Los pedidos de invitado son visibles por numero (es su "boleta").
    if order.user_id and (not request.user.is_authenticated or order.user_id != request.user.id):
        if not request.user.is_authenticated or not getattr(request.user, 'is_worker', False):
            messages.error(request, 'No tienes acceso a ese pedido.')
            return redirect('catalog:home')

    context = {'order': order}
    return render(request, 'store/order_detail.html', context)


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    context = {'orders': orders}
    return render(request, 'store/order_history.html', context)
