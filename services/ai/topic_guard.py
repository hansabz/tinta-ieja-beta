"""Filtro rápido antes de gastar una llamada al LLM.

Un filtro por palabras clave no puede detectar de forma confiable "está fuera de
tema" en general (eso lo hace mejor el propio modelo, guiado por el system prompt).
Lo que SÍ puede detectar barato y bien es el patrón de los intentos más comunes de
jailbreak/prompt injection ("ignorá tus instrucciones", "revelá tu prompt", "dame
la API key", etc.) — y cortarlos antes de que le lleguen al modelo, sin gastar cuota.
"""

import re

PATRONES_JAILBREAK = [
    r"ignor[ae].{0,20}instruccion",
    r"ignore.{0,20}(previous|prior|above).{0,20}instruction",
    r"olvid[aá].{0,20}(instruccion|que (sos|eres)|quien (sos|eres))",
    r"revel[aá].{0,20}(prompt|instruccion|configuraci[oó]n|system)",
    r"system\s*prompt",
    r"act[uú]a\s+como",
    r"^act\s+as\b",
    r"modo\s+desarrollador",
    r"developer\s+mode",
    r"\bdan\s+mode\b",
    r"(api.?key|token|secret.?key|database.?url)",
]

_REGEX = re.compile("|".join(PATRONES_JAILBREAK), re.IGNORECASE)

RESPUESTA_JAILBREAK = (
    "No puedo compartir configuración interna ni cambiar de rol. "
    "Puedo ayudarte con horarios, artistas, estilos o conectarte con el equipo del estudio."
)


def es_intento_de_jailbreak(mensaje: str) -> bool:
    return bool(_REGEX.search(mensaje or ""))
