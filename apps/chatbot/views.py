"""Vista del chatbot: recibe un mensaje del widget de chat (ver templates/base.html,
la función JS `chatForm.addEventListener('submit', ...)`), lo guarda, se lo pasa al
orquestador de IA (services/ai/chat_service.py) y guarda + devuelve la respuesta.

No hay "magia" de IA acá — este archivo solo se encarga de la parte Django (sesión,
base de datos, límite de solicitudes). Toda la lógica de la IA en sí vive en
services/ai/.
"""

import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from apps.contacts.models import SolicitudContacto
from apps.studio.models import ConfiguracionEstudio
from services.ai.chat_service import SinRespuestaDisponible, responder

from .models import Conversacion, Emisor, Mensaje


def _obtener_conversacion(request):
    """Devuelve la conversación activa del usuario, creándola si hace falta.

    - Si el usuario tiene sesión iniciada, la conversación se busca/crea por su
      cuenta (`cliente`), así la sigue viendo aunque cambie de dispositivo... no,
      en realidad queda atada al navegador porque usamos la sesión de Django, pero
      si en el futuro hay login persistente esto ya está preparado para eso.
    - Si es un visitante anónimo, se usa la `session_key` de Django (una cookie
      anónima) para reconocer que es "la misma persona" mensaje a mensaje, sin
      pedirle que se registre.
    """
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
    """Convierte los Mensaje guardados en la base de datos al formato que espera
    la IA (role "user"/"assistant"), para que recuerde lo que se habló antes."""
    mapa = {Emisor.CLIENTE: "user", Emisor.BOT: "assistant"}
    return [
        {"role": mapa[m.emisor], "content": m.texto}
        for m in conversacion.mensajes.order_by("fecha")
    ]


def _mensaje_transferencia(conversacion, motivo):
    """Se dispara cuando NINGÚN proveedor de IA pudo responder (sin claves
    configuradas, o se acabó la cuota gratuita de todos). En vez de dejar al
    usuario sin respuesta, o peor, inventar una respuesta falsa:
      1. Crea una SolicitudContacto real para que el equipo la vea.
      2. Si el cliente ya tenía un artista asignado, se la dirige a esa persona.
      3. Devuelve el mensaje configurable de ConfiguracionEstudio.mensaje_transferencia_ia
         (el gerente lo puede editar desde el panel admin sin tocar código).
    """
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
        # Si por algún motivo no se pudo guardar la solicitud, igual le
        # respondemos algo razonable al usuario — no lo dejamos colgado.
        pass

    plantilla = estudio.mensaje_transferencia_ia or (
        "Para ofrecerte un mejor servicio se te contactará con {artista}. Agradecemos tu paciencia."
    )
    return plantilla.replace("{artista}", nombre_articulo)


@require_POST
@ratelimit(key="ip", rate="15/m", method="POST", block=True)
def enviar_mensaje(request):
    """Endpoint POST /chat/mensaje/ — llamado por fetch() desde el chat en pantalla.

    Flujo completo de una pregunta del usuario:
      1. Lee el mensaje del body (JSON).
      2. Busca/crea la conversación de esta persona y guarda su mensaje.
      3. Le pasa el mensaje + el historial + quién es (contexto) al orquestador de IA.
      4. Si la IA no pudo responder (sin clave, sin cuota), activa el mensaje de
         transferencia a un humano en vez de fallar.
      5. Guarda la respuesta del bot y se la devuelve al navegador como JSON.

    `@ratelimit(...)`: máximo 15 mensajes por minuto por IP — evita que una sola
    persona agote la cuota gratuita compartida de Groq/Gemini (ver arquitectura,
    sección 51).
    """
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

    # `contexto` es información de CONFIANZA (armada acá, no por el usuario ni por
    # la IA) que las herramientas usan para saber quién está escribiendo — ver
    # services/ai/tools.py, sobre todo crear_solicitud_contacto.
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
