from .models import ConfiguracionEstudio


def configuracion_estudio(request):
    """Disponible como {{ estudio }} en todos los templates."""
    return {"estudio": ConfiguracionEstudio.obtener()}
