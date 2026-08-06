"""
apps/accounts/forms.py
Formularios de accounts:
- CustomUserCreationForm / CustomUserChangeForm: para el admin de Django
  (necesarios porque CustomUser no tiene campo 'username').
- EmailAuthenticationForm: login estilizado con Tailwind.
- CustomerRegisterForm: registro de clientes (RF-06), crea CustomUser +
  CustomerProfile en un solo paso.
- StyledPasswordResetForm / StyledSetPasswordForm: recuperacion de
  contrasena (RF-12) con el mismo estilo visual.
"""

from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
    UserChangeForm,
    UserCreationForm,
)

from .models import CustomerProfile, CustomUser


class TailwindStyledFormMixin:
    """Aplica estilos Tailwind consistentes a todos los campos del formulario."""

    input_css = (
        'w-full border border-walnut/30 rounded-sm px-4 py-2 text-sm bg-white '
        'focus:outline-none focus:ring-2 focus:ring-clay'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing} {self.input_css}'.strip()


# --- Formularios del admin de Django (login por email, sin username) ---

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'user_type')


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = '__all__'


# --- Formularios del sitio publico ---

class EmailAuthenticationForm(TailwindStyledFormMixin, AuthenticationForm):
    """Login estandar de Django; funciona con USERNAME_FIELD='email'."""
    pass


class CustomerRegisterForm(TailwindStyledFormMixin, UserCreationForm):
    """Registro de clientes (RF-06). Crea CustomUser + CustomerProfile."""

    field_order = ['email', 'first_name', 'last_name', 'password1', 'password2']

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('email', 'first_name', 'last_name')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = CustomUser.UserType.CUSTOMER
        if commit:
            user.save()
            CustomerProfile.objects.create(user=user)
        return user


class StyledPasswordResetForm(TailwindStyledFormMixin, PasswordResetForm):
    pass


class StyledSetPasswordForm(TailwindStyledFormMixin, SetPasswordForm):
    pass
