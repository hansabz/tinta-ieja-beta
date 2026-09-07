"""Los usuarios EMPLEADO/ADMINISTRADOR necesitan is_staff=True para entrar a
/admin y gestionar sus citas (ver apps.appointments.admin). Los 3 artistas de
ejemplo de la beta (apps/artists/migrations/0003_seed_artistas.py) se crearon
antes de que existiera esta regla, así que se corrigen acá. De acá en más,
UsuarioAdmin.save_model (apps/users/admin.py) lo hace solo."""

from django.db import migrations


def marcar_staff(apps, schema_editor):
    Usuario = apps.get_model("users", "Usuario")
    Usuario.objects.filter(rol__in=["EMPLEADO", "ADMINISTRADOR"]).update(is_staff=True)


def revertir(apps, schema_editor):
    pass  # no vale la pena des-marcarlos; no rompe nada dejarlo


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
        ("artists", "0003_seed_artistas"),
    ]
    operations = [migrations.RunPython(marcar_staff, revertir)]
