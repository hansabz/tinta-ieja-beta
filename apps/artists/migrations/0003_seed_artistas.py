from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import migrations

# Datos de ejemplo para la beta — nombres ficticios, se reemplazan por el equipo real
# del estudio desde el panel administrativo antes de cualquier lanzamiento real.
ARTISTAS = [
    {
        "username": "mora.ibanez",
        "first_name": "Mora",
        "last_name": "Ibáñez",
        "especialidades": "Blackwork · Geométrico",
        "biografia": "Cada línea tiene que sostenerse sola, sin sombra que la salve.",
    },
    {
        "username": "facu.rearte",
        "first_name": "Facu",
        "last_name": "Rearte",
        "especialidades": "Old School · Fineline",
        "biografia": "El flash tradicional envejece bien porque nunca quiso ser perfecto.",
    },
    {
        "username": "kenji.suzuki",
        "first_name": "Kenji",
        "last_name": "Suzuki",
        "especialidades": "Irezumi · Realismo",
        "biografia": "Un tatuaje japonés se lee de lejos y se respeta de cerca.",
    },
]


def crear_artistas(apps, schema_editor):
    Usuario = apps.get_model("users", "Usuario")
    Empleado = apps.get_model("artists", "Empleado")
    for datos in ARTISTAS:
        usuario, creado = Usuario.objects.get_or_create(
            username=datos["username"],
            defaults={
                "first_name": datos["first_name"],
                "last_name": datos["last_name"],
                "rol": "EMPLEADO",
                "is_staff": False,
                "is_active": True,
            },
        )
        if creado:
            usuario.password = make_password(None)  # cuenta sin contraseña utilizable
            usuario.save()
        Empleado.objects.get_or_create(
            usuario=usuario,
            defaults={
                "especialidades": datos["especialidades"],
                "biografia": datos["biografia"],
                "es_artista": True,
                "activo": True,
            },
        )


def eliminar_artistas(apps, schema_editor):
    Usuario = apps.get_model("users", "Usuario")
    Usuario.objects.filter(username__in=[a["username"] for a in ARTISTAS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("artists", "0002_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [migrations.RunPython(crear_artistas, eliminar_artistas)]
