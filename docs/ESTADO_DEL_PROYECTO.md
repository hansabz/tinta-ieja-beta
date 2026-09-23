# Estado del proyecto — Tinta Vieja (beta)

> Documento de continuidad: leelo completo antes de retomar trabajo en una
> conversación nueva. Complementa a `AGENTS.md` (reglas y gotchas para
> cualquier agente de IA que toque el código) y a
> `docs/Tinta_Vieja_Documentacion.docx` (manual para el gerente/usuario final).
> Última actualización: después de agregar `apps/legal/` (documentos
> legales + aviso de cookies), commit siguiente a `88d098e`.

---

## 1. Objetivo actual del proyecto

Beta funcional de un sitio web real para un estudio de tatuajes ("Tinta
Vieja" — nombre y datos de ejemplo, a reemplazar antes de un lanzamiento
real). Construida con Django, 100% en infraestructura gratuita (Render +
Neon + Backblaze B2), para que el dueño/gerente del estudio y sus empleados
puedan:

- Mostrar el portafolio y el equipo al público sin que nadie necesite login.
- Gestionar la agenda de citas ellos mismos (no el cliente por su cuenta).
- Atender consultas simples con un chatbot de IA restringido al estudio.
- Administrar todo el contenido (fotos, precios, config) desde `/admin`,
  sin tocar código.

El proyecto está en etapa de **prueba/beta con datos de ejemplo** — todavía
no es el sitio real del estudio (ver sección 3, pendientes).

---

## 2. Funcionalidades ya implementadas

### Sitio público
- Home conectada 100% a datos reales de la base (nada hardcodeado): estilos,
  artistas, portafolio (últimas 6 obras), cuidados post-tatuaje, contacto.
- **Galería completa** (`/galeria/`) con filtro por estilo y por artista,
  paginada.
- Chatbot con IA (botón flotante + widget), con 3 "chips" de sugerencia en
  la vista previa de la home que abren el chat real con una pregunta
  precargada.
- Formulario de contacto (crea una `SolicitudContacto`, rate-limited).
- **Documentos legales** (`/legal/`): Política de privacidad, Términos y
  condiciones, Términos del servicio de tatuaje y Política de cookies —
  las 4 páginas, con un texto modelo real (no placeholder vacío),
  enlazadas desde el footer.
- **Aviso de cookies** (banner fijo abajo, en todas las páginas): explica
  que solo se usan cookies esenciales, botones Aceptar/Rechazar, guarda la
  preferencia en `localStorage` (nunca en el servidor).

### Cuentas y seguridad
- Registro público — **siempre** crea `rol=CLIENTE`, nunca staff/superuser
  (verificado con test, sin importar qué mande el formulario).
- Login con usuario/contraseña.
- **Login con Google activo y funcionando** (probado de punta a punta con
  una cuenta real) — misma regla: fuerza CLIENTE siempre.
- **Restablecer contraseña** self-service ("¿Olvidaste tu contraseña?"),
  probado con cliente, empleado y administrador.
- Regla explícita: **solo el superusuario puede cambiarle la contraseña a
  otra persona desde `/admin`, y nunca a un cliente** (un cliente usa el
  restablecimiento de arriba). Verificado con tests y a mano en producción.
- `/admin` nunca tiene ningún link visible desde la navegación pública.

### Sistema de citas (`apps/appointments`)
- **Las reservas las carga un empleado (para sí mismo) o el administrador
  (para cualquier tatuador) — el cliente ya no reserva por su cuenta.**
  Un cliente que quiere un turno escribe por chat/WhatsApp/contacto.
- Calendario real: nunca se puede elegir un horario ya ocupado.
- Reglas de negocio, todas configurables desde `/admin` → Configuración del
  estudio (nunca hardcodeadas):
  - Máximo de sesiones por tatuaje (`max_sesiones_por_cita`, default 6)
  - Tope de sesiones por mes por tatuador (`max_citas_por_tatuador_mes`,
    default 3)
  - Umbral de "día ya muy largo" que bloquea otra sesión ese día
    (`umbral_cita_larga_minutos`, default 240 min)
  - Duración por defecto de una sesión (`duracion_sesion_minutos_default`,
    default 240 min)
  - Horizonte de reserva: nunca en el pasado, nunca más allá de
    (`horizonte_reserva_dias`, default 90 días / ~3 meses)
  - Días que una cita terminada queda en el historial antes de borrarse
    sola (`dias_retencion_historial_citas`, default 30)
- Buscador de cliente (por nombre/usuario) al cargar una reserva.
- Finalizar una cita antes de agotar las sesiones programadas (libera el
  calendario).
- Foto de resultado subida por el tatuador (desde la compu, no URL) — el
  cliente la ve con "Ver resultado" en "Mis citas". Publicarla al
  portafolio COPIA el archivo (no se pierde si la cita se borra del
  historial).
- Historial con auto-limpieza (lazy, sin necesitar cron pago) — **solo
  administrador/superusuario puede borrar del historial a mano, nunca un
  empleado.**
- Exportar/importar citas a Excel (hoja "Citas" editable en lote, hoja
  "Sesiones" solo informativa — a propósito no se pueden crear/mover
  horarios por Excel).

### Panel `/admin`
- Encabezado y colores con la marca del estudio (no el azul genérico de
  Django).
- Apps reordenadas: lo que se usa seguido (Citas, Config del estudio,
  Artistas) arriba; modelos técnicos (Groups, Sites, tokens de Google)
  ocultos del menú.
- Alta de usuario en **una sola pantalla**: nombre de cuenta, nombre
  visible, rol, y el perfil de empleado/cliente correspondiente — ya no se
  puede terminar con una cuenta a medio configurar.
- Validación: un usuario **nunca** puede tener perfil de Cliente y de
  Empleado a la vez (ni siquiera cargando los dos en la misma pantalla).
- Botón "+ Cargar reserva" en el listado de Citas.

### Configuración del estudio
- Foto de portada de la home (se sube desde la compu).
- Instagram/TikTok (campos de texto simples, ya no JSON).
- Cuidados post-tatuaje — ahora se muestra de verdad en la home (antes el
  link del footer no llevaba a ningún lado).
- WhatsApp general, teléfono, dirección, horarios, políticas (este último
  campo existe pero todavía no se muestra en ningún lado del sitio público).

### Infraestructura
- Hosting: Render (free) — auto-deploy en cada push a `main`.
- Base de datos: Neon (Postgres).
- Imágenes: Backblaze B2 (S3-compatible, bucket privado).
- Email saliente: SMTP (Gmail con contraseña de aplicación) — con
  `EMAIL_TIMEOUT` para que una conexión colgada no tumbe el sitio entero.
- El dominio real (`RENDER_EXTERNAL_HOSTNAME`) se sincroniza solo en cada
  deploy (`sincronizar_site`, corrido desde `build.sh`) — arregla los links
  de Google login y de restablecer contraseña automáticamente.

---

## 3. Funcionalidades pendientes / incompletas

- **`whatsapp_general` todavía tiene el número de ejemplo `5491100000000`**
  — el chatbot se lo está dando a cualquiera que lo pida. Hay que cargar el
  real en `/admin` → Configuración del estudio.
- Los 3 empleados de ejemplo (`mora.ibanez`, `facu.rearte`, `kenji.suzuki`)
  **no tienen email cargado** — no pueden usar "olvidé mi contraseña" hasta
  que se les cargue uno.
- El email de restablecer contraseña sale con el **Gmail personal** del
  usuario como remitente (`hansalv2710@gmail.com`) — se sugirió crear una
  cuenta dedicada al estudio antes de un lanzamiento real, todavía no se
  hizo.
- Campo **"Políticas"** existe en el modelo y lo usa el chatbot, pero no
  se muestra en ningún lado del sitio público (a diferencia de "Cuidados",
  que ya se conectó). Está vacío en producción — no urge, pero si se carga
  contenido ahí, falta construir la sección visual (mismo patrón que
  "Cuidados").
- Login con Google **solo existe en el sitio público**, no en `/admin`
  — decisión consciente (ver sección 5), no un bug.
- Todos los datos siguen siendo de ejemplo: nombre del estudio, dirección,
  horarios, artistas, teléfono — hay que reemplazarlos antes de un
  lanzamiento real.
- Nada de esto tiene plan pago todavía — limitaciones del free tier
  siguen activas (Render se duerme sin tráfico, límites de Neon/Backblaze).
- Los 4 documentos legales (`/legal/`) son un **modelo estándar de
  redacción**, no texto revisado por un abogado — está bien para la beta,
  pero antes de un lanzamiento comercial real conviene que un profesional
  legal los revise y los adapte al país donde opera el estudio.

---

## 4. Archivos creados y modificados en esta sesión (por área)

### Sistema de citas — `apps/appointments/` (app nueva)
`models.py` (Cita, SesionCita) · `services.py` (TODA la lógica de negocio:
`validar_nueva_sesion`, `validar_rango_de_fecha`, `finalizar_cita`,
`limpiar_historial_vencido`, `publicar_en_portafolio`,
`link_notificacion_cita`) · `views.py` (reservar, buscar_clientes,
confirmacion, mis_citas, horarios_partial — todas `staff_required` menos
`mis_citas`) · `forms.py` (ReservaForm, tatuador restringido según rol) ·
`admin.py` (permisos por rol, exportar/importar Excel, botón "Cargar
reserva") · `excel.py` (exportar_citas_excel, importar_citas_excel) ·
`urls.py` · `signals.py` (borra el archivo de foto al borrar una Cita) ·
`management/commands/limpiar_historial_citas.py` · `tests.py` (36 tests).

### Usuarios y cuentas — `apps/users/`
`adapters.py` (CustomSocialAccountAdapter — fuerza CLIENTE en login de
Google) · `admin.py` (add_fieldsets con rol+nombre, inlines
Empleado/Cliente, `user_change_password` restringido) · `urls.py`
(password_reset_*) · `views.py` (RegistroView con login() +
backend explícito, SolicitarRestablecerContrasenaView) · `models.py`
(Cliente.clean()) · `tests.py`.

### Estudio — `apps/studio/`
`models.py` (ConfiguracionEstudio: +foto, +instagram_url, +tiktok_url,
-redes_sociales, +5 campos de reglas de citas) · `admin.py` (branding
global del admin, reordenar apps, ocultar modelos técnicos) ·
`management/commands/sincronizar_site.py`.

### Galería — `apps/gallery/` (vistas nuevas)
`views.py` (GaleriaView) · `urls.py` (nuevo).

### Legal — `apps/legal/` (app nueva)
`models.py` (DocumentoLegal: 4 tipos fijos — privacidad, términos y
condiciones, términos del servicio, cookies) · `admin.py` (mismo patrón
singleton que ConfiguracionEstudio: no se puede agregar ni borrar, solo
editar el texto) · `views.py`/`urls.py` (`/legal/<tipo>/`) ·
`migrations/0002_seed_documentos.py` (crea los 4 documentos con contenido
real, no vacío) · `tests.py` (9 tests: las 4 páginas devuelven 200, 404 en
un tipo inválido, footer las enlaza, admin bloquea agregar/borrar).

### Artistas — `apps/artists/`
`models.py` (Empleado.foto_url → Empleado.foto, ImageField).

### Compartido
`services/whatsapp.py` (link_whatsapp, usado por citas y chatbot) ·
`services/ai/tools.py` (actualizado: usa `link_whatsapp` compartido,
`instagram_url`/`tiktok_url` en vez de `redes_sociales`).

### Templates nuevos
`templates/appointments/*.html` (reservar, confirmacion, mis_citas,
_horarios, _clientes) · `templates/gallery/galeria.html` ·
`templates/users/password_reset_*.html` (5 archivos) ·
`templates/admin/base_site.html` (skin del admin) ·
`templates/admin/appointments/cita/*.html` (botones extra en el admin).

### Templates modificados
`templates/base.html` (nav sin "Reservar turno" ni link a /admin, footer
reconectado del todo, JS del chat refactorizado + chips conectados,
z-index del menú móvil arreglado) · `templates/studio/inicio.html` (foto
del estudio, sección "Cuidados", botón de galería conectado, chips del
chat con `data-enviar-chat`) · `templates/users/login.html` y
`registro.html` (rediseño + botón Google + link de restablecer).

### Raíz / infraestructura
`requirements.txt` (+django-allauth, +openpyxl, +PyJWT[crypto]) ·
`config/settings.py` (EMAIL_*, RENDER_EXTERNAL_HOSTNAME, STORAGES
"default" explícito, AUTHENTICATION_BACKENDS) · `build.sh` (+
`sincronizar_site` después de migrate) · `.env.example` (+ variables de
email) · `AGENTS.md` (nuevo) · `docs/Tinta_Vieja_Documentacion.docx`
(reescrito).

**Total: ~18 commits desde el baseline de la beta inicial. 49 tests
automáticos, todos pasando.**

---

## 5. Decisiones de diseño importantes (y el porqué)

| Decisión | Por qué |
|---|---|
| Las citas las carga el empleado/admin, no el cliente | Pedido explícito del gerente: menos ambigüedad, más control |
| WhatsApp Business API real descartada | Requiere verificación de negocio de Meta (días, no minutos) — se reemplazó por links wa.me + carga manual de foto de resultado |
| Login con Google fuerza SIEMPRE rol CLIENTE | Regla de seguridad — nunca se puede escalar privilegios por ese camino, ni por accidente ni a propósito |
| Login con Google solo en el sitio público | Si se agregara a `/admin`, cualquiera que se loguee con Google terminaría igual como Cliente (no tendría acceso) — no serviría para nada ahí |
| Solo superusuario cambia la clave de otro, nunca la de un cliente | Pedido explícito — un cliente siempre usa el restablecimiento self-service, es su cuenta personal |
| Reserva: máximo 90 días a futuro, nunca en el pasado | Pedido explícito: "que no se les ocurra hacer sesiones en 2050" |
| Excel: hoja "Sesiones" solo informativa | Permitir crear/mover horarios por Excel saltearía la validación de choques de horario — se mantiene ese control solo en el calendario real |
| Historial de citas se limpia solo (lazy, no cron) | Render free no tiene cron jobs — se dispara la limpieza en cada visita a las vistas de citas, sin infraestructura extra |
| Todos los números de negocio (topes, duración, horizonte) van en `ConfiguracionEstudio`, nunca hardcodeados | El gerente los ajusta sin depender de un cambio de código |
| Documentos legales: 4 filas fijas editables desde `/admin`, no texto hardcodeado en el template | El pedido era "algo que se pueda vender" — el gerente necesita poder ajustar el texto legal sin depender de un cambio de código, igual que "Cuidados" |
| Cookies: banner con Aceptar/Rechazar aunque hoy el sitio solo usa cookies esenciales | El sitio no depende de la respuesta para funcionar (no hay analítica que bloquear todavía), pero deja la base lista para cuando se agregue algo que sí la necesite |

---

## 6. Reglas que hay que seguir al modificar el proyecto

(Están completas en `AGENTS.md` — resumen acá de lo más crítico)

1. **Correr `python manage.py test` antes y después de cualquier cambio**
   (49 tests al momento de escribir esto). Varios bugs reales de producción
   los agarró un test que empezó a fallar solo — no es ruido.
2. `python manage.py check` antes de dar por terminado un cambio de
   modelos/settings.
3. Nunca tocar `.env` local con credenciales de producción (Neon,
   Backblaze) — se usan overrides puntuales de `DATABASE_URL` en la línea
   de comando, nunca guardados en archivos.
4. Nunca retener contraseñas/API keys que el usuario pega en el chat —
   usarlas una vez para la tarea puntual y listo.
5. No usar `.date()` sobre un datetime aware sin pasar por
   `timezone.localtime(...)` antes (ver gotcha de zona horaria).
6. Cualquier `login(request, user)` manual necesita `backend=` explícito
   (hay más de un backend en `AUTHENTICATION_BACKENDS` desde que existe
   login con Google).
7. Antes de commitear, revisar el diff — nunca secretos, nunca `.env`,
   `db.sqlite3`, `media/`, `staticfiles/`.
8. Al agregar un link o botón nuevo, verificar que REALMENTE lleve a algo
   — esta sesión encontró varios (`href="#"`, botones sin handler) que se
   veían funcionales y no lo eran. Hacer una pasada de grep por
   `href="#"` y `<button` sin handler antes de dar algo por terminado.
9. Commit y push solo cuando el usuario lo pide explícitamente (aunque en
   la práctica de esta sesión, cada tanda de cambios terminó pidiéndose).

---

## 7. Errores conocidos (ya corregidos — para no repetirlos)

| Bug | Causa | Fix |
|---|---|---|
| 500 en TODA la web | Un `{% block content %}` escrito como texto dentro de un comentario HTML en `base.html` — Django lo procesa igual | Se sacó el texto literal del comentario |
| Subida de imágenes rota en local | `STORAGES` sin entrada `"default"` cuando no hay credenciales S3 | Se agregó un `"default"` explícito con FileSystemStorage |
| 500 en registro público | `login()` con más de un backend configurado necesita `backend=` explícito | Se agregó el kwarg en `RegistroView` |
| Choques de horario mal calculados cerca de medianoche | `.date()` sobre datetime en UTC en vez de hora local (Argentina) | `timezone.localtime(...)` antes de comparar |
| Cliente y empleado a la vez | Nada bloqueaba tener los dos perfiles ni cargarlos juntos en la misma pantalla | `clean()` en ambos modelos + verificación extra en `save_related` |
| Botones con texto dorado ilegible sobre fondo claro | `.btn-outline` (pensado para fondo oscuro) usado en secciones de fondo claro | Cambiado a `.btn-outline-dark` |
| 500 al restablecer contraseña con credenciales SMTP mal cargadas | En realidad Django ya lo atrapa solo — el 500 real era distinto (ver abajo) | Capa extra de manejo de errores igual, por las dudas |
| 502 real al restablecer contraseña | Conexión SMTP sin timeout, Gmail tardaba en responder, el worker entero se colgaba y Render devolvía 502 a TODOS | `EMAIL_TIMEOUT = 10` en settings |
| 500 en el callback de Google login | Faltaba `PyJWT[crypto]` (dependencia de `django-allauth` para verificar el token de Google, no viene incluida) | Agregado a `requirements.txt` |
| Links del footer y botón de galería no llevaban a nada | `href="#"` sin conectar desde el diseño original, nunca se completó | Página de galería nueva + footer reconectado + chips del chat con JS real |
| Site framework con dominio "example.com" | `django.contrib.sites` cachea el Site en memoria del proceso — un cambio manual no se ve hasta reiniciar | `sincronizar_site` management command, corrido en cada deploy |

---

## 8. Problemas pendientes (no resueltos, conocidos)

- `whatsapp_general` = número de ejemplo en producción (dato, no código —
  ver sección 3).
- Empleados seed sin email cargado.
- Campo "Políticas" sin sección visual en el sitio.

Ningún bug de código abierto conocido al momento de escribir esto — los 49
tests pasan y se verificó cada feature nueva localmente en el navegador.

---

## 9. Último cambio realizado

App nueva `apps/legal/` — Política de privacidad, Términos y condiciones,
Términos del servicio de tatuaje y Política de cookies, las 4 editables
desde `/admin` con texto real (no placeholder), enlazadas desde el footer.
Se agregó también un aviso de cookies real (banner fijo, Aceptar/Rechazar,
preferencia en `localStorage`). Pedido explícito del usuario: "empezar a
crear algo que se pueda vender" necesita estos documentos legales.
Verificado con 9 tests nuevos (las 4 páginas devuelven 200, 404 en un tipo
inválido, el footer las enlaza, el admin bloquea agregar/borrar) y probado
a mano en el navegador local (banner aparece, Aceptar lo oculta y lo
recuerda, las 4 páginas renderizan bien en mobile). Todavía no
desplegado a producción — pendiente de confirmación del usuario para
pushear (ver sección 10).

---

## 10. Qué debería hacerse después

En orden sugerido de prioridad:

1. **Hacer deploy de los documentos legales y el aviso de cookies** a
   producción (está probado localmente, falta el push + verificar en
   vivo — mismo patrón que el resto de la sesión).
2. **Revisión legal real** de los 4 textos con un profesional antes de
   cualquier lanzamiento comercial — son un modelo estándar razonable,
   pero cada país tiene reglas propias (sobre todo para menores de edad y
   datos de salud, que aplican directo a un estudio de tatuajes).
3. Cargar el **WhatsApp real** del estudio en `/admin` (reemplaza el
   número de ejemplo que el chatbot está repartiendo ahora mismo).
4. Decidir si cargarle **email a los 3 empleados de ejemplo** (o
   reemplazarlos directamente por los tatuadores reales del estudio).
5. Reemplazar el resto de los **datos de ejemplo** (nombre, dirección,
   horarios, descripción, fotos) por los reales del estudio.
6. Si se quiere una imagen más profesional: crear el **Gmail dedicado al
   estudio** para el remitente de los emails de restablecer contraseña
   (los pasos ya se explicaron, no se completó).
7. Decidir si se quiere una sección visual para "Políticas" (mismo patrón
   que "Cuidados") — o si ese campo se reemplaza directamente por el
   nuevo "Términos del servicio" de `/legal/`, que ya cubre gran parte de
   lo mismo (edad mínima, salud, cancelaciones).
8. Cuando el estudio esté listo para ser real: dominio propio, evaluar
   planes pagos de Render/Neon/Backblaze si el tráfico lo justifica.

---

## 11. Checklist — objetivos cumplidos en esta sesión

- [x] Reservar turno solo desde el apartado administrativo (empleados/admin), no clientes
- [x] Arreglar colores de botones ilegibles ("Ver horarios disponibles", "Continuar con Google")
- [x] Restablecer contraseña — funcionalidad completa, probada con cliente/empleado/admin
- [x] Restablecer contraseña funciona con emails de clientes reales (no solo admin)
- [x] Restricción: solo superusuario cambia contraseña de otro, nunca de un cliente
- [x] Login con Google — credenciales cargadas, probado con cuenta real, funciona
- [x] Corregir 500 al restablecer contraseña (causa real: timeout SMTP faltante)
- [x] Corregir 500 en login con Google (causa real: PyJWT faltante)
- [x] Foto del estudio configurable desde `/admin`
- [x] Cuidados post-tatuaje conectado (antes el link no llevaba a nada)
- [x] Redes sociales sin JSON (campos de texto simples)
- [x] Auditoría completa de links/botones muertos en todo el sitio público
- [x] Galería completa con filtros (antes "Ver toda la galería" no hacía nada)
- [x] Chips de sugerencia del chat conectados al chat real
- [x] Quitar texto confuso "(todavía no conectado)" del preview del chat
- [x] Documentación Word actualizada
- [x] `AGENTS.md` creado y actualizado
- [x] Este documento de estado/continuidad
- [x] Política de privacidad (`/legal/privacidad/`)
- [x] Términos y condiciones de uso del sitio (`/legal/terminos-y-condiciones/`)
- [x] Términos del servicio de tatuaje (`/legal/terminos-del-servicio/`)
- [x] Política de cookies con aviso/consent banner real (`/legal/cookies/`)
- [x] Las 4 páginas editables desde `/admin` (no hardcodeadas)

- [ ] Deploy a producción de los documentos legales + aviso de cookies (pendiente de confirmación para pushear)
- [ ] Revisión legal profesional de los 4 textos antes de un lanzamiento real (pendiente)
- [ ] Cargar WhatsApp real del estudio (pendiente — dato, no código)
- [ ] Emails de empleados de ejemplo (pendiente)
- [ ] Reemplazar datos de ejemplo por reales (pendiente, previo a producción real)
- [ ] Gmail dedicado al estudio para emails (pendiente, opcional)
