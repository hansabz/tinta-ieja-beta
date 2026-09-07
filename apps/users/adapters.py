"""Adaptador de django-allauth para el login con Google.

Existe por una única razón: aplicar la MISMA regla de seguridad crítica que
apps.users.views.RegistroView aplica al registro público — cualquier cuenta
nueva creada por un cliente (con usuario/contraseña o con Google, da igual)
es SIEMPRE rol=CLIENTE, nunca staff ni superuser, sin importar qué mande el
proveedor externo. allauth no sabe nada de nuestros roles, así que hay que
forzarlo acá antes de que la cuenta quede lista para usarse.
"""

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from .models import Cliente, Rol


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        usuario = super().save_user(request, sociallogin, form)

        cambios = []
        if usuario.rol != Rol.CLIENTE:
            usuario.rol = Rol.CLIENTE
            cambios.append("rol")
        if usuario.is_staff:
            usuario.is_staff = False
            cambios.append("is_staff")
        if usuario.is_superuser:
            usuario.is_superuser = False
            cambios.append("is_superuser")
        if cambios:
            usuario.save(update_fields=cambios)

        Cliente.objects.get_or_create(usuario=usuario)
        return usuario
