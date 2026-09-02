from django.conf import settings
from django.db import models


class EncuestaDiseno(models.Model):
    """Respuestas de la encuesta guiada. Cada campo acepta 'no_se' como valor válido."""

    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="encuestas")
    estilo = models.CharField(max_length=80, default="no_se")
    colores = models.CharField(max_length=120, default="no_se")
    tamano = models.CharField(max_length=40, default="no_se")
    posicion_cuerpo = models.CharField(max_length=80, default="no_se")
    tematica = models.TextField(blank=True)
    elementos_adicionales = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"Encuesta de {self.cliente} ({self.fecha:%d/%m/%Y})"


class ReferenciaImagen(models.Model):
    """Carpeta de referencias visuales del cliente. Solo el propio cliente y su
    artista_asignado pueden verla (ver apps.design_assist.views)."""

    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="referencias")
    encuesta = models.ForeignKey(EncuestaDiseno, on_delete=models.SET_NULL, null=True, blank=True, related_name="referencias")
    url_imagen = models.URLField()
    fuente = models.CharField(max_length=255, blank=True)
    aprobada_por_cliente = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]
        indexes = [models.Index(fields=["cliente"])]

    def __str__(self):
        return f"Referencia de {self.cliente} ({self.fecha:%d/%m/%Y})"
