from django.conf import settings

from .openai_compatible import llamar_chat_completions

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"


def completar(messages, tools):
    return llamar_chat_completions(BASE_URL, settings.GEMINI_API_KEY, settings.GEMINI_MODEL, messages, tools)
