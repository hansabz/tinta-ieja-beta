"""Panel de usuarios en /admin.

Antes, "Agregar usuario" solo mostraba usuario/contraseña — el rol y el
nombre a mostrar en la página (first_name/last_name) quedaban ocultos hasta
guardar y volver a entrar a editar. Eso causó cuentas creadas con rol
CLIENTE por defecto que después se les agregaba (a mano) un perfil de
Empleado, quedando inconsistentes. Ahora todo eso se completa en la MISMA
pantalla de alta — ver add_fieldsets e inlines más abajo.
"""

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse

from apps.artists.models import Empleado

from .models import Cliente, Rol, Usuario


class EmpleadoInline(admin.StackedInline):
    """Completar SOLO si el rol de arriba es Empleado o Administrador."""

    model = Empleado
    fk_name = "usuario"
    extra = 0
    max_num = 1
    fields = ("biografia", "es_artista", "especialidades", "whatsapp", "foto", "activo")
    verbose_name = "Perfil de empleado/tatuador"
    verbose_name_plural = "Perfil de empleado/tatuador (solo si el rol es Empleado o Administrador)"


class ClienteInline(admin.StackedInline):
    """Completar SOLO si el rol de arriba es Cliente. El registro público ya
    crea esto solo — esto es para cuando el gerente carga un cliente a mano."""

    model = Cliente
    fk_name = "usuario"
    extra = 0
    max_num = 1
    fields = ("telefono", "artista_asignado")
    autocomplete_fields = ("artista_asignado",)
    verbose_name = "Perfil de cliente"
    verbose_name_plural = "Perfil de cliente (solo si el rol es Cliente)"


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "get_full_name", "email", "rol", "is_staff", "is_active")
    list_filter = ("rol", "is_staff", "is_active")
    fieldsets = UserAdmin.fieldsets + (("Rol", {"fields": ("rol",)}),)
    # A diferencia del admin default de Django, acá SÍ se pide nombre visible
    # (first_name/last_name), email y rol ya en el alta — no solo usuario/contraseña.
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "description": (
                "El nombre de usuario es solo para iniciar sesión (no se muestra en la "
                "página). Nombre y apellido son lo que va a ver el público."
            ),
            "fields": ("username", "usable_password", "password1", "password2", "first_name", "last_name", "email", "rol"),
        }),
    )
    inlines = [EmpleadoInline, ClienteInline]

    def user_change_password(self, request, id, form_url=""):
        # Regla explícita del estudio: cambiarle la contraseña a OTRA persona
        # desde acá solo lo puede hacer un superusuario real, y nunca a un
        # cliente (un cliente que se olvidó la suya usa "¿Olvidaste tu
        # contraseña?" en la pantalla de login — self-service, no esto).
        usuario_objetivo = self.get_object(request, id)
        if usuario_objetivo is not None and usuario_objetivo.rol == Rol.CLIENTE:
            if not request.user.is_superuser:
                raise PermissionDenied
            messages.error(
                request,
                "No se puede cambiar la contraseña de un cliente desde acá — es su cuenta, "
                "que la restablezca él mismo con \"¿Olvidaste tu contraseña?\" en el login.",
            )
            return redirect(reverse("admin:users_usuario_change", args=[id]))
        if not request.user.is_superuser:
            raise PermissionDenied
        return super().user_change_password(request, id, form_url)

    def save_model(self, request, obj, form, change):
        # Un empleado o administrador necesita entrar a /admin (para gestionar
        # sus citas — ver apps.appointments.admin), así que al asignarle ese
        # rol se le habilita el acceso automáticamente. No se toca is_staff
        # para rol=CLIENTE: ese caso queda a criterio del gerente.
        if obj.rol in (Rol.EMPLEADO, Rol.ADMINISTRADOR):
            obj.is_staff = True
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        # Cliente.clean()/Empleado.clean() solo detectan el caso de agregarle
        # un segundo perfil a un usuario que YA tenía uno guardado — no
        # alcanzan a ver el caso de cargar los dos inlines EN LA MISMA
        # pantalla, porque en ese momento ninguno de los dos existe todavía
        # en la base (ver el bug real que reportó el gerente). Se completa
        # acá: si después de guardar terminaron existiendo los dos, se
        # descartan ambos (nada queda a medias) y se avisa por qué.
        super().save_related(request, form, formsets, change)
        usuario = form.instance
        tiene_cliente = Cliente.objects.filter(usuario_id=usuario.pk).exists()
        tiene_empleado = Empleado.objects.filter(usuario_id=usuario.pk).exists()
        if tiene_cliente and tiene_empleado:
            Cliente.objects.filter(usuario_id=usuario.pk).delete()
            Empleado.objects.filter(usuario_id=usuario.pk).delete()
            messages.error(
                request,
                "Un usuario no puede tener perfil de Cliente Y de Empleado al mismo tiempo — "
                "se guardó el usuario, pero se descartaron los dos perfiles. Volvé a entrar a "
                "esta ficha y completá SOLO el que corresponda a su rol.",
            )


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("usuario", "telefono", "artista_asignado")
    autocomplete_fields = ("usuario", "artista_asignado")
