"""
apps/hr/tests.py
Tests de calculos previsionales chilenos (seccion 8 del documento):
horas extras (RL-04), AFP y salud (RL-06), liquido a pagar (RF-26).
"""

from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import CustomUser, WorkerProfile
from apps.core.models import AfpConfig, MinimumWageConfig

from .models import OvertimeRecord, PayrollAdjustment, PayrollRecord


class HrTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        MinimumWageConfig.objects.create(value=Decimal('500000'), effective_date=date(2020, 1, 1))
        AfpConfig.objects.create(name='Modelo', percentage=Decimal('10.58'))

        user = CustomUser.objects.create_user(
            email='trabajador@test.cl', password='Test1234',
            first_name='Juan', last_name='Soto', user_type='worker',
        )
        cls.worker = WorkerProfile.objects.create(
            user=user, rut='11.111.111-1', role='venta',
            afp='Modelo', base_salary=Decimal('660000'),
        )


class OvertimeCalculationTests(HrTestBase):
    """RL-04: hora extra con recargo del 50%."""

    def test_valor_hora_ordinaria_usa_la_formula_del_documento(self):
        # (sueldo_base x 7) / (jornada_semanal x 30)
        # (660000 * 7) / (44 * 30) = 4620000 / 1320 = 3500
        record = OvertimeRecord.objects.create(
            worker=self.worker, date=date(2026, 8, 5), hours=Decimal('1'),
        )
        self.assertEqual(record.hourly_rate, Decimal('3500'))

    def test_hora_extra_tiene_recargo_del_50_por_ciento(self):
        record = OvertimeRecord.objects.create(
            worker=self.worker, date=date(2026, 8, 5), hours=Decimal('1'),
        )
        self.assertEqual(record.overtime_rate, Decimal('5250'))  # 3500 * 1.5

    def test_total_multiplica_valor_hora_extra_por_horas(self):
        record = OvertimeRecord.objects.create(
            worker=self.worker, date=date(2026, 8, 5), hours=Decimal('4'),
        )
        self.assertEqual(record.total, Decimal('21000'))  # 5250 * 4

    def test_valores_no_cambian_si_el_sueldo_base_cambia_despues(self):
        record = OvertimeRecord.objects.create(
            worker=self.worker, date=date(2026, 8, 5), hours=Decimal('2'),
        )
        total_original = record.total

        self.worker.base_salary = Decimal('1200000')
        self.worker.save()
        record.refresh_from_db()

        self.assertEqual(record.total, total_original)


class PayrollCalculationTests(HrTestBase):
    """RF-23, RF-26: AFP, salud 7% y liquido a pagar."""

    def _liquidar(self, period=date(2026, 8, 1)):
        record = PayrollRecord(worker=self.worker, period=period)
        record.calculate()
        record.save()
        return record

    def test_imponible_sin_extras_es_el_sueldo_base(self):
        record = self._liquidar()
        self.assertEqual(record.taxable_income, Decimal('660000'))

    def test_cotizacion_afp_usa_el_porcentaje_configurado(self):
        record = self._liquidar()
        # 660000 * 10.58% = 69828
        self.assertEqual(record.afp_amount, Decimal('69828'))
        self.assertEqual(record.afp_name, 'Modelo')

    def test_cotizacion_salud_es_7_por_ciento(self):
        record = self._liquidar()
        # 660000 * 7% = 46200
        self.assertEqual(record.health_amount, Decimal('46200'))

    def test_liquido_descuenta_afp_y_salud(self):
        record = self._liquidar()
        # 660000 - 69828 - 46200 = 543972
        self.assertEqual(record.net_pay, Decimal('543972'))

    def test_horas_extras_del_periodo_suman_al_imponible(self):
        OvertimeRecord.objects.create(
            worker=self.worker, date=date(2026, 8, 10), hours=Decimal('4'),
        )
        record = self._liquidar()
        self.assertEqual(record.overtime_total, Decimal('21000'))
        self.assertEqual(record.taxable_income, Decimal('681000'))

    def test_horas_extras_de_otro_mes_no_se_incluyen(self):
        OvertimeRecord.objects.create(
            worker=self.worker, date=date(2026, 7, 15), hours=Decimal('10'),
        )
        record = self._liquidar(period=date(2026, 8, 1))
        self.assertEqual(record.overtime_total, Decimal('0'))

    def test_bono_suma_al_imponible(self):
        PayrollAdjustment.objects.create(
            worker=self.worker, adjustment_type='bono',
            amount=Decimal('50000'), period=date(2026, 8, 1),
        )
        record = self._liquidar()
        self.assertEqual(record.bonuses_total, Decimal('50000'))
        self.assertEqual(record.taxable_income, Decimal('710000'))

    def test_anticipo_descuenta_del_liquido_sin_afectar_imponible(self):
        PayrollAdjustment.objects.create(
            worker=self.worker, adjustment_type='anticipo',
            amount=Decimal('100000'), period=date(2026, 8, 1),
        )
        record = self._liquidar()
        self.assertEqual(record.taxable_income, Decimal('660000'))  # no cambia
        self.assertEqual(record.advances_total, Decimal('100000'))
        self.assertEqual(record.net_pay, Decimal('443972'))  # 543972 - 100000

    def test_descuento_reduce_el_liquido(self):
        PayrollAdjustment.objects.create(
            worker=self.worker, adjustment_type='descuento',
            amount=Decimal('20000'), period=date(2026, 8, 1),
        )
        record = self._liquidar()
        self.assertEqual(record.net_pay, Decimal('523972'))  # 543972 - 20000

    def test_periodo_se_normaliza_al_dia_uno(self):
        record = PayrollRecord(worker=self.worker, period=date(2026, 8, 25))
        record.calculate()
        record.save()
        self.assertEqual(record.period, date(2026, 8, 1))

    def test_no_permite_dos_liquidaciones_del_mismo_periodo(self):
        from django.db.utils import IntegrityError
        self._liquidar()
        with self.assertRaises(IntegrityError):
            PayrollRecord.objects.create(
                worker=self.worker, period=date(2026, 8, 1),
                base_salary=Decimal('660000'), taxable_income=Decimal('660000'),
                afp_name='Modelo', afp_percentage=Decimal('10.58'),
                afp_amount=Decimal('0'), health_amount=Decimal('0'),
                net_pay=Decimal('0'),
            )
