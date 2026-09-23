from django.urls import path

from . import views

app_name = "legal"

urlpatterns = [
    path("<str:tipo>/", views.DocumentoLegalView.as_view(), name="documento"),
]
