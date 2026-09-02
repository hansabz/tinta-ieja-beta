from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class EstadoSolicitud(models.TextChoices):
    PENDIENTE = "PENDIENTE", "Pendiente"
    EN_PROCESO = "EN_PROCESO", "En proceso"
    RESUELTA = "RESUELTA", "Resuelta"


class SolicitudContacto(models.Model):
    """Solicitud de contacto hacia el estudio. La puede crear un cliente logueado
    (queda vinculada a su cuenta) o un visitante anónimo desde el formulario público
    (queda identificada por nombre_contacto/contacto). Siempre hay una forma de
    identificar y responderle a quien la envió."""

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="solicitudes",
    )
    nombre_contacto = models.CharField(max_length=120, blank=True)
    contacto = models.CharField(max_length=120, blank=True, help_text="Email o teléfono")
    empleado = models.ForeignKey(
        "artists.Empleado",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitudes_recibidas",
    )
    motivo = models.TextField(max_length=1000)
    estado = models.CharField(max_length=20, choices=EstadoSolicitud.choices, default=EstadoSolicitud.PENDIENTE)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]
        indexes = [models.Index(fields=["estado"])]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cliente__isnull=False) | ~models.Q(nombre_contacto="") & ~models.Q(contacto=""),
                name="solicitud_tiene_identificacion",
            )
        ]

    def clean(self):
        if not self.cliente_id and not (self.nombre_contacto and self.contacto):
            raise ValidationError(
                "La solicitud necesita un cliente logueado, o nombre y contacto (email/teléfono)."
            )

    def __str__(self):
        quien = str(self.cliente) if self.cliente_id else self.nombre_contacto
        return f"{quien} — {self.motivo[:40]}"
