from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from .models import DocumentoLegal


class DocumentoLegalView(DetailView):
    model = DocumentoLegal
    template_name = "legal/documento.html"
    context_object_name = "documento"

    def get_object(self, queryset=None):
        return get_object_or_404(DocumentoLegal, tipo=self.kwargs["tipo"])
