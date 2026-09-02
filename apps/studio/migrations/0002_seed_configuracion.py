from django.db import migrations


def crear_configuracion(apps, schema_editor):
    ConfiguracionEstudio = apps.get_model("studio", "ConfiguracionEstudio")
    ConfiguracionEstudio.objects.get_or_create(
        pk=1,
        defaults={
            "nombre": "Tinta Vieja",
            "descripcion": (
                "Contanos tu idea, armamos juntos las referencias visuales y un tatuador de "
                'carne y hueso la dibuja para vos. Sin promesas vacías de "diseño instantáneo por IA".'
            ),
            "direccion": "Av. San Martín 1248, Barrio Sur (dato de ejemplo)",
            "horarios": "Martes a sábado, 11:00–20:00",
            "telefono": "+54 9 11 0000-0000 (dato de ejemplo)",
        },
    )


def eliminar_configuracion(apps, schema_editor):
    ConfiguracionEstudio = apps.get_model("studio", "ConfiguracionEstudio")
    ConfiguracionEstudio.objects.filter(pk=1).delete()


class Migration(migrations.Migration):
    dependencies = [("studio", "0001_initial")]
    operations = [migrations.RunPython(crear_configuracion, eliminar_configuracion)]
