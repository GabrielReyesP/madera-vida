"""
apps/accounts/models.py
CustomUser (login por email), WorkerProfile y CustomerProfile
para Madera & Vida. Alineado a la documentación v1.0 (secciones 4 y 7).
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import CustomUserManager
from .validators import validate_minimum_wage, validate_rut


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Usuario base del sistema. Login por EMAIL (no username), como
    especifica RF-13 y la seccion 5/10 de la documentacion.
    """

    class UserType(models.TextChoices):
        CUSTOMER = 'customer', 'Cliente'
        WORKER = 'worker', 'Trabajador'

    email = models.EmailField('Correo electronico', unique=True)
    first_name = models.CharField('Nombre', max_length=100)
    last_name = models.CharField('Apellido', max_length=100)
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.CUSTOMER,
        verbose_name='Tipo de usuario',
    )
    is_active = models.BooleanField('Activo', default=True)
    is_staff = models.BooleanField('Acceso al admin', default=False)
    date_joined = models.DateTimeField('Fecha de registro', default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.get_full_name() or self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    @property
    def is_worker(self):
        return self.user_type == self.UserType.WORKER

    @property
    def is_customer(self):
        return self.user_type == self.UserType.CUSTOMER


class WorkerProfile(models.Model):
    """
    Perfil de trabajador. El campo 'role' define el nivel de acceso
    segun la matriz de permisos de la seccion 4.2 del documento.
    """

    class Role(models.TextChoices):
        JEFATURA = 'jefatura', 'Jefatura'
        ADMINISTRACION = 'administracion', 'Administracion'
        RRHH = 'rrhh', 'Recursos Humanos'
        VENTA = 'venta', 'Venta'

    class ContractType(models.TextChoices):
        INDEFINIDO = 'indefinido', 'Indefinido'
        PLAZO_FIJO = 'plazo_fijo', 'Plazo fijo'
        POR_OBRA = 'por_obra', 'Por obra o faena'

    class HealthSystem(models.TextChoices):
        FONASA = 'fonasa', 'Fonasa'
        ISAPRE = 'isapre', 'Isapre'

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='worker_profile',
        verbose_name='Usuario',
    )
    rut = models.CharField(
        'RUT', max_length=12, unique=True, validators=[validate_rut],
    )
    role = models.CharField('Rol', max_length=20, choices=Role.choices)
    afp = models.CharField('AFP', max_length=100, blank=True)
    health_system = models.CharField(
        'Sistema de salud', max_length=10,
        choices=HealthSystem.choices, default=HealthSystem.FONASA,
    )
    contract_type = models.CharField(
        'Tipo de contrato', max_length=20,
        choices=ContractType.choices, default=ContractType.INDEFINIDO,
    )
    base_salary = models.DecimalField(
        'Sueldo base (CLP)', max_digits=10, decimal_places=0,
        validators=[validate_minimum_wage],
    )
    hire_date = models.DateField('Fecha de contratacion', null=True, blank=True)

    class Meta:
        verbose_name = 'Perfil de trabajador'
        verbose_name_plural = 'Perfiles de trabajadores'

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"

    # --- Helpers de permisos, alineados a la matriz de la seccion 4.2 ---

    @property
    def is_superior(self):
        """Jefatura y Administracion: mismo nivel, acceso completo."""
        return self.role in (self.Role.JEFATURA, self.Role.ADMINISTRACION)

    @property
    def is_rrhh(self):
        return self.role == self.Role.RRHH

    @property
    def is_venta(self):
        return self.role == self.Role.VENTA

    @property
    def can_manage_catalog(self):
        """Modificar stock y precios (RF-15): solo nivel superior."""
        return self.is_superior

    @property
    def can_manage_hr(self):
        """Modulo RRHH: nivel superior + RRHH."""
        return self.is_superior or self.is_rrhh

    @property
    def can_manage_orders(self):
        """Gestionar pedidos/retiros: nivel superior + Venta."""
        return self.is_superior or self.is_venta


class CustomerProfile(models.Model):
    """Perfil de cliente/comprador."""

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='customer_profile',
        verbose_name='Usuario',
    )
    rut = models.CharField(
        'RUT', max_length=12, blank=True, validators=[validate_rut],
    )
    phone = models.CharField('Telefono', max_length=20, blank=True)
    address = models.CharField('Direccion', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Perfil de cliente'
        verbose_name_plural = 'Perfiles de clientes'

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.user.email}"
