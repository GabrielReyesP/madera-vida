"""
apps/accounts/models.py
Modelo de usuario personalizado para Madera & Vida.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Usuario personalizado. Extiende AbstractUser de Django
    (mantiene username, password, email, is_staff, is_superuser, etc.)
    y agrega un campo 'role' para diferenciar tipos de usuario.
    """

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        WORKER = 'worker', 'Trabajador'
        CUSTOMER = 'customer', 'Cliente'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        verbose_name='Rol',
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono',
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_worker(self):
        return self.role == self.Role.WORKER

    @property
    def is_customer(self):
        return self.role == self.Role.CUSTOMER


class WorkerProfile(models.Model):
    """
    Perfil extendido para usuarios con role='worker'.
    Aquí van los datos relevantes para RRHH (apps.hr).
    """

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='worker_profile',
        verbose_name='Usuario',
    )
    rut = models.CharField(max_length=12, unique=True, verbose_name='RUT')
    position = models.CharField(max_length=100, blank=True, verbose_name='Cargo')
    hire_date = models.DateField(null=True, blank=True, verbose_name='Fecha de contratación')
    base_salary = models.DecimalField(
        max_digits=10, decimal_places=0, null=True, blank=True,
        verbose_name='Sueldo base (CLP)',
    )

    class Meta:
        verbose_name = 'Perfil de trabajador'
        verbose_name_plural = 'Perfiles de trabajadores'

    def __str__(self):
        return f"{self.user} ({self.position or 'Sin cargo'})"


class CustomerProfile(models.Model):
    """
    Perfil extendido para usuarios con role='customer'.
    Aquí van los datos relevantes para la tienda (apps.store).
    """

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='customer_profile',
        verbose_name='Usuario',
    )
    rut = models.CharField(max_length=12, blank=True, verbose_name='RUT')
    address = models.CharField(max_length=255, blank=True, verbose_name='Dirección')
    region = models.CharField(max_length=100, blank=True, verbose_name='Región')

    class Meta:
        verbose_name = 'Perfil de cliente'
        verbose_name_plural = 'Perfiles de clientes'

    def __str__(self):
        return f"{self.user} - {self.address or 'Sin dirección'}"
