"""Comando manual/cron para la limpieza del historial de citas.

No hace falta correrlo a mano para que el sistema funcione — las vistas de
citas (apps/appointments/views.py) ya llaman a la misma limpieza cada vez que
alguien entra a "Mis citas", así que el borrado automático pasa solo aunque
Render no tenga un cron job configurado (el free tier no lo incluye). Este
comando sirve para: (a) forzar la limpieza ahora mismo, o (b) si en el futuro
se agrega un cron job real, ejecutarla de forma más puntual.

Uso: python manage.py limpiar_historial_citas
"""

from django.core.management.base import BaseCommand

from apps.appointments.services import limpiar_historial_vencido


class Command(BaseCommand):
    help = "Borra las citas terminadas cuyo mes de retención en el historial ya venció."

    def handle(self, *args, **options):
        total = limpiar_historial_vencido()
        self.stdout.write(self.style.SUCCESS(f"Se borraron {total} cita(s) del historial."))
