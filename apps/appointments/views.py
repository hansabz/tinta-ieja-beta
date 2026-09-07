"""Vistas del sistema de citas para el CLIENTE (reservar y ver las propias).

Todo lo que hace el EMPLEADO/tatuador (marcar terminada, subir la foto de
resultado, publicarla en el portafolio, borrar del historial) vive en
apps/appointments/admin.py — se maneja desde /admin, como pidió el estudio,
no acá.
"""

from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET
from django_ratelimit.decorators import ratelimit

from .forms import ReservaForm
from .models import Cita, EstadoSesion, SesionCita
from .services import ConflictoDeHorario, horas_disponibles, limpiar_historial_vencido, link_notificacion_cita, validar_nueva_sesion


@login_required
def reservar(request):
    form = ReservaForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        numero_sesiones = form.cleaned_data["numero_sesiones"]
        tatuador = form.cleaned_data["tatuador"]
        from apps.studio.models import ConfiguracionEstudio

        config = ConfiguracionEstudio.obtener()
        duracion = config.duracion_sesion_minutos_default

        # Cada sesión llega como un campo oculto "sesion_1_inicio", "sesion_2_inicio", ...
        # con un ISO datetime elegido en el calendario (ver template + JS).
        horarios = []
        errores = []
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
                            if inicio.date() == otro_inicio.date():
                                raise ConflictoDeHorario(
                                    "Dos sesiones de esta misma reserva no pueden coincidir el mismo día."
                                )
                        provisorias.append(inicio)

                    cita = Cita.objects.create(
                        cliente=request.user,
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

    return render(
        request,
        "appointments/reservar.html",
        {"form": form, "hoy": timezone.localdate().isoformat()},
    )


@login_required
def confirmacion(request, pk):
    cita = Cita.objects.select_related("tatuador__usuario", "estilo").prefetch_related("sesiones").get(
        pk=pk, cliente=request.user
    )
    return render(
        request,
        "appointments/confirmacion.html",
        {"cita": cita, "whatsapp_link": link_notificacion_cita(cita)},
    )


@login_required
def mis_citas(request):
    limpiar_historial_vencido()
    citas = (
        Cita.objects.filter(cliente=request.user)
        .select_related("tatuador__usuario", "estilo")
        .prefetch_related("sesiones")
    )
    return render(request, "appointments/mis_citas.html", {"citas": citas})


@login_required
@require_GET
@ratelimit(key="ip", rate="30/m", method="GET", block=True)
def horarios_partial(request):
    """Endpoint HTMX: dado un tatuador (opcional) y una fecha, devuelve los
    horarios disponibles ese día como botones de radio para el formulario."""
    from apps.artists.models import Empleado
    from apps.studio.models import ConfiguracionEstudio

    sesion_n = request.GET.get("sesion", "1")
    fecha_str = request.GET.get("fecha", "")
    tatuador_id = request.GET.get("tatuador", "")

    config = ConfiguracionEstudio.obtener()
    duracion = config.duracion_sesion_minutos_default

    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        return render(request, "appointments/_horarios.html", {"horarios": [], "sesion_n": sesion_n})

    tatuador = None
    if tatuador_id:
        tatuador = Empleado.objects.filter(pk=tatuador_id).first()

    horarios = horas_disponibles(tatuador, fecha, duracion) if tatuador else _horarios_libres_estudio(fecha, duracion)
    return render(
        request,
        "appointments/_horarios.html",
        {"horarios": horarios, "sesion_n": sesion_n},
    )


def _horarios_libres_estudio(fecha, duracion, hora_apertura=10, hora_cierre=19, paso_minutos=60):
    """Cuando el cliente no eligió tatuador, se muestran todas las franjas del
    horario de atención — la asignación real de tatuador la hace el estudio
    después de recibir el aviso por WhatsApp."""
    cursor = timezone.datetime.combine(fecha, timezone.datetime.min.time(), tzinfo=timezone.get_current_timezone())
    cursor = cursor.replace(hour=hora_apertura)
    limite = cursor.replace(hour=hora_cierre)
    horarios = []
    while cursor + timezone.timedelta(minutes=duracion) <= limite:
        horarios.append(cursor)
        cursor += timezone.timedelta(minutes=paso_minutos)
    return horarios
