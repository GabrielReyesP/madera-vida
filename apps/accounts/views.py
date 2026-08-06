"""
apps/accounts/views.py
Login (email), logout y registro de clientes (RF-05, RF-06, seccion 10).
"""

from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import NoReverseMatch, reverse

from .forms import CustomerRegisterForm, EmailAuthenticationForm


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
