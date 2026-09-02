from django.db import migrations

ESTILOS = [
    ("Blackwork", "Líneas sólidas, contraste fuerte, composiciones gráficas."),
    ("Japonés / Irezumi", "Dragones, olas y flores con la narrativa tradicional nipona."),
    ("Old School", "Golondrinas, rosas y dagas — el flash americano de siempre."),
    ("Realismo", "Retratos y escenas con sombreado fotográfico."),
    ("Fineline", "Trazo fino y minimalista, ideal para primeros tatuajes."),
    ("Geométrico", "Patrones y simetría con precisión matemática."),
]


def crear_estilos(apps, schema_editor):
    Estilo = apps.get_model("gallery", "Estilo")
    for nombre, descripcion in ESTILOS:
        Estilo.objects.get_or_create(nombre=nombre, defaults={"descripcion": descripcion})


def eliminar_estilos(apps, schema_editor):
    Estilo = apps.get_model("gallery", "Estilo")
    Estilo.objects.filter(nombre__in=[n for n, _ in ESTILOS]).delete()


class Migration(migrations.Migration):
    dependencies = [("gallery", "0001_initial")]
    operations = [migrations.RunPython(crear_estilos, eliminar_estilos)]
