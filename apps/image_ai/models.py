from django.conf import settings
from django.db import models


class DisenoIA(models.Model):
    """Generación real por IA (Replicate). Solo se usa si
    ConfiguracionEstudio.generacion_ia_habilitada está activo."""

    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="disenos_ia")
    prompt = models.TextField()
    imagen_url = models.URLField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"Diseño IA de {self.cliente} ({self.fecha:%d/%m/%Y})"


class SimulacionTatuaje(models.Model):
    diseno = models.ForeignKey(DisenoIA, on_delete=models.CASCADE, related_name="simulaciones")
    foto_usuario_url = models.URLField()
    resultado_url = models.URLField(blank=True)
    zona_cuerpo = models.CharField(max_length=60, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"Simulación #{self.pk}"
