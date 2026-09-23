from django.test import TestCase
from django.urls import reverse

from .models import DocumentoLegal


class DocumentoLegalTests(TestCase):
    def test_los_4_documentos_existen_tras_migrar(self):
        self.assertEqual(DocumentoLegal.objects.count(), len(DocumentoLegal.Tipo.values))
        for tipo in DocumentoLegal.Tipo.values:
            self.assertTrue(DocumentoLegal.objects.filter(tipo=tipo).exists())

    def test_cada_documento_tiene_contenido_real(self):
        for documento in DocumentoLegal.objects.all():
            self.assertTrue(documento.contenido.strip())
            self.assertTrue(documento.titulo.strip())

    def test_cada_pagina_publica_devuelve_200(self):
        for tipo in DocumentoLegal.Tipo.values:
            resp = self.client.get(reverse("legal:documento", kwargs={"tipo": tipo}))
            self.assertEqual(resp.status_code, 200)
            self.assertContains(resp, DocumentoLegal.objects.get(tipo=tipo).titulo)

    def test_tipo_invalido_devuelve_404(self):
        resp = self.client.get(reverse("legal:documento", kwargs={"tipo": "no-existe"}))
        self.assertEqual(resp.status_code, 404)

    def test_footer_enlaza_los_4_documentos(self):
        resp = self.client.get(reverse("studio:inicio"))
        for tipo in DocumentoLegal.Tipo.values:
            self.assertContains(resp, f"/legal/{tipo}/")


class DocumentoLegalAdminTests(TestCase):
    def setUp(self):
        from apps.users.models import Usuario

        self.admin = Usuario.objects.create_superuser(
            username="admintest", email="admin@test.com", password="clave-segura-123"
        )
        self.client.force_login(self.admin)

    def test_no_se_puede_agregar_un_quinto_documento(self):
        resp = self.client.get(reverse("admin:legal_documentolegal_add"))
        self.assertEqual(resp.status_code, 403)

    def test_no_se_puede_borrar_un_documento(self):
        documento = DocumentoLegal.objects.first()
        resp = self.client.post(
            reverse("admin:legal_documentolegal_delete", args=[documento.pk])
        )
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(DocumentoLegal.objects.filter(pk=documento.pk).exists())

    def test_superusuario_puede_editar_el_contenido(self):
        documento = DocumentoLegal.objects.get(tipo="cookies")
        resp = self.client.post(
            reverse("admin:legal_documentolegal_change", args=[documento.pk]),
            {"titulo": documento.titulo, "contenido": "Texto actualizado de prueba."},
        )
        self.assertEqual(resp.status_code, 302)
        documento.refresh_from_db()
        self.assertEqual(documento.contenido, "Texto actualizado de prueba.")
