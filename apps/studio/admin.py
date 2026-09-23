from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site

from .models import ConfiguracionEstudio


@admin.register(ConfiguracionEstudio)
class ConfiguracionEstudioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "whatsapp_general", "generacion_ia_habilitada")

    def has_add_permission(self, request):
        # singleton: no permitir crear una segunda fila
        return not ConfiguracionEstudio.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# --- Panel /admin más ordenado y con la marca del estudio -------------------
# Vive acá (y no en cada app) porque es configuración GLOBAL del sitio de
# administración, no de un modelo puntual — apps/studio es el lugar más
# lógico dentro del proyecto para "esto es del estudio en general".

admin.site.site_header = "Tinta Vieja — Panel del estudio"
admin.site.site_title = "Tinta Vieja"
admin.site.index_title = "¿Qué querés hacer?"

# Modelos técnicos de Django/allauth que el gerente nunca necesita tocar a
# mano — quedan registrados igual (por si hiciera falta un día) pero no
# ensucian la pantalla principal del admin. Social Applications (las
# credenciales de Google) NO se toca: esa sí la necesita el gerente.
from allauth.account.models import EmailAddress  # noqa: E402
from allauth.socialaccount.models import SocialAccount, SocialToken  # noqa: E402

for _modelo in (Group, Site, EmailAddress, SocialToken, SocialAccount):
    try:
        admin.site.unregister(_modelo)
    except admin.sites.NotRegistered:
        pass

# El orden por defecto es alfabético por app — esto prioriza lo que se usa
# todos los días (citas, config del estudio, artistas) sobre lo que casi no
# se toca (usuarios técnicos, integraciones).
_ORDEN_APPS = ["appointments", "studio", "artists", "gallery", "users", "contacts", "chatbot", "legal", "socialaccount"]


def _get_app_list_ordenado(self, request, app_label=None):
    app_dict = self._build_app_dict(request, app_label)
    app_list = list(app_dict.values())

    def _posicion(app):
        try:
            return _ORDEN_APPS.index(app["app_label"])
        except ValueError:
            return len(_ORDEN_APPS)

    app_list.sort(key=_posicion)
    return app_list


admin.site.get_app_list = _get_app_list_ordenado.__get__(admin.site, admin.site.__class__)
