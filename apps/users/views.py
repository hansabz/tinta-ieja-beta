from django.contrib.auth import login
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import RegistroForm
from .models import Cliente, Rol


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
