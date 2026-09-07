from django.apps import AppConfig


class AppointmentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.appointments"
    verbose_name = "Citas"

    def ready(self):
        # Conecta las señales que borran el archivo de la foto de resultado
        # cuando se borra una Cita (Django no lo hace solo, ver models.py).
        from . import signals  # noqa: F401
