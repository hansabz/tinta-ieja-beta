from django.conf import settings

from .openai_compatible import llamar_chat_completions

BASE_URL = "https://api.groq.com/openai/v1"


def completar(messages, tools):
    return llamar_chat_completions(BASE_URL, settings.GROQ_API_KEY, settings.GROQ_MODEL, messages, tools)
