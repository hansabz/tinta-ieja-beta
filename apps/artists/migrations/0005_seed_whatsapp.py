from django.db import migrations

# Números de ejemplo (mismo criterio que el resto de los datos de la beta:
# claramente ficticios, se reemplazan por los reales del estudio antes de lanzar).
WHATSAPP_POR_USUARIO = {
    "mora.ibanez": "5491122334401",
    "facu.rearte": "5491122334402",
    "kenji.suzuki": "5491122334403",
}


def cargar_whatsapp(apps, schema_editor):
    Usuario = apps.get_model("users", "Usuario")
    Empleado = apps.get_model("artists", "Empleado")
    for username, numero in WHATSAPP_POR_USUARIO.items():
        try:
            usuario = Usuario.objects.get(username=username)
        except Usuario.DoesNotExist:
            continue
        Empleado.objects.filter(usuario=usuario).update(whatsapp=numero)


def quitar_whatsapp(apps, schema_editor):
    Usuario = apps.get_model("users", "Usuario")
    Empleado = apps.get_model("artists", "Empleado")
    Empleado.objects.filter(usuario__username__in=WHATSAPP_POR_USUARIO.keys()).update(whatsapp="")


class Migration(migrations.Migration):
    dependencies = [("artists", "0004_empleado_whatsapp")]
    operations = [migrations.RunPython(cargar_whatsapp, quitar_whatsapp)]
