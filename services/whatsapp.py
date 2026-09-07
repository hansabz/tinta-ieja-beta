"""Utilidad compartida para armar enlaces de WhatsApp (wa.me).

Vive acá (fuera de services/ai/ y de apps/appointments/) porque la usan dos
partes independientes del proyecto: el chatbot (services/ai/tools.py, para
"quiero hablar con Juan") y el sistema de citas (apps/appointments/services.py,
para avisar al tatuador o al gerente de un turno nuevo). Ninguna de las dos
depende de la otra — ambas importan esto.
"""

import re
from urllib.parse import quote


def link_whatsapp(numero, mensaje=""):
    """Arma un link https://wa.me/<numero> a partir de un número con o sin
    formato (espacios, guiones, "+"). Devuelve "" si no hay dígitos válidos —
    nunca se inventa un número. `mensaje`, si se da, precarga el texto del chat."""
    digitos = re.sub(r"[^0-9]", "", numero or "")
    if not digitos:
        return ""
    base = f"https://wa.me/{digitos}"
    return f"{base}?text={quote(mensaje)}" if mensaje else base
