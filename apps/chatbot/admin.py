from django.contrib import admin

from .models import Conversacion, Mensaje


class MensajeInline(admin.TabularInline):
    model = Mensaje
    extra = 0
    readonly_fields = ("emisor", "texto", "fecha")
    can_delete = False


@admin.register(Conversacion)
class ConversacionAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "session_key", "iniciada", "actualizada")
    list_filter = ("iniciada",)
    search_fields = ("cliente__username", "session_key")
    inlines = [MensajeInline]
