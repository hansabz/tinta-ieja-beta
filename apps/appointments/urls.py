from django.urls import path

from . import views

app_name = "appointments"

urlpatterns = [
    path("reservar/", views.reservar, name="reservar"),
    path("reservar/horarios/", views.horarios_partial, name="horarios_partial"),
    path("reservar/clientes/", views.buscar_clientes, name="buscar_clientes"),
    path("confirmacion/<int:pk>/", views.confirmacion, name="confirmacion"),
    path("mis-citas/", views.mis_citas, name="mis_citas"),
]
