"""Mantiene el registro de django.contrib.sites (Site pk=SITE_ID) apuntando
al dominio real del despliegue.

Por qué existe: el login con Google (django-allauth) y los emails de
"restablecer contraseña" arman sus links usando ESTE registro, no el host de
la petición — si queda en el "example.com" que trae Django por defecto, esos
links salen rotos (bug real que pasó en desarrollo). Se corre solo en cada
deploy de Render (ver build.sh, después de migrate) usando la misma variable
RENDER_EXTERNAL_HOSTNAME que ya se usa para ALLOWED_HOSTS — así nunca hace
falta acordarse de arreglarlo a mano de nuevo.

En local no hace nada solo (no hay RENDER_EXTERNAL_HOSTNAME) — correrlo a
mano ahí es opcional, ver --dominio.
"""

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Sincroniza el dominio del Site con RENDER_EXTERNAL_HOSTNAME (o --dominio a mano)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dominio", default="",
            help="Forzar un dominio en vez de leer RENDER_EXTERNAL_HOSTNAME (útil en local).",
        )

    def handle(self, *args, **options):
        dominio = options["dominio"] or getattr(settings, "RENDER_EXTERNAL_HOSTNAME", "")
        if not dominio:
            self.stdout.write("Nada que sincronizar (no hay RENDER_EXTERNAL_HOSTNAME ni --dominio).")
            return

        site, _ = Site.objects.get_or_create(pk=settings.SITE_ID, defaults={"domain": dominio, "name": dominio})
        if site.domain != dominio:
            site.domain = dominio
            site.name = dominio
            site.save()
            self.stdout.write(self.style.SUCCESS(f"Site actualizado a: {dominio}"))
        else:
            self.stdout.write(f"Site ya estaba en: {dominio}")
