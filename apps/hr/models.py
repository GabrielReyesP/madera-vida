"""
apps/hr/models.py
OvertimeRecord, PayrollAdjustment, PayrollRecord: RRHH y liquidaciones
de sueldo (RF-16, RF-23 a RF-26, seccion 8 del documento).

Formulas (seccion 8, aplicadas tal cual las define el documento):
  valor_hora_ordinaria = (sueldo_base x 7) / (jornada_semanal x 30)
  valor_hora_extra      = valor_hora_ordinaria x 1.5
  imponible             = sueldo_base + horas_extras + bonos
  cotizacion_afp        = imponible x %AFP
  cotizacion_salud      = imponible x 7%
  liquido               = imponible - AFP - salud - descuentos - anticipos
"""

from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import models

from apps.accounts.models import WorkerProfile
from apps.core.models import AfpConfig


class OvertimeRecord(models.Model):
    """Horas extras de un trabajador (RF-16, RF-24, RL-04)."""

    class Status(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        APROBADA = 'aprobada', 'Aprobada'
        PAGADA = 'pagada', 'Pagada'

    worker = models.ForeignKey(
        WorkerProfile, on_delete=models.CASCADE,
        related_name='overtime_records', verbose_name='Trabajador',
    )
    date = models.DateField('Fecha')
    hours = models.DecimalField('Horas extras', max_digits=4, decimal_places=2)

    # Snapshot calculado al momento de guardar (no se recalcula si el
    # sueldo base del trabajador cambia despues).
    hourly_rate = models.DecimalField('Valor hora ordinaria', max_digits=10, decimal_places=0, editable=False)
    overtime_rate = models.DecimalField('Valor hora extra (1.5x)', max_digits=10, decimal_places=0, editable=False)
    total = models.DecimalField('Total', max_digits=10, decimal_places=0, editable=False)

    status = models.CharField('Estado', max_length=20, choices=Status.choices, default=Status.PENDIENTE)
    created_at = models.DateTimeField('Registrado', auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de horas extras'
        verbose_name_plural = 'Registros de horas extras'
        ordering = ['-date']

    def __str__(self):
        return f'{self.worker} · {self.date:%d-%m-%Y} · {self.hours}h'

    def save(self, *args, **kwargs):
        weekly_hours = Decimal(str(settings.CHILEAN_CONSTANTS['WEEKLY_HOURS']))
        self.hourly_rate = self._round(self.worker.base_salary * 7 / (weekly_hours * 30))
        self.overtime_rate = self._round(self.hourly_rate * Decimal('1.5'))
        self.total = self._round(self.overtime_rate * self.hours)
        super().save(*args, **kwargs)

    @staticmethod
    def _round(value):
        return Decimal(value).quantize(Decimal('1'), rounding=ROUND_HALF_UP)


class PayrollAdjustment(models.Model):
    """Anticipos, bonos y descuentos aplicados a un periodo (RF-25)."""

    class AdjustmentType(models.TextChoices):
        ANTICIPO = 'anticipo', 'Anticipo'
        BONO = 'bono', 'Bono'
        DESCUENTO = 'descuento', 'Descuento'

    worker = models.ForeignKey(
        WorkerProfile, on_delete=models.CASCADE,
        related_name='payroll_adjustments', verbose_name='Trabajador',
    )
    adjustment_type = models.CharField('Tipo', max_length=20, choices=AdjustmentType.choices)
    amount = models.DecimalField('Monto (CLP)', max_digits=10, decimal_places=0)
    period = models.DateField(
        'Periodo (mes)', help_text='Cualquier día del mes correspondiente; se normaliza al día 1.',
    )
    description = models.CharField('Descripción', max_length=255, blank=True)
    created_at = models.DateTimeField('Registrado', auto_now_add=True)

    class Meta:
        verbose_name = 'Anticipo / bono / descuento'
        verbose_name_plural = 'Anticipos, bonos y descuentos'
        ordering = ['-period']

    def __str__(self):
        return f'{self.get_adjustment_type_display()} · {self.worker} · ${self.amount:,.0f}'.replace(',', '.')

    def save(self, *args, **kwargs):
        self.period = self.period.replace(day=1)
        super().save(*args, **kwargs)


class PayrollRecord(models.Model):
    """Liquidacion de sueldo mensual de un trabajador (RF-26)."""

    class Status(models.TextChoices):
        BORRADOR = 'borrador', 'Borrador'
        EMITIDA = 'emitida', 'Emitida'
        PAGADA = 'pagada', 'Pagada'

    worker = models.ForeignKey(
        WorkerProfile, on_delete=models.CASCADE,
        related_name='payroll_records', verbose_name='Trabajador',
    )
    period = models.DateField('Periodo (mes)', help_text='Se normaliza al día 1 del mes.')

    base_salary = models.DecimalField('Sueldo base', max_digits=10, decimal_places=0, editable=False)
    overtime_total = models.DecimalField('Total horas extras', max_digits=10, decimal_places=0, default=0, editable=False)
    bonuses_total = models.DecimalField('Total bonos', max_digits=10, decimal_places=0, default=0, editable=False)
    taxable_income = models.DecimalField('Imponible', max_digits=10, decimal_places=0, editable=False)

    afp_name = models.CharField('AFP aplicada', max_length=50, editable=False)
    afp_percentage = models.DecimalField('% AFP aplicado', max_digits=5, decimal_places=2, editable=False)
    afp_amount = models.DecimalField('Cotización AFP', max_digits=10, decimal_places=0, editable=False)
    health_amount = models.DecimalField('Cotización salud (7%)', max_digits=10, decimal_places=0, editable=False)

    advances_total = models.DecimalField('Total anticipos', max_digits=10, decimal_places=0, default=0, editable=False)
    deductions_total = models.DecimalField('Total descuentos', max_digits=10, decimal_places=0, default=0, editable=False)

    net_pay = models.DecimalField('Líquido a pagar', max_digits=10, decimal_places=0, editable=False)

    status = models.CharField('Estado', max_length=20, choices=Status.choices, default=Status.EMITIDA)
    created_at = models.DateTimeField('Generada', auto_now_add=True)

    class Meta:
        verbose_name = 'Liquidación de sueldo'
        verbose_name_plural = 'Liquidaciones de sueldo'
        unique_together = ('worker', 'period')
        ordering = ['-period']

    def __str__(self):
        return f'{self.worker} · {self.period:%m-%Y}'

    @staticmethod
    def _round(value):
        return Decimal(value).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    def calculate(self):
        """
        Calcula bruto/AFP/salud/liquido para self.worker y self.period,
        segun las formulas de la seccion 8 del documento. No persiste
        el registro; llamar a .save() despues para guardarlo.
        """
        HUNDRED = Decimal('100')
        self.period = self.period.replace(day=1)

        if self.period.month == 12:
            period_end = self.period.replace(year=self.period.year + 1, month=1)
        else:
            period_end = self.period.replace(month=self.period.month + 1)

        overtime_total = sum(
            (o.total for o in OvertimeRecord.objects.filter(
                worker=self.worker, date__gte=self.period, date__lt=period_end,
            )),
            Decimal('0'),
        )

        adjustments = list(PayrollAdjustment.objects.filter(worker=self.worker, period=self.period))
        bonuses_total = sum(
            (a.amount for a in adjustments if a.adjustment_type == PayrollAdjustment.AdjustmentType.BONO),
            Decimal('0'),
        )
        advances_total = sum(
            (a.amount for a in adjustments if a.adjustment_type == PayrollAdjustment.AdjustmentType.ANTICIPO),
            Decimal('0'),
        )
        deductions_total = sum(
            (a.amount for a in adjustments if a.adjustment_type == PayrollAdjustment.AdjustmentType.DESCUENTO),
            Decimal('0'),
        )

        base_salary = self.worker.base_salary
        taxable_income = base_salary + overtime_total + bonuses_total

        afp_config = AfpConfig.objects.filter(name__iexact=self.worker.afp, is_active=True).first()
        afp_name = afp_config.name if afp_config else (self.worker.afp or 'No especificada')
        afp_percentage = afp_config.percentage if afp_config else Decimal('10.00')

        afp_amount = self._round(taxable_income * afp_percentage / HUNDRED)
        health_amount = self._round(taxable_income * Decimal('7.00') / HUNDRED)

        net_pay = taxable_income - afp_amount - health_amount - deductions_total - advances_total

        self.base_salary = base_salary
        self.overtime_total = overtime_total
        self.bonuses_total = bonuses_total
        self.taxable_income = taxable_income
        self.afp_name = afp_name
        self.afp_percentage = afp_percentage
        self.afp_amount = afp_amount
        self.health_amount = health_amount
        self.advances_total = advances_total
        self.deductions_total = deductions_total
        self.net_pay = net_pay
        return self
