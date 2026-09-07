from django import forms

from apps.artists.models import Empleado
from apps.gallery.models import Estilo
from apps.studio.models import ConfiguracionEstudio


class ReservaForm(forms.Form):
    """Datos generales de la reserva (no incluye los horarios de cada sesión —
    esos se validan aparte en la vista contra el calendario real, ver
    views.py y services.validar_nueva_sesion)."""

    tatuador = forms.ModelChoiceField(
        queryset=Empleado.objects.filter(es_artista=True, activo=True),
        required=False,
        empty_label="No tengo preferencia (decide el estudio)",
    )
    estilo = forms.ModelChoiceField(queryset=Estilo.objects.all(), required=False, empty_label="A definir")
    numero_sesiones = forms.IntegerField(min_value=1, initial=1)
    notas = forms.CharField(widget=forms.Textarea, required=False, label="Contános tu idea")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = ConfiguracionEstudio.obtener()
        self.fields["numero_sesiones"].max_value = self.config.max_sesiones_por_cita
        self.fields["numero_sesiones"].widget = forms.Select(
            choices=[(n, n) for n in range(1, self.config.max_sesiones_por_cita + 1)]
        )

    def clean_numero_sesiones(self):
        valor = self.cleaned_data["numero_sesiones"]
        if valor > self.config.max_sesiones_por_cita:
            raise forms.ValidationError(
                f"El máximo de sesiones permitido es {self.config.max_sesiones_por_cita}."
            )
        return valor
