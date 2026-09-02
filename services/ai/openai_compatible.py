"""Cliente mínimo para APIs de chat compatibles con el formato de OpenAI
(Groq y Gemini exponen ambos este mismo formato — ver arquitectura, sección 8)."""

import httpx

from .base import ProviderError


def llamar_chat_completions(base_url, api_key, model, messages, tools, timeout=20):
    if not api_key:
        raise ProviderError("sin_api_key")

    try:
        resp = httpx.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": messages,
                "tools": tools,
                "tool_choice": "auto",
                "temperature": 0.4,
                "max_tokens": 700,
            },
            timeout=timeout,
        )
    except httpx.HTTPError as exc:
        raise ProviderError(f"error_de_red:{exc}") from exc

    if resp.status_code == 429:
        raise ProviderError("limite_de_cuota")
    if resp.status_code >= 400:
        raise ProviderError(f"error_http_{resp.status_code}:{resp.text[:200]}")

    return resp.json()
