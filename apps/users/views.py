import logging
import smtplib

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView

from .forms import RegistroForm
from .models import Cliente, Rol

logger = logging.getLogger("apps.users")


class RegistroView(CreateView):
    form_class = RegistroForm
    template_name = "users/registro.html"
    success_url = reverse_lazy("studio:inicio")

    def form_valid(self, form):
        usuario = form.save(commit=False)
        # Regla de seguridad crítica: el registro público SIEMPRE crea CLIENTE.
        # No se lee ningún campo "rol"/"role" del request bajo ninguna circunstancia,
        # incluso si el formulario fuera manipulado para enviarlo.
        usuario.rol = Rol.CLIENTE
        usuario.is_staff = False
        usuario.is_superuser = False
        usuario.save()
        Cliente.objects.create(usuario=usuario)
        self.object = usuario
        # Desde que existe login con Google (django-allauth) hay más de un
        # backend de autenticación configurado (ver AUTHENTICATION_BACKENDS
        # en settings.py) — login() ya no puede adivinar cuál usar y hace
        # falta indicarlo a mano. Sin esto, cualquier registro público
        # explota acá con un 500 (justo lo que pasó en producción).
        login(self.request, usuario, backend="django.contrib.auth.backends.ModelBackend")
        return HttpResponseRedirect(self.get_success_url())


class SolicitarRestablecerContrasenaView(auth_views.PasswordResetView):
    """Igual al PasswordResetView de Django, pero si el envío de email falla
    (credenciales SMTP mal cargadas, Gmail caído, lo que sea) NUNCA muestra
    un error 500 — honestidad ante todo: se avisa con un mensaje claro en vez
    de una pantalla rota. Esto pasó de verdad en producción con una
    contraseña de aplicación de Gmail mal configurada."""

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except smtplib.SMTPException:
            logger.exception("No se pudo enviar el email de restablecer contraseña")
            messages.error(
                self.request,
                "No pudimos enviar el email en este momento (falló el envío desde el servidor). "
                "Probá de nuevo en un rato, o contactanos directamente para que te ayudemos a entrar.",
            )
            return redirect(reverse("users:password_reset"))
