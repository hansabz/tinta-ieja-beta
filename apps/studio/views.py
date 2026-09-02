from django.views.generic import TemplateView

from apps.artists.models import Empleado
from apps.gallery.models import Estilo, Obra


class InicioView(TemplateView):
    template_name = "studio/inicio.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["estilos"] = Estilo.objects.all()
        context["obras"] = (
            Obra.objects.select_related("artista__usuario", "estilo").order_by("-fecha")[:6]
        )
        context["artistas"] = (
            Empleado.objects.filter(es_artista=True, activo=True).select_related("usuario")
        )
        return context
