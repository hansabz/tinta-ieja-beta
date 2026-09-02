from django.contrib import admin

from .models import ConfiguracionEstudio


@admin.register(ConfiguracionEstudio)
class ConfiguracionEstudioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "whatsapp_general", "generacion_ia_habilitada")

    def has_add_permission(self, request):
        # singleton: no permitir crear una segunda fila
        return not ConfiguracionEstudio.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
