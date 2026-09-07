"""App "appointments": el sistema de citas/turnos del estudio.

Una Cita agrupa toda la reserva de un cliente (con qué tatuador, cuántas
sesiones, costo total) y cada sesión individual (fecha/hora concreta en el
calendario) vive en SesionCita — así un tatuaje que se hace en 4 encuentros
tiene 1 Cita con 4 SesionCita, cada una con su propio horario, sin pisarse con
otras citas del mismo tatuador (ver services.py, donde están las reglas de
choque de horario, tope mensual y "días muy largos").

Los números que rigen esas reglas (máximo de sesiones, tope mensual por
tatuador, etc.) NO están escritos acá — se leen de
apps.studio.models.ConfiguracionEstudio, para que el gerente los pueda ajustar
desde /admin sin tocar código.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class EstadoCita(models.TextChoices):
    PENDIENTE = "PENDIENTE", "Pendiente"
    TERMINADA = "TERMINADA", "Terminada"
    CANCELADA = "CANCELADA", "Cancelada"


class EstadoSesion(models.TextChoices):
    PENDIENTE = "PENDIENTE", "Pendiente"
    REALIZADA = "REALIZADA", "Realizada"
    CANCELADA = "CANCELADA", "Cancelada"


class Cita(models.Model):
    """La reserva completa. `tatuador` puede quedar vacío si el cliente no eligió
    a nadie en particular — en ese caso el aviso de la reserva va al WhatsApp
    general del estudio (el gerente) en vez de a un tatuador puntual."""

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="citas"
    )
    tatuador = models.ForeignKey(
        "artists.Empleado", on_delete=models.SET_NULL, null=True, blank=True, related_name="citas"
    )
    estilo = models.ForeignKey(
        "gallery.Estilo", on_delete=models.PROTECT, null=True, blank=True, related_name="citas"
    )
    numero_sesiones = models.PositiveSmallIntegerField(
        default=1, help_text="Cuántos encuentros necesita este tatuaje (tope fijado por el gerente)."
    )
    costo = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Se completa cuando el estudio cotiza el trabajo — puede quedar vacío al reservar.",
    )
    estado = models.CharField(max_length=20, choices=EstadoCita.choices, default=EstadoCita.PENDIENTE)
    notas = models.TextField(blank=True)
    creada = models.DateTimeField(auto_now_add=True)
    fecha_finalizada = models.DateTimeField(
        null=True, blank=True,
        help_text="Se completa sola al marcar la cita como terminada. A partir de acá se "
        "cuenta el mes que queda en el historial antes del borrado automático.",
    )

    # --- Resultado final (foto que sube el tatuador al terminar) -----------
    foto_resultado = models.ImageField(upload_to="citas_resultados/", blank=True, null=True)
    resultado_publicado_portafolio = models.BooleanField(
        default=False,
        help_text="Si el tatuador decidió publicar la foto en su portafolio público, queda "
        "una copia en Obra (apps.gallery) y esta marca evita duplicarla.",
    )
    obra_publicada = models.ForeignKey(
        "gallery.Obra", on_delete=models.SET_NULL, null=True, blank=True, related_name="cita_origen"
    )

    class Meta:
        ordering = ["-creada"]
        verbose_name = "Cita"
        verbose_name_plural = "Citas"
        indexes = [
            models.Index(fields=["estado"]),
            models.Index(fields=["tatuador"]),
            models.Index(fields=["fecha_finalizada"]),
        ]

    def __str__(self):
        return f"{self.cliente} — {self.get_estado_display()}"

    @property
    def proxima_sesion(self):
        return self.sesiones.filter(estado=EstadoSesion.PENDIENTE).order_by("inicio").first()

    @property
    def duracion_total_minutos(self):
        return sum(self.sesiones.values_list("duracion_minutos", flat=True))

    def vencida_para_historial(self, dias_retencion):
        return bool(
            self.estado == EstadoCita.TERMINADA
            and self.fecha_finalizada
            and self.fecha_finalizada <= timezone.now() - timezone.timedelta(days=dias_retencion)
        )


class SesionCita(models.Model):
    """Un encuentro puntual dentro de una Cita — la unidad real que ocupa un
    horario en el calendario del tatuador."""

    cita = models.ForeignKey(Cita, on_delete=models.CASCADE, related_name="sesiones")
    numero = models.PositiveSmallIntegerField(help_text="1ra, 2da, 3ra sesión... de esta cita.")
    inicio = models.DateTimeField()
    duracion_minutos = models.PositiveSmallIntegerField(default=240)
    estado = models.CharField(max_length=20, choices=EstadoSesion.choices, default=EstadoSesion.PENDIENTE)

    class Meta:
        ordering = ["numero"]
        verbose_name = "Sesión de cita"
        verbose_name_plural = "Sesiones de citas"
        constraints = [
            models.UniqueConstraint(fields=["cita", "numero"], name="sesion_numero_unico_por_cita")
        ]
        indexes = [
            models.Index(fields=["inicio"]),
            models.Index(fields=["estado"]),
        ]

    @property
    def fin(self):
        return self.inicio + timezone.timedelta(minutes=self.duracion_minutos)

    def __str__(self):
        return f"Sesión {self.numero} — {self.cita.cliente} — {self.inicio:%d/%m/%Y %H:%M}"
