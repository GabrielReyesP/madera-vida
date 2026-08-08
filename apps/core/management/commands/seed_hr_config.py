"""
apps/core/management/commands/seed_hr_config.py
Carga datos semilla de RRHH: AFPs chilenas y el sueldo minimo vigente
(Fase 5 checklist: "Modelos core: MinimumWageConfig, AfpConfig + datos semilla").

Uso:
    python manage.py seed_hr_config

Es idempotente: se puede correr varias veces sin duplicar datos.
"""

from datetime import date

from django.core.management.base import BaseCommand

from apps.core.models import AfpConfig, MinimumWageConfig


class Command(BaseCommand):
    help = 'Carga datos semilla de AFPs y sueldo minimo vigente.'

    def handle(self, *args, **options):
        # NOTA: estos porcentajes son valores de referencia y deben
        # verificarse/actualizarse contra las tasas vigentes publicadas
        # por la Superintendencia de Pensiones antes de usarse en un
        # calculo real de liquidaciones.
        afps = [
            ('Capital', '11.44'),
            ('Cuprum', '11.44'),
            ('Habitat', '11.27'),
            ('Modelo', '10.58'),
            ('PlanVital', '11.16'),
            ('ProVida', '11.45'),
            ('Uno', '10.49'),
        ]

        created_count = 0
        for name, percentage in afps:
            _, created = AfpConfig.objects.get_or_create(
                name=name, defaults={'percentage': percentage, 'is_active': True},
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'AFPs: {created_count} creadas, {len(afps) - created_count} ya existían.'
        ))

        _, wage_created = MinimumWageConfig.objects.get_or_create(
            effective_date=date(2026, 1, 1),
            defaults={'value': 539000},
        )
        if wage_created:
            self.stdout.write(self.style.SUCCESS('Sueldo mínimo: configuración inicial creada ($539.000).'))
        else:
            self.stdout.write('Sueldo mínimo: ya existía una configuración para esa fecha.')

        self.stdout.write(self.style.WARNING(
            'Recuerda: los porcentajes de AFP y el sueldo mínimo son valores de referencia. '
            'Verifícalos contra las cifras oficiales vigentes antes de usarlos en liquidaciones reales.'
        ))
