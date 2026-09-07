from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Cliente, Rol, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "email", "rol", "is_staff", "is_active")
    list_filter = ("rol", "is_staff", "is_active")
    fieldsets = UserAdmin.fieldsets + (("Rol", {"fields": ("rol",)}),)

    def save_model(self, request, obj, form, change):
        # Un empleado o administrador necesita entrar a /admin (para gestionar
        # sus citas — ver apps.appointments.admin), así que al asignarle ese
        # rol se le habilita el acceso automáticamente. No se toca is_staff
        # para rol=CLIENTE: ese caso queda a criterio del gerente.
        if obj.rol in (Rol.EMPLEADO, Rol.ADMINISTRADOR):
            obj.is_staff = True
        super().save_model(request, obj, form, change)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("usuario", "telefono", "artista_asignado")
    autocomplete_fields = ("usuario",)
