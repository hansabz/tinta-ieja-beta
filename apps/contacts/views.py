from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from .forms import SolicitudContactoForm
from .models import SolicitudContacto


@require_POST
@ratelimit(key="ip", rate="5/m", method="POST", block=True)
def crear_solicitud(request):
    autenticado = request.user.is_authenticated
    form = SolicitudContactoForm(request.POST, usuario_autenticado=autenticado)

    if not form.is_valid():
        for errores in form.errors.values():
            for error in errores:
                messages.error(request, error)
        return redirect("studio:inicio")

    solicitud = SolicitudContacto(motivo=form.cleaned_data["motivo"])
    if autenticado:
        solicitud.cliente = request.user
    else:
        solicitud.nombre_contacto = form.cleaned_data["nombre_contacto"]
        solicitud.contacto = form.cleaned_data["contacto"]

    cliente_perfil = getattr(request.user, "cliente", None) if autenticado else None
    if cliente_perfil and cliente_perfil.artista_asignado_id:
        solicitud.empleado = cliente_perfil.artista_asignado

    solicitud.full_clean()
    solicitud.save()

    messages.success(request, "¡Gracias! Recibimos tu mensaje y te vamos a contactar pronto.")
    return redirect("studio:inicio")
