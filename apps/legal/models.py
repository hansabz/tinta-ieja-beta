from django.db import models


class DocumentoLegal(models.Model):
    """Los 4 documentos legales del sitio (privacidad, términos y condiciones,
    términos del servicio, cookies). Son un conjunto fijo — se crean una sola
    vez con una migración de datos (ver migrations/0002_seed_documentos.py) y
    desde /admin solo se puede editar el texto, nunca agregar ni borrar uno,
    igual que ConfiguracionEstudio (apps.studio.models)."""

    class Tipo(models.TextChoices):
        PRIVACIDAD = "privacidad", "Política de privacidad"
        TERMINOS_CONDICIONES = "terminos-y-condiciones", "Términos y condiciones de uso del sitio"
        TERMINOS_SERVICIO = "terminos-del-servicio", "Términos del servicio de tatuaje"
        COOKIES = "cookies", "Política de cookies"

    tipo = models.CharField(max_length=30, choices=Tipo.choices, unique=True)
    titulo = models.CharField(max_length=150)
    contenido = models.TextField(
        help_text="Separá cada párrafo con una línea en blanco — así se muestran en la página "
        "pública. Es un modelo estándar para la etapa beta: antes de un lanzamiento comercial "
        "real convenía que un profesional legal lo revise y lo adapte a tu país."
    )
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Documento legal"
        verbose_name_plural = "Documentos legales"
        ordering = ["tipo"]

    def __str__(self):
        return self.titulo
