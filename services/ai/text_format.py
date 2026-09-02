"""Red de seguridad para el estilo de respuesta: la instrucción principal está en el
system prompt (texto plano, sin Markdown), pero si igual se cuela algo de formato,
esto lo limpia antes de mostrarlo en el chat."""

import re

_FILA_SEPARADORA = re.compile(r"^\|?[\s:\-|]+\|?$")


def limpiar_formato(texto: str) -> str:
    if not texto:
        return texto

    lineas_limpias = []
    for linea in texto.split("\n"):
        l = linea.strip()

        if _FILA_SEPARADORA.match(l) and "|" in l:
            continue  # fila separadora de tabla markdown (---|---)

        if l.count("|") >= 2:
            celdas = [c.strip() for c in l.strip("|").split("|") if c.strip()]
            l = ", ".join(celdas)

        l = re.sub(r"^#{1,6}\s*", "", l)  # títulos "# Estilos"
        l = re.sub(r"^[-*]\s+", "", l)  # viñetas "- Blackwork"
        l = l.replace("**", "").replace("__", "")  # negrita/subrayado
        l = re.sub(r"`([^`]*)`", r"\1", l)  # `código`

        lineas_limpias.append(l)

    resultado = "\n".join(lineas_limpias).strip()
    resultado = re.sub(r"\n{3,}", "\n\n", resultado)
    return resultado
