"""Vistas públicas de la galería.

La home (studio:inicio) solo muestra las últimas 6 obras como adelanto — acá
vive la galería COMPLETA, con filtro por estilo y por artista (antes el botón
"Ver toda la galería" de la home no llevaba a ningún lado)."""

from django.views.generic import ListView

from apps.artists.models import Empleado

from .models import Estilo, Obra


class GaleriaView(ListView):
    model = Obra
    template_name = "gallery/galeria.html"
    context_object_name = "obras"
    paginate_by = 24

    def get_queryset(self):
        qs = Obra.objects.select_related("artista__usuario", "estilo")
        estilo_id = self.request.GET.get("estilo", "")
        artista_id = self.request.GET.get("artista", "")
        # .isdigit() antes de filtrar: un ?estilo=algo-raro en la URL no debe
        # tirar un 500 (ValueError de Django al castear a int), solo se ignora.
        if estilo_id.isdigit():
            qs = qs.filter(estilo_id=estilo_id)
        if artista_id.isdigit():
            qs = qs.filter(artista_id=artista_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["estilos"] = Estilo.objects.all()
        context["artistas"] = Empleado.objects.filter(es_artista=True, activo=True).select_related("usuario")
        context["estilo_seleccionado"] = self.request.GET.get("estilo", "")
        context["artista_seleccionado"] = self.request.GET.get("artista", "")
        return context
