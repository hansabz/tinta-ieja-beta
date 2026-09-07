"""Reglas de negocio del sistema de citas: todo lo que decide si una sesión se
puede agendar o no vive acá (no en las vistas ni en el admin), para que la
misma regla valga tanto si la reserva la hace un cliente desde la web como si
la carga un empleado a mano desde /admin.

Los números (tope mensual, umbral de "día muy largo", etc.) se leen siempre de
ConfiguracionEstudio — nunca están fijos en el código.
"""

from django.core.files.base import ContentFile
from django.utils import timezone

from apps.studio.models import ConfiguracionEstudio
from services.whatsapp import link_whatsapp

from .models import Cita, EstadoCita, EstadoSesion, SesionCita


class ConflictoDeHorario(Exception):
    """Se lanza cuando una sesión nueva pisa una regla de agenda del tatuador."""


def _rango_mes(fecha):
    inicio_mes = fecha.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if inicio_mes.month == 12:
        fin_mes = inicio_mes.replace(year=inicio_mes.year + 1, month=1)
    else:
        fin_mes = inicio_mes.replace(month=inicio_mes.month + 1)
    return inicio_mes, fin_mes


def sesiones_activas_del_tatuador(tatuador, excluir_sesion_id=None):
    qs = SesionCita.objects.filter(
        cita__tatuador=tatuador
    ).exclude(estado=EstadoSesion.CANCELADA)
    if excluir_sesion_id:
        qs = qs.exclude(pk=excluir_sesion_id)
    return qs


def validar_nueva_sesion(tatuador, inicio, duracion_minutos, excluir_sesion_id=None):
    """Lanza ConflictoDeHorario si la sesión propuesta no se puede agendar.
    Si `tatuador` es None (cliente no eligió a nadie), no hay agenda que
    validar — la asignación real la hace el gerente después."""
    if tatuador is None:
        return

    config = ConfiguracionEstudio.obtener()
    fin_propuesto = inicio + timezone.timedelta(minutes=duracion_minutos)
    activas = sesiones_activas_del_tatuador(tatuador, excluir_sesion_id)

    # 1) Tope de sesiones por mes calendario.
    inicio_mes, fin_mes = _rango_mes(inicio)
    del_mes = activas.filter(inicio__gte=inicio_mes, inicio__lt=fin_mes).count()
    if del_mes >= config.max_citas_por_tatuador_mes:
        raise ConflictoDeHorario(
            f"{tatuador} ya tiene {del_mes} sesiones agendadas ese mes "
            f"(máximo {config.max_citas_por_tatuador_mes})."
        )

    # 2) Choque de horario ese mismo día + regla de "día ya muy largo".
    del_dia = activas.filter(inicio__date=inicio.date())
    for sesion in del_dia:
        se_pisan = inicio < sesion.fin and sesion.inicio < fin_propuesto
        if se_pisan:
            raise ConflictoDeHorario("Ese horario se pisa con otra sesión ya agendada.")
        dia_ya_muy_largo = sesion.duracion_minutos > config.umbral_cita_larga_minutos
        nueva_muy_larga = duracion_minutos > config.umbral_cita_larga_minutos
        if dia_ya_muy_largo or nueva_muy_larga:
            raise ConflictoDeHorario(
                "Ese día ya tiene una sesión larga agendada — no se puede sumar otra."
            )


def horas_disponibles(tatuador, fecha, duracion_minutos, hora_apertura=10, hora_cierre=19, paso_minutos=60):
    """Franjas horarias candidatas para `fecha` que no violan validar_nueva_sesion.
    Uso simple (no calcula huecos exactos entre citas): prueba una franja cada
    `paso_minutos` dentro del horario del estudio y descarta las que chocan."""
    disponibles = []
    cursor = timezone.datetime.combine(fecha, timezone.datetime.min.time(), tzinfo=timezone.get_current_timezone())
    cursor = cursor.replace(hour=hora_apertura)
    limite = cursor.replace(hour=hora_cierre)
    while cursor + timezone.timedelta(minutes=duracion_minutos) <= limite:
        try:
            validar_nueva_sesion(tatuador, cursor, duracion_minutos)
            disponibles.append(cursor)
        except ConflictoDeHorario:
            pass
        cursor += timezone.timedelta(minutes=paso_minutos)
    return disponibles


def link_notificacion_cita(cita):
    """Devuelve el link de WhatsApp para avisar de la reserva: al tatuador
    elegido si tiene número cargado, o al WhatsApp general del estudio (el
    gerente) si no se eligió a nadie o no tiene número."""
    estudio = ConfiguracionEstudio.obtener()
    mensaje = (
        f"Nueva reserva: {cita.cliente.get_full_name() or cita.cliente.username} — "
        f"{cita.numero_sesiones} sesión(es)."
    )
    if cita.tatuador and cita.tatuador.whatsapp:
        return link_whatsapp(cita.tatuador.whatsapp, mensaje)
    return link_whatsapp(estudio.whatsapp_general, mensaje)


def publicar_en_portafolio(cita, titulo, descripcion=""):
    """Copia la foto de resultado de la cita a una Obra nueva del portafolio del
    tatuador. Copia el ARCHIVO (no solo la referencia) para que la limpieza
    automática del historial de citas, un mes después, pueda borrar la foto
    original sin afectar la que ya quedó publicada."""
    from apps.gallery.models import Obra

    if not cita.foto_resultado:
        raise ValueError("Esta cita no tiene foto de resultado para publicar.")
    if not cita.tatuador:
        raise ValueError("Esta cita no tiene un tatuador asignado.")
    if not cita.estilo:
        raise ValueError("Elegí un estilo para poder publicarla en el portafolio.")
    if cita.resultado_publicado_portafolio:
        return cita.obra_publicada

    contenido = ContentFile(cita.foto_resultado.read())
    nombre_archivo = cita.foto_resultado.name.rsplit("/", 1)[-1]

    obra = Obra(artista=cita.tatuador, estilo=cita.estilo, titulo=titulo, descripcion=descripcion)
    obra.imagen.save(nombre_archivo, contenido, save=True)

    cita.obra_publicada = obra
    cita.resultado_publicado_portafolio = True
    cita.save(update_fields=["obra_publicada", "resultado_publicado_portafolio"])
    return obra


def finalizar_cita(cita):
    """Cierra la cita YA (el tatuador terminó antes de agotar las sesiones que
    tenía programadas, ver requerimiento de finalización manual). Libera del
    calendario cualquier sesión futura que ya no va a pasar, para que no siga
    contando contra el tope mensual del tatuador."""
    ahora = timezone.now()
    cita.estado = EstadoCita.TERMINADA
    if not cita.fecha_finalizada:
        cita.fecha_finalizada = ahora
    cita.save(update_fields=["estado", "fecha_finalizada"])

    cita.sesiones.filter(estado=EstadoSesion.PENDIENTE, inicio__gt=ahora).update(
        estado=EstadoSesion.CANCELADA
    )
    cita.sesiones.filter(estado=EstadoSesion.PENDIENTE, inicio__lte=ahora).update(
        estado=EstadoSesion.REALIZADA
    )


def limpiar_historial_vencido():
    """Borra las citas TERMINADA cuyo mes de gracia ya pasó (ver
    ConfiguracionEstudio.dias_retencion_historial_citas). La foto de resultado
    se borra sola vía la señal post_delete (ver signals.py) — salvo que ya
    esté publicada en el portafolio, en cuyo caso esa copia vive en Obra y no
    se toca. Se llama sola desde las vistas de citas (ver views.py) además de
    poder correrse a mano con el comando de gestión."""
    config = ConfiguracionEstudio.obtener()
    vencidas = [
        c for c in Cita.objects.filter(estado=EstadoCita.TERMINADA, fecha_finalizada__isnull=False)
        if c.vencida_para_historial(config.dias_retencion_historial_citas)
    ]
    total = len(vencidas)
    for cita in vencidas:
        cita.delete()
    return total
