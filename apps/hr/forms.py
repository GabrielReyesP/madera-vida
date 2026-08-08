"""
apps/hr/forms.py
Formularios de RRHH: horas extras, anticipos/bonos/descuentos y
generacion de liquidaciones (RF-16, RF-25, RF-26).
"""

from django import forms

from apps.accounts.forms import TailwindStyledFormMixin
from apps.accounts.models import WorkerProfile

from .models import OvertimeRecord, PayrollAdjustment


class OvertimeRecordForm(TailwindStyledFormMixin, forms.ModelForm):
    class Meta:
        model = OvertimeRecord
        fields = ('worker', 'date', 'hours')
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}


class PayrollAdjustmentForm(TailwindStyledFormMixin, forms.ModelForm):
    class Meta:
        model = PayrollAdjustment
        fields = ('worker', 'adjustment_type', 'amount', 'period', 'description')
        widgets = {'period': forms.DateInput(attrs={'type': 'date'})}


class PayrollGenerateForm(TailwindStyledFormMixin, forms.Form):
    worker = forms.ModelChoiceField(queryset=WorkerProfile.objects.all(), label='Trabajador')
    period = forms.DateField(
        label='Periodo (mes)', widget=forms.DateInput(attrs={'type': 'date'}),
        help_text='Elige cualquier día del mes que quieres liquidar.',
    )
