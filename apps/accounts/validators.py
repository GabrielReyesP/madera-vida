"""
apps/accounts/validators.py
Validadores personalizados para Madera & Vida.
"""

import re

from django.core.exceptions import ValidationError


def validate_rut(value):
    """
    Valida un RUT chileno con dígito verificador (módulo 11).
    Acepta formatos como '12345678-9', '12.345.678-9' o '123456789'.
    (Requerimiento RL-02)
    """
    rut = re.sub(r'[.\-\s]', '', value).upper()

    if len(rut) < 2:
        raise ValidationError('RUT inválido: formato incompleto.')

    cuerpo, dv = rut[:-1], rut[-1]

    if not cuerpo.isdigit():
        raise ValidationError('RUT inválido: el cuerpo debe contener solo números.')

    suma = 0
    multiplicador = 2
    for digito in reversed(cuerpo):
        suma += int(digito) * multiplicador
        multiplicador = multiplicador + 1 if multiplicador < 7 else 2

    resto = suma % 11
    dv_calculado = 11 - resto

    if dv_calculado == 11:
        dv_esperado = '0'
    elif dv_calculado == 10:
        dv_esperado = 'K'
    else:
        dv_esperado = str(dv_calculado)

    if dv != dv_esperado:
        raise ValidationError(
            f'RUT inválido: el dígito verificador no coincide (se esperaba "{dv_esperado}").'
        )


def validate_minimum_wage(value):
    """
    Valida que el sueldo base no sea inferior al sueldo minimo vigente
    (RL-03, RF-22). Import diferido de apps.core.models para no acoplar
    accounts a core en tiempo de carga del modulo.
    """
    from apps.core.models import MinimumWageConfig

    minimum = MinimumWageConfig.get_current()
    if value < minimum:
        raise ValidationError(
            f'El sueldo base (${value:,.0f}) no puede ser menor al sueldo mínimo vigente '
            f'(${minimum:,.0f}).'.replace(',', '.')
        )
