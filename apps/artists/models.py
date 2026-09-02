from django.conf import settings
from django.db import models


class Empleado(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="empleado")
    biografia = models.TextField(blank=True)
    es_artista = models.BooleanField(default=True)
    especialidades = models.CharField(max_length=255, blank=True, help_text="Ej: Blackwork, Old School")
    foto_url = models.URLField(blank=True)
    activo = models.BooleanField(default=True)
    whatsapp = models.CharField(
        max_length=30,
        blank=True,
        help_text="Número con código de país, solo dígitos. Ej: 5491122334455. "
        "Si se deja vacío, el chatbot ofrece el WhatsApp general del estudio en su lugar.",
    )

    def __str__(self):
        return str(self.usuario)
