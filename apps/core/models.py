"""
apps/core/models.py
CompanyInfo: datos de la empresa para el sitio publico (RF-01).
AuditLog: registro de auditoria de acciones sensibles (RF-20, RL-07).
"""

from django.conf import settings
from django.db import models


class CompanyInfo(models.Model):
    name = models.CharField('Nombre', max_length=150, default='Madera & Vida')
    description = models.TextField('Descripcion')
    address = models.CharField('Direccion', max_length=255)
    schedule = models.CharField(
        'Horario de atencion', max_length=255,
        help_text='Ej: Lunes a Viernes 9:00 - 18:00, Sabado 9:00 - 13:00',
    )
    phone = models.CharField('Telefono', max_length=20, blank=True)
    email = models.EmailField('Correo de contacto', blank=True)
    hero_image = models.ImageField(
        'Foto principal', upload_to='company/', blank=True, null=True,
        help_text='Se muestra junto a la descripción en la página principal.',
    )

    class Meta:
        verbose_name = 'Informacion de la empresa'
        verbose_name_plural = 'Informacion de la empresa'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={
            'description': 'Empresa dedicada a la venta de productos de madera.',
            'address': 'Por definir',
            'schedule': 'Por definir',
        })
        return obj


class AuditLog(models.Model):
    """
    Registro de acciones sensibles del panel interno (RF-20): quien,
    que accion, sobre que entidad, y el cambio antes/despues cuando
    corresponde. Se escribe explicitamente desde las vistas que
    realizan la accion (no por señales genericas), para que el
    'antes/despues' sea exacto y no inferido.
    """

    class Action(models.TextChoices):
        PRODUCT_UPDATE = 'product_update', 'Producto modificado'
        PRODUCT_CREATE = 'product_create', 'Producto creado'
        PRODUCT_DEACTIVATE = 'product_deactivate', 'Producto desactivado'
        PRODUCT_ACTIVATE = 'product_activate', 'Producto activado'
        PRODUCT_DELETE = 'product_delete', 'Producto eliminado'
        ORDER_STATUS_CHANGE = 'order_status_change', 'Estado de pedido modificado'
        WORKER_PASSWORD_RESET = 'worker_password_reset', 'Contraseña de trabajador reseteada'
        WORKER_CREATE = 'worker_create', 'Trabajador creado'
        PAYROLL_GENERATED = 'payroll_generated', 'Liquidación de sueldo generada'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='audit_entries',
        verbose_name='Usuario que realizo la accion',
    )
    action = models.CharField('Accion', max_length=30, choices=Action.choices)
    entity = models.CharField('Entidad', max_length=100, help_text='Ej: Product, Order, CustomUser')
    entity_id = models.CharField('ID de la entidad', max_length=50, blank=True)
    before = models.JSONField('Antes', null=True, blank=True)
    after = models.JSONField('Despues', null=True, blank=True)
    ip_address = models.GenericIPAddressField('Direccion IP', null=True, blank=True)
    created_at = models.DateTimeField('Fecha', auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de auditoria'
        verbose_name_plural = 'Registros de auditoria'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_action_display()} · {self.entity} · {self.created_at:%d-%m-%Y %H:%M}'


class MinimumWageConfig(models.Model):
    """
    Sueldo minimo vigente, configurable por fecha (RL-03). Permite
    mantener el valor al dia sin tocar codigo cuando la ley cambie.
    """

    value = models.DecimalField('Sueldo mínimo (CLP)', max_digits=10, decimal_places=0)
    effective_date = models.DateField('Vigente desde')
    created_at = models.DateTimeField('Creado', auto_now_add=True)

    class Meta:
        verbose_name = 'Configuración de sueldo mínimo'
        verbose_name_plural = 'Configuraciones de sueldo mínimo'
        ordering = ['-effective_date']

    def __str__(self):
        return f'${self.value:,.0f} desde {self.effective_date:%d-%m-%Y}'.replace(',', '.')

    @classmethod
    def get_current(cls, on_date=None):
        """Devuelve el valor vigente a la fecha indicada (hoy por defecto)."""
        from decimal import Decimal

        from django.utils import timezone

        on_date = on_date or timezone.localdate()
        config = cls.objects.filter(effective_date__lte=on_date).order_by('-effective_date').first()
        if config:
            return config.value
        # Respaldo si aun no se ha cargado ninguna configuracion.
        return Decimal(str(settings.CHILEAN_CONSTANTS['MINIMUM_WAGE']))


class AfpConfig(models.Model):
    """
    Porcentaje total de cotizacion por AFP (10% obligatorio + comision
    variable de cada administradora), configurable sin tocar codigo (RL-06).
    """

    name = models.CharField('Nombre AFP', max_length=50, unique=True)
    percentage = models.DecimalField(
        'Porcentaje total (%)', max_digits=5, decimal_places=2,
        help_text='Incluye el 10% obligatorio más la comisión de la AFP.',
    )
    is_active = models.BooleanField('Activa', default=True)

    class Meta:
        verbose_name = 'Configuración AFP'
        verbose_name_plural = 'Configuraciones AFP'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.percentage}%)'
