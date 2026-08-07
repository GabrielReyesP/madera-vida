"""
apps/catalog/forms.py
Formulario de producto para el panel interno (RF-15: solo nivel
superior puede crear/modificar).
"""

from django import forms

from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'category', 'name', 'description', 'image',
            'price_net', 'stock', 'low_stock_threshold', 'is_active',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        css = (
            'w-full border border-walnut/30 rounded-sm px-4 py-2 text-sm bg-white '
            'focus:outline-none focus:ring-2 focus:ring-clay'
        )
        for name, field in self.fields.items():
            if name == 'is_active':
                field.widget.attrs['class'] = 'h-4 w-4'
            else:
                field.widget.attrs['class'] = css
