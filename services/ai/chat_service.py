"""Orquestador del chat: arma el prompt, llama al proveedor de IA con reintento
automático (Groq -> Gemini), y resuelve las llamadas a herramientas que pida el
modelo. Ver arquitectura, sección 30-32 y 52."""

import json
import logging

from apps.studio.models import ConfiguracionEstudio

from . import gemini_service, groq_service
from .base import ProviderError
from .prompts import TEMA_RECHAZADO, system_prompt
from .text_format import limpiar_formato
from .tools import TOOL_SCHEMAS, ejecutar_herramienta
from .topic_guard import RESPUESTA_JAILBREAK, es_intento_de_jailbreak

logger = logging.getLogger("chatbot.ai")

PROVEEDORES = [("groq", groq_service.completar), ("gemini", gemini_service.completar)]
MAX_RONDAS_HERRAMIENTAS = 4
VENTANA_HISTORIAL = 12


class SinRespuestaDisponible(Exception):
    """Ningún proveedor de IA respondió (sin claves configuradas, límite de cuota
    agotado, o error de red). El llamador debe activar el mensaje de transferencia
    a un humano (ver ConfiguracionEstudio.mensaje_transferencia_ia)."""


def _completar_con_fallback(messages, tools):
    errores = []
    for nombre, funcion in PROVEEDORES:
        try:
            return funcion(messages, tools)
        except ProviderError as exc:
            logger.warning("Proveedor de IA '%s' no respondió: %s", nombre, exc)
            errores.append(f"{nombre}: {exc}")
    raise SinRespuestaDisponible("; ".join(errores))


def responder(mensaje_usuario, historial, contexto):
    """historial: lista de {"role": "user"|"assistant", "content": str}.
    contexto: {"usuario": request.user, "nombre_sesion": str, "contacto_sesion": str}.
    Devuelve el texto de respuesta. Puede levantar SinRespuestaDisponible."""

    if es_intento_de_jailbreak(mensaje_usuario):
        logger.info("Mensaje bloqueado por el filtro de jailbreak/tema")
        return RESPUESTA_JAILBREAK

    estudio = ConfiguracionEstudio.obtener()
    messages = [{"role": "system", "content": system_prompt(estudio.nombre)}]
    messages.extend(historial[-VENTANA_HISTORIAL:])
    messages.append({"role": "user", "content": mensaje_usuario})

    for _ in range(MAX_RONDAS_HERRAMIENTAS):
        data = _completar_con_fallback(messages, TOOL_SCHEMAS)
        choice = data["choices"][0]
        mensaje = choice["message"]
        tool_calls = mensaje.get("tool_calls") or []

        if not tool_calls:
            texto = (mensaje.get("content") or "").strip()
            return limpiar_formato(texto) or TEMA_RECHAZADO

        messages.append(mensaje)
        for llamada in tool_calls:
            nombre_fn = llamada["function"]["name"]
            try:
                argumentos = json.loads(llamada["function"].get("arguments") or "{}")
            except (json.JSONDecodeError, TypeError):
                argumentos = {}
            resultado = ejecutar_herramienta(nombre_fn, argumentos, contexto)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": llamada["id"],
                    "content": json.dumps(resultado, ensure_ascii=False, default=str),
                }
            )

    return "Se complicó procesar tu pedido. ¿Querés que te conecte directo con el equipo del estudio?"
