from django import forms

from apps.artists.models import Empleado
from apps.gallery.models import Estilo
from apps.studio.models import ConfiguracionEstudio


class ReservaForm(forms.Form):
    """Datos generales de la reserva. La carga un EMPLEADO o el
    ADMINISTRADOR (ver views.reservar) — no el cliente: el tatuador es
    obligatorio y, si quien reserva es un empleado, queda fijado a sí mismo
    (no puede agendar en la agenda de otro tatuador). El cliente para el que
    es la reserva no es un campo de este Form — se busca y se elige aparte
    (ver el buscador en el template) y se valida a mano en la vista, igual
    que los horarios de cada sesión."""

    tatuador = forms.ModelChoiceField(queryset=Empleado.objects.filter(es_artista=True, activo=True))
    estilo = forms.ModelChoiceField(queryset=Estilo.objects.all(), required=False, empty_label="A definir")
    numero_sesiones = forms.IntegerField(min_value=1, initial=1)
    notas = forms.CharField(widget=forms.Textarea, required=False, label="Notas / idea del tatuaje")

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = ConfiguracionEstudio.obtener()
        self.fields["numero_sesiones"].max_value = self.config.max_sesiones_por_cita
        self.fields["numero_sesiones"].widget = forms.Select(
            choices=[(n, n) for n in range(1, self.config.max_sesiones_por_cita + 1)]
        )

        # Un empleado (no administrador) solo puede reservar para sí mismo —
        # se le oculta la posibilidad de elegir a otro tatuador.
        empleado_propio = getattr(usuario, "empleado", None) if usuario else None
        es_admin = bool(usuario and (usuario.is_superuser or usuario.rol == "ADMINISTRADOR"))
        if empleado_propio and not es_admin:
            self.fields["tatuador"].queryset = Empleado.objects.filter(pk=empleado_propio.pk)
            self.fields["tatuador"].initial = empleado_propio.pk
            self.fields["tatuador"].disabled = True

    def clean_numero_sesiones(self):
        valor = self.cleaned_data["numero_sesiones"]
        if valor > self.config.max_sesiones_por_cita:
            raise forms.ValidationError(
                f"El máximo de sesiones permitido es {self.config.max_sesiones_por_cita}."
            )
        return valor
