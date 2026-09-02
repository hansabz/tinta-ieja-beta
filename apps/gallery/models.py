"""App "gallery": el catálogo/portafolio del estudio.

Estilo y Etiqueta son tablas de catálogo simples (se cargan y editan desde el
panel admin). Obra es cada trabajo real subido a la galería pública — la foto se
sube acá (campo `imagen`) y automáticamente queda accesible en /media/obras/…
"""

from django.db import models


class Estilo(models.Model):
    """Ej: "Blackwork", "Old School". Aparece en la sección "Estilos que trabajamos"
    de la home y como filtro/etiqueta en cada Obra."""

    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Etiqueta(models.Model):
    """Etiquetas libres para las obras (además del Estilo), ej: "color", "cover-up"."""

    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Obra(models.Model):
    """Un trabajo del portafolio. Se crea/edita desde el panel admin
    (/admin/gallery/obra/) — ahí es donde se sube la foto real."""

    artista = models.ForeignKey("artists.Empleado", on_delete=models.CASCADE, related_name="obras")
    estilo = models.ForeignKey(Estilo, on_delete=models.PROTECT, related_name="obras")
    etiquetas = models.ManyToManyField(Etiqueta, blank=True, related_name="obras")
    titulo = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to="obras/")  # ver MEDIA_ROOT/MEDIA_URL en settings.py
    zona_cuerpo = models.CharField(max_length=60, blank=True)
    fecha = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["estilo"]),
            models.Index(fields=["artista"]),
        ]

    def __str__(self):
        return self.titulo
