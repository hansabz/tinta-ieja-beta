from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Usuario


class RegistroForm(UserCreationForm):
    """Formulario de registro público.

    Deliberadamente NO incluye un campo de rol: el modelo Usuario define
    rol=CLIENTE por defecto, y la vista de registro nunca lee ni asigna un rol
    a partir de datos enviados por el cliente. Ver apps.users.views.RegistroView.
    """

    email = forms.EmailField(required=True)

    class Meta:
        model = Usuario
        fields = ("username", "email")
