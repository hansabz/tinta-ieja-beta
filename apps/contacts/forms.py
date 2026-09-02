from django import forms


class SolicitudContactoForm(forms.Form):
    nombre_contacto = forms.CharField(max_length=120, required=False, label="Tu nombre")
    contacto = forms.CharField(max_length=120, required=False, label="Tu email o teléfono")
    motivo = forms.CharField(
        max_length=1000,
        widget=forms.Textarea,
        label="Contanos brevemente tu idea",
    )

    def __init__(self, *args, usuario_autenticado=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario_autenticado = usuario_autenticado

    def clean(self):
        cleaned = super().clean()
        if not self.usuario_autenticado:
            if not cleaned.get("nombre_contacto"):
                self.add_error("nombre_contacto", "Necesitamos tu nombre para poder responderte.")
            if not cleaned.get("contacto"):
                self.add_error("contacto", "Dejanos un email o teléfono para poder responderte.")
        return cleaned
