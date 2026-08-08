"""
apps/accounts/urls.py
Login, logout, registro y recuperacion de contrasena (RF-05, RF-06, RF-12).
"""

from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .forms import StyledPasswordResetForm, StyledSetPasswordForm

app_name = 'accounts'

urlpatterns = [
    path('login/', views.EmailLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='catalog:home'), name='logout'),
    path('registro/', views.register, name='register'),

    # Ley 19.628 / 21.719: derechos sobre datos personales
    path('privacidad/', views.privacy_center, name='privacy_center'),
    path('privacidad/mis-datos/', views.data_export, name='data_export'),
    path('privacidad/rectificar/', views.data_update, name='data_update'),
    path('privacidad/eliminar/', views.data_delete, name='data_delete'),

    # Recuperacion de contrasena para clientes (RF-12)
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            email_template_name='emails/password_reset_email.txt',
            subject_template_name='emails/password_reset_subject.txt',
            form_class=StyledPasswordResetForm,
            success_url=reverse_lazy('accounts:password_reset_done'),
        ),
        name='password_reset',
    ),
    path(
        'password-reset/enviado/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'password-reset/confirmar/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            form_class=StyledSetPasswordForm,
            success_url=reverse_lazy('accounts:password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),
    path(
        'password-reset/completo/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
]
