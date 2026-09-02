from django.contrib import admin

from .models import Estilo, Etiqueta, Obra


@admin.register(Estilo)
class EstiloAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


@admin.register(Etiqueta)
class EtiquetaAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


@admin.register(Obra)
class ObraAdmin(admin.ModelAdmin):
    list_display = ("titulo", "artista", "estilo", "fecha")
    list_filter = ("estilo", "etiquetas")
    search_fields = ("titulo", "descripcion")
    autocomplete_fields = ("artista",)
