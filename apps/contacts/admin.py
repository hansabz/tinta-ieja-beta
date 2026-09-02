from django.contrib import admin

from .models import SolicitudContacto


@admin.register(SolicitudContacto)
class SolicitudContactoAdmin(admin.ModelAdmin):
    list_display = ("quien", "contacto", "empleado", "estado", "fecha")
    list_filter = ("estado",)
    search_fields = ("nombre_contacto", "contacto", "motivo", "cliente__username", "cliente__email")
    autocomplete_fields = ("cliente", "empleado")

    @admin.display(description="De")
    def quien(self, obj):
        return str(obj.cliente) if obj.cliente_id else obj.nombre_contacto
