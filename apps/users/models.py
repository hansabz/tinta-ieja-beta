from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class Rol(models.TextChoices):
    CLIENTE = "CLIENTE", "Cliente"
    EMPLEADO = "EMPLEADO", "Empleado"
    ADMINISTRADOR = "ADMINISTRADOR", "Administrador"


class Usuario(AbstractUser):
    """Usuario base. El registro público SIEMPRE crea rol=CLIENTE (ver apps.users.views)."""

    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.CLIENTE)

    def es_cliente(self):
        return self.rol == Rol.CLIENTE

    def es_empleado(self):
        return self.rol == Rol.EMPLEADO

    def es_administrador(self):
        return self.rol == Rol.ADMINISTRADOR or self.is_superuser

    def __str__(self):
        return self.get_full_name() or self.username


class Cliente(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name="cliente")
    telefono = models.CharField(max_length=30, blank=True)
    artista_asignado = models.ForeignKey(
        "artists.Empleado",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clientes_asignados",
    )

    def clean(self):
        # Un usuario nunca puede ser cliente y empleado al mismo tiempo —
        # antes nada lo impedía y eso generó cuentas inconsistentes desde
        # /admin. Ver Empleado.clean() en apps.artists.models para la
        # validación espejo.
        if self.usuario_id and hasattr(self.usuario, "empleado"):
            raise ValidationError(
                "Este usuario ya tiene un perfil de empleado/tatuador — no puede ser cliente al mismo tiempo."
            )
        if self.usuario_id and self.usuario.rol != Rol.CLIENTE:
            raise ValidationError(
                f"Este usuario tiene rol '{self.usuario.get_rol_display()}', no Cliente. "
                "Cambiá el rol en la ficha del usuario antes de crear su perfil de cliente."
            )

    def __str__(self):
        return str(self.usuario)
