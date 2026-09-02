from django.db import models


class ConfiguracionEstudio(models.Model):
    """Tabla singleton: una sola fila, editable desde el panel admin. El chatbot la consulta
    para responder con información real del estudio (nunca inventada)."""

    nombre = models.CharField(max_length=120, default="Tinta Vieja")
    descripcion = models.TextField(blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    horarios = models.CharField(max_length=255, blank=True)
    telefono = models.CharField(max_length=50, blank=True)
    whatsapp_general = models.CharField(
        max_length=30,
        blank=True,
        help_text="Número con código de país, solo dígitos. Ej: 5491122334455. "
        "El chatbot lo ofrece cuando piden hablar con alguien y no hay un artista específico.",
    )
    correo = models.EmailField(blank=True)
    redes_sociales = models.JSONField(blank=True, default=dict)
    politicas = models.TextField(blank=True)
    cuidados = models.TextField(blank=True)
    mensaje_transferencia_ia = models.TextField(
        default="Claro, para ofrecerte un mejor servicio se te contactará con {artista}. Agradecemos tu paciencia."
    )
    generacion_ia_habilitada = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Configuración del estudio"
        verbose_name_plural = "Configuración del estudio"

    def save(self, *args, **kwargs):
        self.pk = 1  # fuerza singleton
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # nunca se borra

    @classmethod
    def obtener(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.nombre
