"""App "artists": el perfil de trabajo de cada empleado/artista del estudio.

Empleado es una extensión de Usuario (apps.users.models.Usuario) — todo empleado
o artista primero existe como Usuario con rol=EMPLEADO (eso da el login), y ACÁ
se guarda la info específica de su trabajo (bio, especialidades, WhatsApp, foto).

Se crea desde /admin/users/usuario/add/: ahí mismo, en un solo formulario, se
carga el nombre de la cuenta (username/contraseña), el nombre que se va a ver
en la página pública (first_name/last_name) y el rol — y más abajo, en la
sección "Perfil de empleado/tatuador", los datos de este modelo (biografía,
especialidades, foto). Ya no hace falta ir a dos pantallas separadas."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Empleado(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="empleado")
    biografia = models.TextField(blank=True)
    es_artista = models.BooleanField(default=True)
    especialidades = models.CharField(max_length=255, blank=True, help_text="Ej: Blackwork, Old School")
    foto = models.ImageField(
        upload_to="artistas/",
        blank=True,
        null=True,
        help_text="Foto de perfil pública — se sube directo desde tu computadora.",
    )
    activo = models.BooleanField(default=True)
    whatsapp = models.CharField(
        max_length=30,
        blank=True,
        help_text="Número con código de país, solo dígitos. Ej: 5491122334455. "
        "Si se deja vacío, el chatbot ofrece el WhatsApp general del estudio en su lugar.",
    )

    def clean(self):
        # Espejo de Cliente.clean() (apps.users.models) — un usuario no puede
        # tener los dos perfiles ni un rol que no corresponda.
        from apps.users.models import Rol

        if self.usuario_id and hasattr(self.usuario, "cliente"):
            raise ValidationError(
                "Este usuario ya tiene un perfil de cliente — no puede ser empleado al mismo tiempo."
            )
        if self.usuario_id and self.usuario.rol not in (Rol.EMPLEADO, Rol.ADMINISTRADOR):
            raise ValidationError(
                f"Este usuario tiene rol '{self.usuario.get_rol_display()}', no Empleado/Administrador. "
                "Cambiá el rol en la ficha del usuario antes de crear su perfil de empleado."
            )

    def __str__(self):
        return str(self.usuario)
