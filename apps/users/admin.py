from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Cliente, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "email", "rol", "is_staff", "is_active")
    list_filter = ("rol", "is_staff", "is_active")
    fieldsets = UserAdmin.fieldsets + (("Rol", {"fields": ("rol",)}),)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("usuario", "telefono", "artista_asignado")
    autocomplete_fields = ("usuario",)
