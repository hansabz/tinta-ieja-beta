"""Pruebas de las reglas de negocio del sistema de citas — ver services.py y
admin.py, que es donde vive toda la lógica que estos tests verifican."""

import io
import tempfile
from datetime import timedelta

from django.contrib import admin as django_admin
from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

from apps.artists.models import Empleado
from apps.gallery.models import Estilo
from apps.studio.models import ConfiguracionEstudio
from apps.users.models import Cliente, Rol, Usuario

from .admin import CitaAdmin
from .excel import exportar_citas_excel, importar_citas_excel
from .models import Cita, EstadoSesion, SesionCita
from .services import ConflictoDeHorario, limpiar_historial_vencido, publicar_en_portafolio, validar_nueva_sesion

# PNG 1x1 válido — para probar ImageField sin depender de un archivo real en disco.
PNG_1X1 = SimpleUploadedFile(
    "resultado.png",
    bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108020000009077"
        "53de0000000c4944415408d763f8cfc0c0c0c000010005ffe6f4f30000000049454e44ae426082"
    ),
    content_type="image/png",
)


def _crear_tatuador(username):
    usuario = Usuario.objects.create(username=username, rol=Rol.EMPLEADO, is_staff=True, password=make_password(None))
    return Empleado.objects.create(usuario=usuario, es_artista=True, activo=True)


def _crear_cliente(username):
    usuario = Usuario.objects.create(username=username, rol=Rol.CLIENTE, password=make_password(None))
    Cliente.objects.create(usuario=usuario)
    return usuario


class ReglasDeAgendaTests(TestCase):
    def setUp(self):
        self.tatuador = _crear_tatuador("tatu.test")
        self.cliente = _crear_cliente("cliente.test")
        self.config = ConfiguracionEstudio.obtener()

    def _cita(self):
        return Cita.objects.create(cliente=self.cliente, tatuador=self.tatuador)

    def test_no_permite_dos_sesiones_que_se_pisan(self):
        inicio = timezone.now() + timedelta(days=1)
        SesionCita.objects.create(cita=self._cita(), numero=1, inicio=inicio, duracion_minutos=120)
        with self.assertRaises(ConflictoDeHorario):
            validar_nueva_sesion(self.tatuador, inicio + timedelta(minutes=30), 120)

    def test_permite_sesion_que_no_se_pisa(self):
        inicio = timezone.now() + timedelta(days=1)
        SesionCita.objects.create(cita=self._cita(), numero=1, inicio=inicio, duracion_minutos=60)
        # No debe lanzar: empieza justo cuando termina la anterior.
        validar_nueva_sesion(self.tatuador, inicio + timedelta(minutes=60), 60)

    def test_tope_mensual_por_tatuador(self):
        # Fechas fijas (no relativas a "hoy") para no cruzar de mes por accidente:
        # todas caen en enero del año que viene, bien separadas entre sí.
        tz = timezone.get_current_timezone()
        base = timezone.datetime(timezone.now().year + 1, 1, 5, 10, 0, tzinfo=tz)
        for i in range(self.config.max_citas_por_tatuador_mes):
            SesionCita.objects.create(
                cita=self._cita(), numero=1, inicio=base + timedelta(days=i * 3), duracion_minutos=60
            )
        # Un cuarto turno ese mismo enero, en un día todavía libre: igual debe
        # rechazarse porque ya se llegó al tope mensual.
        with self.assertRaises(ConflictoDeHorario):
            validar_nueva_sesion(self.tatuador, base.replace(day=25), 60)

    def test_dia_con_sesion_larga_bloquea_otra_sesion_ese_dia(self):
        inicio = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=3)
        SesionCita.objects.create(
            cita=self._cita(), numero=1, inicio=inicio,
            duracion_minutos=self.config.umbral_cita_larga_minutos + 1,
        )
        with self.assertRaises(ConflictoDeHorario):
            validar_nueva_sesion(self.tatuador, inicio + timedelta(hours=6), 30)

    def test_sin_tatuador_elegido_no_valida_agenda(self):
        # Cliente no eligió a nadie: no hay agenda de un tatuador puntual que validar.
        validar_nueva_sesion(None, timezone.now() + timedelta(days=1), 60)


class LimpiezaHistorialTests(TestCase):
    def setUp(self):
        self.tatuador = _crear_tatuador("tatu.hist")
        self.cliente = _crear_cliente("cliente.hist")
        self.config = ConfiguracionEstudio.obtener()

    def test_borra_solo_las_vencidas(self):
        vieja = Cita.objects.create(
            cliente=self.cliente, tatuador=self.tatuador, estado="TERMINADA",
            fecha_finalizada=timezone.now() - timedelta(days=self.config.dias_retencion_historial_citas + 1),
        )
        reciente = Cita.objects.create(
            cliente=self.cliente, tatuador=self.tatuador, estado="TERMINADA",
            fecha_finalizada=timezone.now() - timedelta(days=1),
        )
        pendiente = Cita.objects.create(cliente=self.cliente, tatuador=self.tatuador, estado="PENDIENTE")

        borradas = limpiar_historial_vencido()

        self.assertEqual(borradas, 1)
        self.assertFalse(Cita.objects.filter(pk=vieja.pk).exists())
        self.assertTrue(Cita.objects.filter(pk=reciente.pk).exists())
        self.assertTrue(Cita.objects.filter(pk=pendiente.pk).exists())


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PublicarEnPortafolioTests(TestCase):
    def test_copia_el_archivo_y_no_depende_del_original(self):
        tatuador = _crear_tatuador("tatu.portfolio")
        cliente = _crear_cliente("cliente.portfolio")
        estilo = Estilo.objects.create(nombre="Blackwork-test")
        cita = Cita.objects.create(
            cliente=cliente, tatuador=tatuador, estilo=estilo,
            estado="TERMINADA", fecha_finalizada=timezone.now(), foto_resultado=PNG_1X1,
        )

        obra = publicar_en_portafolio(cita, titulo="Prueba")

        self.assertTrue(obra.imagen.name)
        self.assertNotEqual(obra.imagen.name, cita.foto_resultado.name)
        cita.refresh_from_db()
        self.assertTrue(cita.resultado_publicado_portafolio)
        self.assertEqual(cita.obra_publicada_id, obra.pk)


class PermisosAdminCitasTests(TestCase):
    """Verifica en código (no a mano en el navegador) la regla explícita del
    estudio: un empleado nunca puede borrar del historial, ni siquiera lo
    propio; el gerente/administrador sí."""

    def setUp(self):
        self.factory = RequestFactory()
        self.admin_instance = CitaAdmin(Cita, django_admin.site)
        self.tatuador_empleado = _crear_tatuador("empleado.permisos")
        self.otro_tatuador = _crear_tatuador("otro.permisos")
        self.administrador = Usuario.objects.create(
            username="gerente.permisos", rol=Rol.ADMINISTRADOR, is_staff=True
        )
        self.cliente = _crear_cliente("cliente.permisos")
        self.cita_propia = Cita.objects.create(cliente=self.cliente, tatuador=self.tatuador_empleado)
        self.cita_ajena = Cita.objects.create(cliente=self.cliente, tatuador=self.otro_tatuador)

    def _request_como(self, usuario):
        request = self.factory.get("/admin/appointments/cita/")
        request.user = usuario
        return request

    def test_empleado_no_puede_borrar_ninguna_cita(self):
        req = self._request_como(self.tatuador_empleado.usuario)
        self.assertFalse(self.admin_instance.has_delete_permission(req, self.cita_propia))
        self.assertFalse(self.admin_instance.has_delete_permission(req, self.cita_ajena))
        self.assertFalse(self.admin_instance.has_delete_permission(req, None))

    def test_administrador_si_puede_borrar(self):
        req = self._request_como(self.administrador)
        self.assertTrue(self.admin_instance.has_delete_permission(req, self.cita_propia))

    def test_empleado_solo_ve_sus_propias_citas(self):
        req = self._request_como(self.tatuador_empleado.usuario)
        visibles = list(self.admin_instance.get_queryset(req))
        self.assertIn(self.cita_propia, visibles)
        self.assertNotIn(self.cita_ajena, visibles)

    def test_empleado_no_puede_cambiar_cita_ajena(self):
        req = self._request_como(self.tatuador_empleado.usuario)
        self.assertTrue(self.admin_instance.has_change_permission(req, self.cita_propia))
        self.assertFalse(self.admin_instance.has_change_permission(req, self.cita_ajena))


class ExcelExportImportTests(TestCase):
    def setUp(self):
        self.tatuador = _crear_tatuador("tatu.excel")
        self.cliente = _crear_cliente("cliente.excel")
        self.estilo = Estilo.objects.create(nombre="Realismo-test")

    def test_exportar_incluye_hojas_citas_y_sesiones(self):
        from openpyxl import load_workbook

        cita = Cita.objects.create(cliente=self.cliente, tatuador=self.tatuador, costo=100)
        SesionCita.objects.create(cita=cita, numero=1, inicio=timezone.now() + timedelta(days=1), duracion_minutos=60)

        respuesta = exportar_citas_excel(Cita.objects.filter(pk=cita.pk))
        self.assertEqual(
            respuesta["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        libro = load_workbook(io.BytesIO(respuesta.content))
        self.assertEqual(libro.sheetnames, ["Citas", "Sesiones"])
        fila_cita = list(libro["Citas"].iter_rows(min_row=2, values_only=True))[0]
        self.assertEqual(fila_cita[0], cita.pk)
        self.assertEqual(fila_cita[1], "cliente.excel")
        fila_sesion = list(libro["Sesiones"].iter_rows(min_row=2, values_only=True))[0]
        self.assertEqual(fila_sesion[0], cita.pk)

    def test_importar_crea_cita_nueva_sin_id(self):
        archivo = _libro_citas([
            ["", "cliente.excel", "tatu.excel", "Realismo-test", 2, 150, "PENDIENTE", "prueba"],
        ])
        resumen = importar_citas_excel(archivo)
        self.assertEqual(resumen["creadas"], 1)
        self.assertEqual(resumen["errores"], [])
        cita = Cita.objects.get(cliente=self.cliente)
        self.assertEqual(cita.numero_sesiones, 2)
        self.assertEqual(cita.tatuador, self.tatuador)

    def test_importar_actualiza_cita_existente_por_id(self):
        cita = Cita.objects.create(cliente=self.cliente, costo=10)
        archivo = _libro_citas([
            [cita.pk, "cliente.excel", "", "", 1, 999, "TERMINADA", "actualizada"],
        ])
        resumen = importar_citas_excel(archivo)
        self.assertEqual(resumen["actualizadas"], 1)
        cita.refresh_from_db()
        self.assertEqual(float(cita.costo), 999)
        self.assertEqual(cita.estado, "TERMINADA")
        self.assertIsNotNone(cita.fecha_finalizada)

    def test_importar_reporta_error_sin_romper_el_resto(self):
        archivo = _libro_citas([
            ["", "usuario-que-no-existe", "", "", 1, None, "PENDIENTE", ""],
            ["", "cliente.excel", "", "", 1, None, "PENDIENTE", ""],
        ])
        resumen = importar_citas_excel(archivo)
        self.assertEqual(resumen["creadas"], 1)
        self.assertEqual(len(resumen["errores"]), 1)
        self.assertIn("usuario-que-no-existe", resumen["errores"][0])

    def test_empleado_no_puede_importar(self):
        respuesta = self.client_como(self.tatuador.usuario).get(
            "/admin/appointments/cita/importar-excel/"
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertFalse(Cita.objects.filter(cliente=self.cliente).exists())

    def client_como(self, usuario):
        from django.test import Client

        cliente_http = Client()
        cliente_http.force_login(usuario)
        return cliente_http


def _libro_citas(filas):
    """Arma un .xlsx en memoria con una hoja "Citas" para probar importar_citas_excel."""
    import io as _io

    from openpyxl import Workbook

    libro = Workbook()
    hoja = libro.active
    hoja.title = "Citas"
    hoja.append(["id", "cliente_username", "tatuador_username", "estilo", "numero_sesiones", "costo", "estado", "notas"])
    for fila in filas:
        hoja.append(fila)
    buffer = _io.BytesIO()
    libro.save(buffer)
    buffer.seek(0)
    return buffer
