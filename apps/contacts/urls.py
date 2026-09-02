from django.urls import path

from . import views

app_name = "contacts"

urlpatterns = [
    path("solicitud/", views.crear_solicitud, name="crear_solicitud"),
]
