#!/usr/bin/env python
"""Utilidad de línea de comandos de Django para Madera & Vida."""

import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "¿No tienes Django instalado? Asegúrate de activar el entorno "
            "virtual y ejecutar: pip install -r requirements/base.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()