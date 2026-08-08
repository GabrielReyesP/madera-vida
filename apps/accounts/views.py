"""
apps/accounts/views.py
Login (email), logout, registro de clientes (RF-05, RF-06, seccion 10)
y centro de privacidad con derechos ARCO (Ley 19.628 / 21.719, RL-07).
"""

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import NoReverseMatch, reverse

from .forms import CustomerDataForm, CustomerRegisterForm, EmailAuthenticationForm


class EmailLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = EmailAuthenticationForm

    def get_success_url(self):
        user = self.request.user
        if getattr(user, 'is_worker', False):
            # El panel interno (dashboard) se construye en Fase 4.
            # Mientras no exista, cae de vuelta al sitio publico.
            try:
                return reverse('dashboard:index')
            except NoReverseMatch:
                return reverse('catalog:home')
        return reverse('catalog:home')


def register(request):
    if request.user.is_authenticated:
        return redirect('catalog:home')

    if request.method == 'POST':
        form = CustomerRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('catalog:home')
    else:
        form = CustomerRegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


# --- Ley 19.628 / 21.719: derechos sobre datos personales (RL-07) ---

@login_required
def privacy_center(request):
    """Centro de privacidad: acceso, rectificacion y supresion de datos."""
    return render(request, 'accounts/privacy_center.html')


@login_required
def data_export(request):
    """
    Derecho de ACCESO: entrega al usuario una copia de sus datos
    personales en formato JSON legible y portable.
    """
    user = request.user
    data = {
        'cuenta': {
            'email': user.email,
            'nombre': user.first_name,
            'apellido': user.last_name,
            'tipo_de_usuario': user.get_user_type_display(),
            'fecha_de_registro': user.date_joined.isoformat(),
            'ultimo_acceso': user.last_login.isoformat() if user.last_login else None,
        },
    }

    customer_profile = getattr(user, 'customer_profile', None)
    if customer_profile:
        data['perfil_de_cliente'] = {
            'rut': customer_profile.rut,
            'telefono': customer_profile.phone,
            'direccion': customer_profile.address,
        }

    worker_profile = getattr(user, 'worker_profile', None)
    if worker_profile:
        data['perfil_de_trabajador'] = {
            'rut': worker_profile.rut,
            'rol': worker_profile.get_role_display(),
            'afp': worker_profile.afp,
            'sistema_de_salud': worker_profile.get_health_system_display(),
            'tipo_de_contrato': worker_profile.get_contract_type_display(),
            'fecha_de_contratacion': (
                worker_profile.hire_date.isoformat() if worker_profile.hire_date else None
            ),
        }

    from apps.store.models import Order
    orders = Order.objects.filter(user=user).prefetch_related('items')
    data['pedidos'] = [
        {
            'numero': o.order_number,
            'fecha': o.created_at.isoformat(),
            'estado': o.get_status_display(),
            'total': str(o.total),
            'productos': [
                {'nombre': i.product_name, 'cantidad': i.quantity} for i in o.items.all()
            ],
        }
        for o in orders
    ]

    response = JsonResponse(data, json_dumps_params={'ensure_ascii': False, 'indent': 2})
    response['Content-Disposition'] = 'attachment; filename="mis_datos_madera_vida.json"'
    return response


@login_required
def data_update(request):
    """Derecho de RECTIFICACION: el usuario corrige sus propios datos."""
    profile = getattr(request.user, 'customer_profile', None)
    if profile is None:
        messages.info(request, 'La rectificación de datos laborales se solicita a Recursos Humanos.')
        return redirect('accounts:privacy_center')

    if request.method == 'POST':
        form = CustomerDataForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tus datos fueron actualizados.')
            return redirect('accounts:privacy_center')
    else:
        form = CustomerDataForm(instance=profile, user=request.user)

    return render(request, 'accounts/data_update.html', {'form': form})


@login_required
def data_delete(request):
    """
    Derecho de SUPRESION. Se anonimiza la cuenta en vez de borrarla en
    duro: los pedidos deben conservarse por obligaciones tributarias y
    contables, pero se desvinculan de la persona y se limpian sus datos
    identificatorios.
    """
    user = request.user

    if getattr(user, 'is_worker', False):
        messages.error(
            request,
            'Las cuentas de trabajadores no pueden eliminarse aquí: los datos laborales '
            'tienen plazos de conservación legal. Contacta a Recursos Humanos.',
        )
        return redirect('accounts:privacy_center')

    if request.method == 'POST':
        if request.POST.get('confirm') != 'ELIMINAR':
            messages.error(request, 'Debes escribir ELIMINAR para confirmar.')
            return redirect('accounts:data_delete')

        from apps.store.models import Order

        # Los pedidos se conservan (obligacion tributaria) pero se anonimizan.
        Order.objects.filter(user=user).update(
            user=None,
            contact_name='Usuario eliminado',
            contact_email='',
            contact_phone='',
            contact_rut='',
        )

        logout(request)
        user.delete()
        messages.success(
            request,
            'Tu cuenta y tus datos personales fueron eliminados. '
            'Los registros contables se conservaron de forma anonimizada.',
        )
        return redirect('catalog:home')

    return render(request, 'accounts/data_delete.html')
