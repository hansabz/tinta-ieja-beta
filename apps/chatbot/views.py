import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from apps.contacts.models import SolicitudContacto
from apps.studio.models import ConfiguracionEstudio
from services.ai.chat_service import SinRespuestaDisponible, responder

from .models import Conversacion, Emisor, Mensaje


def _obtener_conversacion(request):
    if not request.session.session_key:
        request.session.create()

    if request.user.is_authenticated:
        conversacion = (
            Conversacion.objects.filter(cliente=request.user).order_by("-actualizada").first()
        )
        if conversacion is None:
            conversacion = Conversacion.objects.create(cliente=request.user)
        return conversacion

    session_key = request.session.session_key
    conversacion = (
        Conversacion.objects.filter(session_key=session_key, cliente__isnull=True)
        .order_by("-actualizada")
        .first()
    )
    if conversacion is None:
        conversacion = Conversacion.objects.create(session_key=session_key)
    return conversacion


def _historial_para_ia(conversacion):
    mapa = {Emisor.CLIENTE: "user", Emisor.BOT: "assistant"}
    return [
        {"role": mapa[m.emisor], "content": m.texto}
        for m in conversacion.mensajes.order_by("fecha")
    ]


def _mensaje_transferencia(conversacion, motivo):
    estudio = ConfiguracionEstudio.obtener()
    empleado = None
    nombre_articulo = "el equipo del estudio"

    if conversacion.cliente_id:
        perfil = getattr(conversacion.cliente, "cliente", None)
        if perfil and perfil.artista_asignado_id:
            empleado = perfil.artista_asignado
            nombre_articulo = empleado.usuario.get_full_name() or empleado.usuario.username

    solicitud = SolicitudContacto(motivo=motivo, empleado=empleado)
    if conversacion.cliente_id:
        solicitud.cliente = conversacion.cliente
    else:
        solicitud.nombre_contacto = "Visitante del chat (sin identificar)"
        solicitud.contacto = "sin datos — seguimiento manual"
    try:
        solicitud.full_clean()
        solicitud.save()
    except Exception:
        pass

    plantilla = estudio.mensaje_transferencia_ia or (
        "Para ofrecerte un mejor servicio se te contactará con {artista}. Agradecemos tu paciencia."
    )
    return plantilla.replace("{artista}", nombre_articulo)


@require_POST
@ratelimit(key="ip", rate="15/m", method="POST", block=True)
def enviar_mensaje(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        payload = request.POST

    mensaje_texto = (payload.get("mensaje") or "").strip()[:2000]
    if not mensaje_texto:
        return JsonResponse({"error": "mensaje_vacio"}, status=400)

    conversacion = _obtener_conversacion(request)
    historial = _historial_para_ia(conversacion)
    Mensaje.objects.create(conversacion=conversacion, emisor=Emisor.CLIENTE, texto=mensaje_texto)

    contexto = {"usuario": request.user}

    try:
        respuesta = responder(mensaje_texto, historial, contexto)
    except SinRespuestaDisponible:
        respuesta = _mensaje_transferencia(
            conversacion, motivo=f"El asistente no pudo responder: {mensaje_texto[:200]}"
        )

    Mensaje.objects.create(conversacion=conversacion, emisor=Emisor.BOT, texto=respuesta)
    conversacion.save(update_fields=["actualizada"])

    return JsonResponse({"respuesta": respuesta})
