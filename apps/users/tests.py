from unittest.mock import patch

from django.test import TestCase

from .adapters import CustomSocialAccountAdapter
from .models import Cliente, Rol, Usuario


class LoginConGoogleTests(TestCase):
    """El login con Google usa django-allauth, que no sabe nada de nuestros
    roles — CustomSocialAccountAdapter es lo que hace cumplir la misma regla
    del registro público (ver apps.users.views.RegistroView): toda cuenta
    nueva es CLIENTE, nunca staff/superuser, pase lo que pase."""

    def test_fuerza_rol_cliente_y_crea_perfil_de_cliente(self):
        # Simula el caso más peligroso: que el resultado de allauth viniera
        # (por el motivo que sea) con privilegios — igual se corrigen acá.
        usuario = Usuario.objects.create(
            username="google.test", rol=Rol.ADMINISTRADOR, is_staff=True, is_superuser=True
        )
        adapter = CustomSocialAccountAdapter()
        ruta = "apps.users.adapters.DefaultSocialAccountAdapter.save_user"
        with patch(ruta, return_value=usuario):
            resultado = adapter.save_user(request=None, sociallogin=None, form=None)

        resultado.refresh_from_db()
        self.assertEqual(resultado.rol, Rol.CLIENTE)
        self.assertFalse(resultado.is_staff)
        self.assertFalse(resultado.is_superuser)
        self.assertTrue(Cliente.objects.filter(usuario=resultado).exists())
