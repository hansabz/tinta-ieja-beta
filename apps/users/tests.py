from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.artists.models import Empleado

from .adapters import CustomSocialAccountAdapter
from .models import Cliente, Rol, Usuario


class RegistroPublicoTests(TestCase):
    """Con más de un AUTHENTICATION_BACKENDS configurado (desde que existe
    login con Google) login() explota si no se le dice qué backend usar —
    pasó de verdad en producción. Esto lo bloquea para siempre."""

    def test_registro_no_rompe_al_loguear_automaticamente(self):
        respuesta = self.client.post("/cuentas/registro/", {
            "username": "cliente.nuevo.test",
            "email": "cliente@ejemplo.com",
            "password1": "ContraseñaSegura123!",
            "password2": "ContraseñaSegura123!",
        })
        self.assertEqual(respuesta.status_code, 302)
        usuario = Usuario.objects.get(username="cliente.nuevo.test")
        self.assertEqual(usuario.rol, Rol.CLIENTE)
        self.assertTrue(Cliente.objects.filter(usuario=usuario).exists())
        # Si login() hubiera fallado, la sesión no quedaría autenticada.
        respuesta_home = self.client.get("/")
        self.assertContains(respuesta_home, "cliente.nuevo.test")


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


class NoClienteYEmpleadoALaVezTests(TestCase):
    """Antes de esta validación, nada impedía que un usuario terminara con
    perfil de Cliente Y de Empleado a la vez (o con un rol que no coincidía
    con ninguno de los dos) — así se armó la inconsistencia que reportó el
    gerente. Ver Cliente.clean()/Empleado.clean()."""

    def test_no_se_puede_crear_empleado_si_ya_es_cliente(self):
        usuario = Usuario.objects.create(username="ya.es.cliente", rol=Rol.CLIENTE)
        Cliente.objects.create(usuario=usuario)
        with self.assertRaises(ValidationError):
            Empleado(usuario=usuario).clean()

    def test_no_se_puede_crear_cliente_si_ya_es_empleado(self):
        usuario = Usuario.objects.create(username="ya.es.empleado", rol=Rol.EMPLEADO)
        Empleado.objects.create(usuario=usuario)
        with self.assertRaises(ValidationError):
            Cliente(usuario=usuario).clean()

    def test_no_se_puede_crear_empleado_con_rol_cliente(self):
        usuario = Usuario.objects.create(username="rol.equivocado", rol=Rol.CLIENTE)
        with self.assertRaises(ValidationError):
            Empleado(usuario=usuario).clean()

    def test_no_se_puede_crear_cliente_con_rol_empleado(self):
        usuario = Usuario.objects.create(username="rol.equivocado.2", rol=Rol.EMPLEADO)
        with self.assertRaises(ValidationError):
            Cliente(usuario=usuario).clean()

    def test_empleado_con_rol_correcto_no_lanza_error(self):
        usuario = Usuario.objects.create(username="todo.bien", rol=Rol.EMPLEADO)
        Empleado(usuario=usuario).clean()  # no debe lanzar

    def test_admin_descarta_los_dos_perfiles_si_se_cargan_juntos(self):
        # El caso real que reportó el gerente: cargar Cliente Y Empleado en la
        # MISMA pantalla de alta. Acá ninguno de los dos clean() de arriba
        # alcanza a detectarlo solo (ver save_related en apps.users.admin),
        # así que se prueba el flujo completo vía el admin, no el modelo.
        from django.test import Client

        admin_user = Usuario.objects.create(
            username="admin.doblerol.test", rol=Rol.ADMINISTRADOR, is_staff=True, is_superuser=True
        )
        cliente = Client()
        cliente.force_login(admin_user)

        datos = {
            "username": "doble.rol.test",
            "password1": "ContraseñaSegura123!",
            "password2": "ContraseñaSegura123!",
            "first_name": "Doble", "last_name": "Rol", "email": "",
            "rol": Rol.EMPLEADO, "usable_password": "true",
            "empleado-TOTAL_FORMS": "1", "empleado-INITIAL_FORMS": "0",
            "empleado-MIN_NUM_FORMS": "0", "empleado-MAX_NUM_FORMS": "1",
            "empleado-0-especialidades": "Realismo", "empleado-0-es_artista": "on", "empleado-0-activo": "on",
            "cliente-TOTAL_FORMS": "1", "cliente-INITIAL_FORMS": "0",
            "cliente-MIN_NUM_FORMS": "0", "cliente-MAX_NUM_FORMS": "1",
            "cliente-0-telefono": "5491111111111",
            "_save": "Save",
        }
        respuesta = cliente.post("/admin/users/usuario/add/", datos)
        self.assertEqual(respuesta.status_code, 302)  # el usuario en sí se guarda

        nuevo = Usuario.objects.get(username="doble.rol.test")
        self.assertFalse(Cliente.objects.filter(usuario=nuevo).exists())
        self.assertFalse(Empleado.objects.filter(usuario=nuevo).exists())
