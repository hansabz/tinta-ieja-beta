"""Reemplaza Empleado.foto_url (link externo) por Empleado.foto (imagen subida
directo desde la computadora, igual que Obra.imagen) — el gerente reportó que
pedir una URL era confuso y no daba opción de subir un archivo. Los valores
de foto_url que ya existieran (links externos) se pierden: no hay forma
automática de "descargar" esa URL a un archivo real, así que hay que volver
a subir la foto desde /admin una vez aplicada esta migración."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("artists", "0005_seed_whatsapp"),
    ]

    operations = [
        migrations.RemoveField(model_name="empleado", name="foto_url"),
        migrations.AddField(
            model_name="empleado",
            name="foto",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="artistas/",
                help_text="Foto de perfil pública — se sube directo desde tu computadora.",
            ),
        ),
    ]
