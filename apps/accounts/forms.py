"""
apps/accounts/forms.py
Formularios para el admin de CustomUser. Necesarios porque el
UserCreationForm/UserChangeForm por defecto de Django asumen un
campo 'username' que este proyecto no usa (login por email).
"""

from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'user_type')


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = '__all__'
