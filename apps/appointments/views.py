"""Vistas del sistema de citas.

Desde que el estudio decidió que los EMPLEADOS son quienes cargan las
reservas (no el cliente por su cuenta), "reservar" y sus endpoints de apoyo
(buscar horarios, buscar cliente) son solo para staff — ver `_es_staff`.
"mis_citas" sigue siendo del cliente: ahí ve el estado de sus citas y la
foto de resultado, aunque no las haya cargado él mismo.

Todo lo que hace el EMPLEADO/tatuador para CERRAR una cita (marcar
terminada, subir la foto de resultado, publicarla en el portafolio, borrar
del historial) vive en apps/appointments/admin.py, no acá.
"""

from datetime import datetime

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET
from django_ratelimit.decorators import ratelimit

from .forms import ReservaForm
from .models import Cita, EstadoSesion, SesionCita
from .services import (
    ConflictoDeHorario,
    horas_disponibles,
    limpiar_historial_vencido,
    link_notificacion_cita,
    validar_nueva_sesion,
)

Usuario = get_user_model()


def _es_staff(usuario):
    return usuario.is_authenticated and usuario.is_staff


# Todas las vistas de esta sección (menos mis_citas) requieren estar logueado
# Y ser staff — el cliente ya no reserva por su cuenta (ver el chat/WhatsApp/
# formulario de contacto para eso). login_url manda a la pantalla normal de
# login en vez de a la de /admin, que es más agresiva y no forma parte del
# resto del sitio.
staff_required = user_passes_test(_es_staff, login_url="users:login")


@staff_required
def reservar(request):
    form = ReservaForm(request.POST or None, usuario=request.user)
    cliente_seleccionado = None
    cliente_id = request.POST.get("cliente_id") or request.GET.get("cliente_id")
    if cliente_id:
        cliente_seleccionado = Usuario.objects.filter(pk=cliente_id, rol="CLIENTE").first()

    if request.method == "POST" and form.is_valid():
        numero_sesiones = form.cleaned_data["numero_sesiones"]
        tatuador = form.cleaned_data["tatuador"]
        from apps.studio.models import ConfiguracionEstudio

        config = ConfiguracionEstudio.obtener()
        duracion = config.duracion_sesion_minutos_default

        errores = []
        if cliente_seleccionado is None:
            errores.append("Elegí para qué cliente es la reserva (buscalo arriba y seleccionalo).")

        # Cada sesión llega como un campo oculto "sesion_1_inicio", "sesion_2_inicio", ...
        # con un ISO datetime elegido en el calendario (ver template + JS).
        horarios = []
        for n in range(1, numero_sesiones + 1):
            crudo = request.POST.get(f"sesion_{n}_inicio")
            if not crudo:
                errores.append(f"Falta elegir el horario de la sesión {n}.")
                continue
            try:
                inicio = datetime.fromisoformat(crudo)
                if timezone.is_naive(inicio):
                    inicio = timezone.make_aware(inicio)
            except ValueError:
                errores.append(f"El horario de la sesión {n} no es válido.")
                continue
            horarios.append(inicio)

        if not errores:
            try:
                with transaction.atomic():
                    # Se valida también contra las sesiones nuevas entre sí (no solo contra
                    # lo que ya hay en la base) para que no se pisen dentro de la misma reserva.
                    provisorias = []
                    for inicio in horarios:
                        validar_nueva_sesion(tatuador, inicio, duracion)
                        for otro_inicio in provisorias:
                            # Comparar en hora local, no en UTC (ver el comentario
                            # en services._rango_mes sobre por qué importa).
                            if timezone.localtime(inicio).date() == timezone.localtime(otro_inicio).date():
                                raise ConflictoDeHorario(
                                    "Dos sesiones de esta misma reserva no pueden coincidir el mismo día."
                                )
                        provisorias.append(inicio)

                    cita = Cita.objects.create(
                        cliente=cliente_seleccionado,
                        tatuador=tatuador,
                        estilo=form.cleaned_data["estilo"],
                        numero_sesiones=numero_sesiones,
                        notas=form.cleaned_data["notas"],
                    )
                    for i, inicio in enumerate(horarios, start=1):
                        SesionCita.objects.create(
                            cita=cita, numero=i, inicio=inicio, duracion_minutos=duracion
                        )
                return redirect(reverse("appointments:confirmacion", args=[cita.pk]))
            except ConflictoDeHorario as exc:
                errores.append(str(exc))

        for error in errores:
            messages.error(request, error)

    hoy = timezone.localdate()
    from apps.studio.models import ConfiguracionEstudio

    limite = hoy + timezone.timedelta(days=ConfiguracionEstudio.obtener().horizonte_reserva_dias)
    return render(
        request,
        "appointments/reservar.html",
        {
            "form": form,
            "hoy": hoy.isoformat(),
            "limite": limite.isoformat(),
            "cliente_seleccionado": cliente_seleccionado,
        },
    )


@staff_required
@require_GET
@ratelimit(key="ip", rate="30/m", method="GET", block=True)
def buscar_clientes(request):
    """Endpoint de búsqueda para elegir a quién es la cita — ver reservar.html."""
    q = (request.GET.get("q") or "").strip()
    clientes = None
    if len(q) >= 2:
        clientes = list(
            Usuario.objects.filter(rol="CLIENTE")
            .filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q))
            .order_by("first_name", "last_name")[:8]
        )
    return render(request, "appointments/_clientes.html", {"clientes": clientes})


@staff_required
def confirmacion(request, pk):
    cita = Cita.objects.select_related("cliente", "tatuador__usuario", "estilo").prefetch_related("sesiones").get(
        pk=pk
    )
    return render(
        request,
        "appointments/confirmacion.html",
        {"cita": cita, "whatsapp_link": link_notificacion_cita(cita)},
    )


@login_required
def mis_citas(request):
    # A diferencia de las vistas de arriba, esta SÍ es para cualquier cliente
    # logueado: ver el estado de sus citas y la foto de resultado no cambió,
    # aunque ahora la reserva la haya cargado un empleado y no él mismo.
    limpiar_historial_vencido()
    citas = (
        Cita.objects.filter(cliente=request.user)
        .select_related("tatuador__usuario", "estilo")
        .prefetch_related("sesiones")
    )
    return render(request, "appointments/mis_citas.html", {"citas": citas})


@staff_required
@require_GET
@ratelimit(key="ip", rate="30/m", method="GET", block=True)
def horarios_partial(request):
    """Endpoint de apoyo: dado un tatuador y una fecha, devuelve los horarios
    disponibles ese día como botones para el formulario de reserva."""
    from apps.artists.models import Empleado

    sesion_n = request.GET.get("sesion", "1")
    fecha_str = request.GET.get("fecha", "")
    tatuador_id = request.GET.get("tatuador", "")

    from apps.studio.models import ConfiguracionEstudio

    duracion = ConfiguracionEstudio.obtener().duracion_sesion_minutos_default

    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        return render(request, "appointments/_horarios.html", {"horarios": [], "sesion_n": sesion_n})

    tatuador = Empleado.objects.filter(pk=tatuador_id).first() if tatuador_id else None
    horarios = horas_disponibles(tatuador, fecha, duracion) if tatuador else []
    return render(request, "appointments/_horarios.html", {"horarios": horarios, "sesion_n": sesion_n})
