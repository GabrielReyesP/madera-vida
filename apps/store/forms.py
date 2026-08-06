"""
apps/store/forms.py
Formulario de checkout. Se usa tanto para invitados como para clientes
registrados: siempre se piden nombre, email, telefono y RUT (dato
interno completo por pedido), aunque se prellenan si el usuario ya
tiene sesion iniciada.
"""

from django import forms

from apps.accounts.validators import validate_rut


class CheckoutForm(forms.Form):
    contact_name = forms.CharField(label='Nombre completo', max_length=150)
    contact_email = forms.EmailField(label='Correo electrónico')
    contact_phone = forms.CharField(label='Teléfono', max_length=20)
    contact_rut = forms.CharField(label='RUT', max_length=12, validators=[validate_rut])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        css = (
            'w-full border border-walnut/30 rounded-sm px-4 py-2 text-sm bg-white '
            'focus:outline-none focus:ring-2 focus:ring-clay'
        )
        for field in self.fields.values():
            field.widget.attrs['class'] = css
