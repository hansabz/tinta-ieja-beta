"""Panel de citas en /admin.

Reglas de permisos (ver el requerimiento original):
- El gerente/administrador (rol ADMINISTRADOR o is_superuser) ve y gestiona todas
  las citas, y es el ÚNICO que puede borrarlas del historial a mano.
- Un empleado/tatuador (rol EMPLEADO) solo ve y gestiona SUS PROPIAS citas
  (donde tatuador.usuario == el empleado logueado) y nunca puede borrar nada
  — ni las suyas ni las de otro. Puede marcarlas como terminadas, subir la
  foto de resultado y decidir si la publica en su portafolio.
"""

from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path

from .excel import exportar_citas_excel, importar_citas_excel
from .models import Cita, SesionCita
from .services import finalizar_cita, publicar_en_portafolio


def _es_admin(user):
    return user.is_superuser or getattr(user, "rol", None) == "ADMINISTRADOR"


def _empleado_de(user):
    return getattr(user, "empleado", None)


class SesionCitaInline(admin.TabularInline):
    model = SesionCita
    extra = 0
    fields = ("numero", "inicio", "duracion_minutos", "estado")


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = (
        "cliente", "tatuador", "proxima_fecha", "costo",
        "duracion_total_minutos", "numero_sesiones", "estado",
    )
    list_filter = ("estado", "tatuador", "estilo")
    search_fields = ("cliente__username", "cliente__first_name", "cliente__last_name")
    autocomplete_fields = ("cliente", "tatuador", "estilo")
    readonly_fields = ("creada", "resultado_publicado_portafolio", "obra_publicada")
    inlines = [SesionCitaInline]
    actions = ["accion_marcar_terminada", "accion_publicar_en_portafolio", "accion_exportar_excel"]
    change_list_template = "admin/appointments/cita/change_list.html"

    @admin.display(description="Fecha (próxima sesión)")
    def proxima_fecha(self, obj):
        sesion = obj.proxima_sesion or obj.sesiones.order_by("-inicio").first()
        return sesion.inicio if sesion else "—"

    # --- Visibilidad: cada empleado solo ve sus propias citas ---------------
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if _es_admin(request.user):
            return qs
        empleado = _empleado_de(request.user)
        return qs.filter(tatuador=empleado) if empleado else qs.none()

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_staff

    def has_view_permission(self, request, obj=None):
        if not (request.user.is_active and request.user.is_staff):
            return False
        if obj is None or _es_admin(request.user):
            return True
        return obj.tatuador_id == getattr(_empleado_de(request.user), "pk", None)

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    def has_add_permission(self, request):
        # Las citas nacen del formulario público de reserva o las carga el
        # gerente a mano; un empleado no crea citas propias desde acá.
        return _es_admin(request.user)

    def has_delete_permission(self, request, obj=None):
        # Regla explícita del estudio: nunca un empleado, sea cual sea el estado.
        return _es_admin(request.user)

    def get_readonly_fields(self, request, obj=None):
        base = list(self.readonly_fields)
        if _es_admin(request.user):
            return base
        # Un empleado solo puede tocar el resultado del trabajo, no reasignar
        # la cita ni cambiar cliente/tatuador/costo.
        return base + ["cliente", "tatuador", "estilo", "numero_sesiones", "costo"]

    # --- Excel: exportar todas / importar (solo administrador) --------------
    def get_urls(self):
        urls = [
            path(
                "importar-excel/",
                self.admin_site.admin_view(self.importar_excel_view),
                name="appointments_cita_importar_excel",
            ),
        ]
        return urls + super().get_urls()

    def importar_excel_view(self, request):
        if not _es_admin(request.user):
            self.message_user(request, "Solo el administrador puede importar citas.", messages.ERROR)
            return redirect("admin:appointments_cita_changelist")

        resumen = None
        if request.method == "POST" and request.FILES.get("archivo"):
            resumen = importar_citas_excel(request.FILES["archivo"])
            if resumen["creadas"] or resumen["actualizadas"]:
                self.message_user(
                    request,
                    f"Importación lista: {resumen['creadas']} cita(s) creadas, "
                    f"{resumen['actualizadas']} actualizadas.",
                    messages.SUCCESS,
                )
            for error in resumen["errores"]:
                self.message_user(request, error, messages.WARNING)
            if not resumen["errores"]:
                return redirect("admin:appointments_cita_changelist")

        return render(
            request,
            "admin/appointments/cita/importar.html",
            {**self.admin_site.each_context(request), "resumen": resumen, "opts": self.model._meta},
        )

    @admin.action(description="Exportar seleccionadas a Excel")
    def accion_exportar_excel(self, request, queryset):
        return exportar_citas_excel(queryset)

    # --- Otras acciones ---------------------------------------------------
    @admin.action(description="Marcar como terminada (libera sesiones futuras)")
    def accion_marcar_terminada(self, request, queryset):
        for cita in queryset:
            finalizar_cita(cita)
        self.message_user(request, f"{queryset.count()} cita(s) marcadas como terminadas.", messages.SUCCESS)

    @admin.action(description="Publicar foto de resultado en el portafolio del tatuador")
    def accion_publicar_en_portafolio(self, request, queryset):
        publicadas, fallidas = 0, []
        for cita in queryset:
            try:
                titulo = f"Tatuaje de {cita.cliente.get_full_name() or cita.cliente.username}"
                publicar_en_portafolio(cita, titulo=titulo)
                publicadas += 1
            except ValueError as exc:
                fallidas.append(f"{cita}: {exc}")
        if publicadas:
            self.message_user(request, f"{publicadas} foto(s) publicadas en el portafolio.", messages.SUCCESS)
        for error in fallidas:
            self.message_user(request, error, messages.WARNING)
