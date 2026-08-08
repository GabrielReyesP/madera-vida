"""
apps/accounts/tests.py
Tests de validadores (RUT modulo 11, sueldo minimo) y permisos por rol.
"""

from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.core.models import MinimumWageConfig

from .models import CustomUser, WorkerProfile
from .validators import validate_minimum_wage, validate_rut


class ValidateRutTests(TestCase):
    """RL-02: digito verificador modulo 11."""

    def test_acepta_ruts_validos_en_distintos_formatos(self):
        for rut in ['12.345.678-5', '12345678-5', '123456785', '11.111.111-1']:
            with self.subTest(rut=rut):
                validate_rut(rut)  # no debe lanzar

    def test_acepta_digito_verificador_k(self):
        # 20.347.878-K es un RUT con DV = K
        validate_rut('20.347.878-K')

    def test_rechaza_digito_verificador_incorrecto(self):
        with self.assertRaises(ValidationError):
            validate_rut('12.345.678-9')

    def test_rechaza_cuerpo_no_numerico(self):
        with self.assertRaises(ValidationError):
            validate_rut('abcdefg-5')

    def test_rechaza_rut_incompleto(self):
        with self.assertRaises(ValidationError):
            validate_rut('5')


class ValidateMinimumWageTests(TestCase):
    """RL-03 / RF-22: no permitir sueldos bajo el minimo vigente."""

    def setUp(self):
        MinimumWageConfig.objects.create(value=Decimal('500000'), effective_date=date(2020, 1, 1))

    def test_acepta_sueldo_igual_al_minimo(self):
        validate_minimum_wage(Decimal('500000'))

    def test_acepta_sueldo_sobre_el_minimo(self):
        validate_minimum_wage(Decimal('750000'))

    def test_rechaza_sueldo_bajo_el_minimo(self):
        with self.assertRaises(ValidationError):
            validate_minimum_wage(Decimal('499999'))

    def test_usa_la_configuracion_mas_reciente_vigente(self):
        MinimumWageConfig.objects.create(value=Decimal('600000'), effective_date=date(2021, 1, 1))
        with self.assertRaises(ValidationError):
            validate_minimum_wage(Decimal('550000'))


class RolePermissionTests(TestCase):
    """Seccion 4.2: matriz de permisos por rol."""

    @classmethod
    def setUpTestData(cls):
        MinimumWageConfig.objects.create(value=Decimal('500000'), effective_date=date(2020, 1, 1))
        cls.profiles = {}
        # RUTs con digito verificador valido (verificados con modulo 11).
        roles_ruts = [
            ('jefatura', '11.111.111-1'),
            ('administracion', '11.111.110-3'),
            ('rrhh', '11.111.112-K'),
            ('venta', '11.111.113-8'),
        ]
        for role, rut in roles_ruts:
            user = CustomUser.objects.create_user(
                email=f'{role}@test.cl', password='Test1234',
                first_name=role.capitalize(), last_name='Test', user_type='worker',
            )
            cls.profiles[role] = WorkerProfile.objects.create(
                user=user, rut=rut, role=role, base_salary=Decimal('700000'),
            )

    def test_jefatura_y_administracion_son_nivel_superior(self):
        self.assertTrue(self.profiles['jefatura'].is_superior)
        self.assertTrue(self.profiles['administracion'].is_superior)
        self.assertFalse(self.profiles['rrhh'].is_superior)
        self.assertFalse(self.profiles['venta'].is_superior)

    def test_solo_nivel_superior_gestiona_catalogo(self):
        # RF-15: modificar stock y precios
        self.assertTrue(self.profiles['jefatura'].can_manage_catalog)
        self.assertTrue(self.profiles['administracion'].can_manage_catalog)
        self.assertFalse(self.profiles['rrhh'].can_manage_catalog)
        self.assertFalse(self.profiles['venta'].can_manage_catalog)

    def test_rrhh_y_superior_gestionan_recursos_humanos(self):
        # RF-27
        self.assertTrue(self.profiles['jefatura'].can_manage_hr)
        self.assertTrue(self.profiles['rrhh'].can_manage_hr)
        self.assertFalse(self.profiles['venta'].can_manage_hr)

    def test_venta_y_superior_gestionan_pedidos(self):
        # RF-18
        self.assertTrue(self.profiles['jefatura'].can_manage_orders)
        self.assertTrue(self.profiles['venta'].can_manage_orders)
        self.assertFalse(self.profiles['rrhh'].can_manage_orders)


class CustomUserTests(TestCase):
    """RF-13: login por email, sin username."""

    def test_crear_usuario_usa_email_como_identificador(self):
        user = CustomUser.objects.create_user(
            email='cliente@test.cl', password='Test1234',
            first_name='Ana', last_name='Perez',
        )
        self.assertEqual(user.get_username(), 'cliente@test.cl')
        self.assertTrue(user.is_customer)
        self.assertFalse(user.is_worker)

    def test_crear_usuario_sin_email_falla(self):
        with self.assertRaises(ValueError):
            CustomUser.objects.create_user(email='', password='Test1234')

    def test_superusuario_tiene_permisos_de_staff(self):
        admin = CustomUser.objects.create_superuser(
            email='admin@test.cl', password='Test1234',
            first_name='Admin', last_name='Root',
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
