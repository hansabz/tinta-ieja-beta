"""Herramientas controladas del agente (ver arquitectura, sección 30-32).

El LLM nunca ejecuta código ni accede a la base de datos directamente: solo puede
pedir que se llame a una de estas funciones, con parámetros que él mismo genera.
Cada función valida sus parámetros, tiene un límite de resultados, y nunca recibe
ni expone secretos (API keys, DATABASE_URL, SECRET_KEY) — esos ni siquiera existen
en el contexto que ve el modelo.

`contexto` es información de confianza que arma el backend (nunca el LLM): quién es
el usuario real de la conversación. crear_solicitud_contacto usa `contexto` para
saber a quién pertenece la solicitud — el modelo nunca puede asignar un cliente
arbitrario, solo redactar el motivo.
"""

import logging
import re

logger = logging.getLogger("chatbot.tools")


def _link_whatsapp(numero):
    digitos = re.sub(r"[^0-9]", "", numero or "")
    return f"https://wa.me/{digitos}" if digitos else ""


def consultar_informacion_estudio(args, contexto):
    from apps.studio.models import ConfiguracionEstudio

    estudio = ConfiguracionEstudio.obtener()
    return {
        "nombre": estudio.nombre,
        "descripcion": estudio.descripcion,
        "direccion": estudio.direccion,
        "horarios": estudio.horarios,
        "telefono": estudio.telefono,
        "redes_sociales": estudio.redes_sociales,
        "politicas": estudio.politicas,
        "cuidados": estudio.cuidados,
    }


def consultar_artistas(args, contexto):
    from apps.artists.models import Empleado

    qs = Empleado.objects.filter(es_artista=True, activo=True).select_related("usuario")
    especialidad = (args.get("especialidad") or "").strip()
    if especialidad:
        qs = qs.filter(especialidades__icontains=especialidad)
    return [
        {
            "nombre": e.usuario.get_full_name() or e.usuario.username,
            "especialidades": e.especialidades,
            "biografia": e.biografia,
        }
        for e in qs[:10]
    ]


def consultar_obras(args, contexto):
    from apps.gallery.models import Obra

    qs = Obra.objects.select_related("artista__usuario", "estilo").order_by("-fecha")
    estilo = (args.get("estilo") or "").strip()
    if estilo:
        qs = qs.filter(estilo__nombre__icontains=estilo)
    return [
        {
            "titulo": o.titulo,
            "artista": o.artista.usuario.get_full_name() or o.artista.usuario.username,
            "estilo": o.estilo.nombre,
            "zona_cuerpo": o.zona_cuerpo,
        }
        for o in qs[:8]
    ]


def consultar_estilos(args, contexto):
    from apps.gallery.models import Estilo

    return [{"nombre": e.nombre, "descripcion": e.descripcion} for e in Estilo.objects.all()[:20]]


def crear_solicitud_contacto(args, contexto):
    from apps.contacts.models import SolicitudContacto

    motivo = (args.get("motivo") or "").strip()[:1000]
    if not motivo:
        return {"error": "Falta el motivo de la solicitud."}

    usuario = contexto.get("usuario")
    nombre = (args.get("nombre") or "").strip()[:120]
    contacto = (args.get("contacto") or "").strip()[:120]

    solicitud = SolicitudContacto(motivo=motivo)
    if usuario is not None and usuario.is_authenticated:
        solicitud.cliente = usuario
        perfil = getattr(usuario, "cliente", None)
        if perfil and perfil.artista_asignado_id:
            solicitud.empleado = perfil.artista_asignado
    elif nombre and contacto:
        solicitud.nombre_contacto = nombre
        solicitud.contacto = contacto
    else:
        return {
            "error": "no_identificado",
            "mensaje_para_usuario": "Para crear la solicitud necesito tu nombre y un email o teléfono de contacto — pedíselos al usuario y volvé a llamar a esta herramienta con esos datos.",
        }

    solicitud.full_clean()
    solicitud.save()
    logger.info("SolicitudContacto #%s creada desde el chatbot", solicitud.pk)
    return {"ok": True, "id": solicitud.pk, "estado": solicitud.estado}


def obtener_contacto_whatsapp(args, contexto):
    """Devuelve el link de WhatsApp de un artista puntual (si lo pidieron por nombre
    y tiene uno cargado) o, si no, el WhatsApp general del estudio. Nunca inventa un
    número: si no hay ninguno configurado, lo dice con honestidad."""
    from django.db.models import Q

    from apps.artists.models import Empleado
    from apps.studio.models import ConfiguracionEstudio

    nombre_pedido = (args.get("nombre_artista") or "").strip()

    if nombre_pedido:
        empleado = (
            Empleado.objects.filter(activo=True)
            .filter(
                Q(usuario__first_name__icontains=nombre_pedido)
                | Q(usuario__last_name__icontains=nombre_pedido)
                | Q(usuario__username__icontains=nombre_pedido)
            )
            .select_related("usuario")
            .first()
        )
        if empleado is None:
            return {"error": "artista_no_encontrado", "nombre_pedido": nombre_pedido}
        nombre_real = empleado.usuario.get_full_name() or empleado.usuario.username
        if empleado.whatsapp:
            logger.info("WhatsApp de artista '%s' entregado desde el chatbot", nombre_real)
            return {
                "tipo": "artista",
                "nombre": nombre_real,
                "whatsapp_link": _link_whatsapp(empleado.whatsapp),
            }
        # el artista existe pero no tiene whatsapp cargado -> ofrecer el general como alternativa
        estudio = ConfiguracionEstudio.obtener()
        if estudio.whatsapp_general:
            return {
                "tipo": "sin_whatsapp_de_artista_usar_general",
                "nombre_artista": nombre_real,
                "whatsapp_link": _link_whatsapp(estudio.whatsapp_general),
            }
        return {"error": "sin_whatsapp_configurado"}

    estudio = ConfiguracionEstudio.obtener()
    if not estudio.whatsapp_general:
        return {"error": "sin_whatsapp_configurado"}
    logger.info("WhatsApp general del estudio entregado desde el chatbot")
    return {"tipo": "general", "whatsapp_link": _link_whatsapp(estudio.whatsapp_general)}


def buscar_informacion_web(args, contexto):
    from django.conf import settings

    consulta = (args.get("consulta") or "").strip()[:200]
    if not consulta:
        return {"error": "Falta la consulta."}
    if not settings.TAVILY_API_KEY:
        return {"error": "servicio_no_configurado"}

    try:
        from tavily import TavilyClient

        cliente = TavilyClient(api_key=settings.TAVILY_API_KEY)
        resultado = cliente.search(
            query=f"{consulta} tatuaje historia cultura",
            max_results=4,
            include_answer=True,
        )
    except Exception:
        logger.exception("Fallo la busqueda web (Tavily)")
        return {"error": "fallo_busqueda"}

    fuentes = [
        {"titulo": r.get("title"), "url": r.get("url")}
        for r in resultado.get("results", [])[:4]
    ]
    return {"resumen": resultado.get("answer", ""), "fuentes": fuentes}


TOOL_REGISTRY = {
    "consultar_informacion_estudio": consultar_informacion_estudio,
    "consultar_artistas": consultar_artistas,
    "consultar_obras": consultar_obras,
    "consultar_estilos": consultar_estilos,
    "crear_solicitud_contacto": crear_solicitud_contacto,
    "obtener_contacto_whatsapp": obtener_contacto_whatsapp,
    "buscar_informacion_web": buscar_informacion_web,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "consultar_informacion_estudio",
            "description": "Devuelve la información real y verificada del estudio: dirección, horarios, teléfono, políticas y cuidados. Usar siempre que pregunten por estos datos, nunca inventarlos.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_artistas",
            "description": "Lista los artistas/tatuadores reales del estudio, opcionalmente filtrados por especialidad.",
            "parameters": {
                "type": "object",
                "properties": {
                    "especialidad": {"type": "string", "description": "Ej: 'Old School', 'Realismo'. Opcional."}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_obras",
            "description": "Lista trabajos reales del portafolio del estudio, opcionalmente filtrados por estilo.",
            "parameters": {
                "type": "object",
                "properties": {"estilo": {"type": "string", "description": "Ej: 'Blackwork'. Opcional."}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_estilos",
            "description": "Lista los estilos de tatuaje que trabaja el estudio.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crear_solicitud_contacto",
            "description": "Crea una solicitud para que un empleado o el gerente del estudio contacte al usuario. Usar cuando el usuario pida explícitamente hablar con una persona, pedir una cotización, o agendar algo que el asistente no puede resolver solo. Si el usuario no tiene sesión iniciada, esta herramienta devuelve 'no_identificado' la primera vez: en ese caso pedile su nombre y un email o teléfono en el chat, y volvé a llamar a la herramienta incluyendo 'nombre' y 'contacto'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "motivo": {"type": "string", "description": "Resumen breve de lo que necesita el usuario."},
                    "nombre": {"type": "string", "description": "Nombre de quien escribe. Solo hace falta si no tiene sesión iniciada."},
                    "contacto": {"type": "string", "description": "Email o teléfono de quien escribe. Solo hace falta si no tiene sesión iniciada."},
                },
                "required": ["motivo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_contacto_whatsapp",
            "description": "Devuelve un link de WhatsApp para hablar directo con una persona del estudio — la forma preferida de conectar al usuario con un humano, porque los artistas no siempre están pendientes de la página. Si el usuario nombra a un artista específico ('quiero hablar con Facu'), pasá 'nombre_artista' y te da su WhatsApp directo. Si no especifica con quién, llamala sin argumentos y te da el WhatsApp general del estudio. Compartí el link tal cual en la respuesta.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_artista": {
                        "type": "string",
                        "description": "Nombre o apellido del artista pedido. Dejar vacío si no especificó a quién.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_informacion_web",
            "description": "Busca en internet información cultural/histórica sobre estilos y símbolos de tatuajes (ej: origen del Irezumi, significado de un símbolo). NO usar para nada que no sea investigación cultural de tatuajes.",
            "parameters": {
                "type": "object",
                "properties": {"consulta": {"type": "string", "description": "Qué investigar."}},
                "required": ["consulta"],
            },
        },
    },
]


def ejecutar_herramienta(nombre, argumentos, contexto):
    """Despacha de forma segura una llamada a herramienta pedida por el LLM."""
    funcion = TOOL_REGISTRY.get(nombre)
    if funcion is None:
        return {"error": f"herramienta_desconocida:{nombre}"}
    try:
        return funcion(argumentos or {}, contexto)
    except Exception:
        logger.exception("Error ejecutando herramienta %s", nombre)
        return {"error": "error_interno"}
