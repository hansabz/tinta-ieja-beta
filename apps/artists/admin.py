from django.contrib import admin

from .models import Empleado


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "es_artista", "especialidades", "whatsapp", "activo")
    list_filter = ("es_artista", "activo")
    search_fields = ("usuario__username", "usuario__first_name", "usuario__last_name", "especialidades")
    autocomplete_fields = ("usuario",)
