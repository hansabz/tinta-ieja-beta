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
        login(self.request, usuario)
        return HttpResponseRedirect(self.get_success_url())
