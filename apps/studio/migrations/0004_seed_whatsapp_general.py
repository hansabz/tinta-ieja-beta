from django.db import migrations


def cargar_whatsapp(apps, schema_editor):
    ConfiguracionEstudio = apps.get_model("studio", "ConfiguracionEstudio")
    ConfiguracionEstudio.objects.filter(pk=1).update(whatsapp_general="5491100000000")


def quitar_whatsapp(apps, schema_editor):
    ConfiguracionEstudio = apps.get_model("studio", "ConfiguracionEstudio")
    ConfiguracionEstudio.objects.filter(pk=1).update(whatsapp_general="")


class Migration(migrations.Migration):
    dependencies = [("studio", "0003_configuracionestudio_whatsapp_general")]
    operations = [migrations.RunPython(cargar_whatsapp, quitar_whatsapp)]
