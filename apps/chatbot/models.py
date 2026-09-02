"""App "chatbot": guarda el historial de conversaciones con el asistente de IA.
La lógica de la IA en sí (prompt, herramientas, proveedores) vive en services/ai/ —
acá solo están los modelos de datos y (en views.py) el endpoint que las conecta."""

from django.conf import settings
from django.db import models


class Conversacion(models.Model):
    """El chat es para cualquier visitante, no solo clientes registrados. Si hay
    sesión iniciada, se vincula a `cliente`; si no, se identifica por `session_key`
    (la clave de sesión de Django, anónima) para poder seguir el hilo sin cuenta."""

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="conversaciones",
    )
    session_key = models.CharField(max_length=40, blank=True, db_index=True)
    iniciada = models.DateTimeField(auto_now_add=True)
    actualizada = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-actualizada"]

    def __str__(self):
        quien = self.cliente or f"anónimo:{self.session_key[:8]}"
        return f"Conversación #{self.pk} — {quien}"


class Emisor(models.TextChoices):
    CLIENTE = "CLIENTE", "Cliente"
    BOT = "BOT", "Asistente"


class Mensaje(models.Model):
    conversacion = models.ForeignKey(Conversacion, on_delete=models.CASCADE, related_name="mensajes")
    emisor = models.CharField(max_length=10, choices=Emisor.choices)
    texto = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fecha"]

    def __str__(self):
        return f"[{self.emisor}] {self.texto[:40]}"
