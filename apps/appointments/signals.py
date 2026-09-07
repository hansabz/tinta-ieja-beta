"""Django no borra el archivo físico de un FileField/ImageField cuando se borra
la fila — hay que hacerlo a mano. Esto importa especialmente acá porque la
limpieza automática del historial (ver management/commands/limpiar_historial_citas.py)
borra citas viejas todo el tiempo; sin esto, las fotos de resultado se quedarían
ocupando espacio para siempre."""

from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Cita


@receiver(post_delete, sender=Cita)
def borrar_foto_resultado(sender, instance, **kwargs):
    archivo = instance.foto_resultado
    if archivo and archivo.name:
        archivo.storage.delete(archivo.name)
