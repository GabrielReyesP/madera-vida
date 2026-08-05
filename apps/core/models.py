"""
apps/core/models.py
CompanyInfo: datos de la empresa para el sitio publico (RF-01).
Tabla 'singleton': siempre existe un unico registro (pk=1).
"""

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
