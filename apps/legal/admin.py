from django.contrib import admin

from .models import DocumentoLegal


@admin.register(DocumentoLegal)
class DocumentoLegalAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "actualizado")
    readonly_fields = ("tipo", "actualizado")
    fields = ("tipo", "titulo", "contenido", "actualizado")

    def has_add_permission(self, request):
        # Los 4 documentos ya existen (creados por una migración) — no se agregan más.
        return False

    def has_delete_permission(self, request, obj=None):
        return False
