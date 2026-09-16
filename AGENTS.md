# Tinta Vieja — contexto para agentes de IA

Este archivo existe para que cualquier asistente de código con acceso a este
repositorio (Claude Code, Antigravity, u otro) tenga de entrada el contexto
que normalmente se pierde entre sesiones: qué es este proyecto, cómo está
armado, qué reglas de negocio ya se decidieron y por qué, y qué errores ya se
cometieron una vez para no repetirlos. Es el mismo tipo de archivo que
herramientas como Claude Code, Cursor o Antigravity buscan automáticamente en
la raíz del repo (`AGENTS.md` es el nombre que reconoce la mayoría; si tu
herramienta busca otro nombre, un symlink o una copia resuelve el resto).

## Qué es esto

Web de demostración (beta) para un estudio de tatuajes real. Django +
Postgres (Neon) + almacenamiento de imágenes S3-compatible (Backblaze B2) +
hosting en Render, todo en capa gratuita. Documentación completa orientada al
usuario final (el gerente del estudio) en `docs/Tinta_Vieja_Documentacion.docx`
— este archivo es el complementario, orientado a quien vaya a tocar código.

## Antes de tocar nada

- **Corré la suite completa antes y después de cualquier cambio**:
  `python manage.py test` (41+ tests al momento de escribir esto). Si algo se
  rompe, es una señal real, no ruido — varios bugs de producción reales de
  este proyecto los agarró un test que empezó a fallar solo.
- **`python manage.py check`** antes de dar por terminado cualquier cambio de
  modelos/settings.
- Este proyecto tiene un dev server local (`.claude/launch.json` — o
  `python manage.py runserver` a mano) contra SQLite. La base real (Neon) y el
  storage real (Backblaze) NUNCA se tocan desde `.env` local — se acceden solo
  con overrides puntuales de `DATABASE_URL` en la línea de comando, nunca
  guardados en ningún archivo del repo.
- No hay CI configurado — el chequeo antes de cada commit es manual (correr
  los tests vos mismo).

## Invariantes de seguridad — no se negocian

Estas reglas están verificadas con tests automáticos. Si tu cambio hace que
alguno de estos deje de cumplirse, es un bug, no un "detalle":

1. **El registro público SIEMPRE crea `rol=CLIENTE`**, `is_staff=False`,
   `is_superuser=False` — sin importar qué mande el cliente en el POST. Mismo
   criterio para el login con Google (`apps/users/adapters.py`).
2. **Un usuario nunca puede tener perfil de `Cliente` y de `Empleado` al mismo
   tiempo** (`Cliente.clean()` / `Empleado.clean()` en `apps/users/models.py`
   y `apps/artists/models.py`, más una verificación extra en
   `UsuarioAdmin.save_related` para el caso de cargar los dos en la misma
   pantalla — ver el comentario ahí, es un caso límite real que pasó).
3. **Un empleado nunca puede borrar una cita del historial** — solo
   administrador/superusuario (`apps/appointments/admin.py`,
   `has_delete_permission`).
4. **Cambiarle la contraseña a OTRA persona desde `/admin` es exclusivo del
   superusuario, y nunca se puede hacer sobre un cliente** — un cliente usa el
   restablecimiento self-service (`UsuarioAdmin.user_change_password`).
5. **`/admin` nunca tiene un link visible desde la navegación pública** — ni
   siquiera para un usuario staff navegando el sitio como cliente. Se llega
   solo escribiendo la URL.
6. El chatbot de IA **nunca inventa una respuesta** cuando no puede contestar
   — crea una `SolicitudContacto` real y ofrece hablar con una persona
   (`services/ai/chat_service.py`).

## Gotchas ya encontrados (para no perder tiempo redescubriéndolos)

- **`USE_TZ=True` con `TIME_ZONE="America/Argentina/Buenos_Aires"`**: nunca
  llames `.date()` sobre un datetime aware sin pasar antes por
  `timezone.localtime(...)`. Comparar fechas en UTC directamente rompe la
  lógica de "mismo día"/"mismo mes" cerca de la medianoche — pasó de verdad en
  `apps/appointments/services.py` (ver el comentario ahí).
- **Un `{% ... %}` de Django dentro de un comentario HTML `<!-- -->` se
  procesa igual** — no es un comentario para el motor de templates. Causó un
  500 en TODA la web una vez.
- **`STORAGES` necesita una entrada `"default"` explícita** en
  `config/settings.py` o Django no sabe dónde guardar un `ImageField` cuando
  no hay credenciales de S3 cargadas (rompía la subida de imágenes en
  desarrollo local).
- **Con más de un backend en `AUTHENTICATION_BACKENDS`** (pasó al agregar
  login con Google), cualquier `login(request, user)` manual necesita el
  kwarg `backend=` explícito — si no, `ValueError` en cualquier flujo que
  loguee a mano después de crear una cuenta (pasó en `RegistroView`).
- **`django.contrib.sites` cachea el `Site` en memoria del proceso** — un
  cambio de dominio hecho a mano no se ve hasta reiniciar el proceso. En
  producción esto se resuelve solo: `python manage.py sincronizar_site` corre
  en cada deploy (`build.sh`), después de `migrate`, y lee
  `RENDER_EXTERNAL_HOSTNAME`.
- El admin de Django por defecto (`add_fieldsets`) **no muestra
  first_name/last_name/rol en el alta**, solo usuario/contraseña — causó
  cuentas creadas con datos a medias. Se corrigió con un `add_fieldsets`
  custom en `UsuarioAdmin`.

## Estructura del código

```
apps/
  users/        Usuario (custom, con `rol`), Cliente, registro, login, reset de contraseña
  artists/      Empleado (perfil de trabajo del tatuador)
  appointments/ Cita, SesionCita, calendario de reserva, reglas de negocio, Excel
  gallery/      Estilo, Etiqueta, Obra (portafolio público)
  studio/       ConfiguracionEstudio (singleton, todos los números ajustables desde /admin)
  contacts/     SolicitudContacto
  chatbot/      Conversacion, Mensaje — la IA vive en services/ai/, no acá
  design_assist/ image_ai/ research/   apps previstas para más adelante, sin uso activo todavía
services/
  ai/           Todo lo del chatbot: prompts, proveedores (Groq/Gemini), herramientas controladas
  whatsapp.py   Helper compartido para armar links wa.me — lo usan appointments y el chatbot
config/         settings.py, urls.py — leer settings.py primero, tiene comentarios de por qué
```

Patrón repetido en todo el proyecto: la lógica de negocio (qué se puede y qué
no) vive en `services.py` de cada app, no en las vistas ni en el admin — así
la misma regla vale sin importar desde dónde se dispare la acción.

## Convenciones de commit

- Mensajes en español, explicando el POR QUÉ del cambio, no solo el qué —
  varios bugs de este proyecto son sutiles y el "por qué" ahorra
  re-descubrirlos.
- `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>` al final si el
  cambio lo hizo Claude Code — si otra herramienta/agente hace el commit,
  usá su propia línea de co-autoría en vez de esta (no la copies sin más).
- Nunca commitear `.env`, `db.sqlite3`, `media/`, `staticfiles/`,
  `.venv/` — ya están en `.gitignore`, pero revisá el diff igual antes de
  cada commit si tocaste algo cerca de configuración o credenciales.

## Si dos agentes van a tocar este repo

Si vas a alternar entre Claude Code y otra herramienta (Antigravity u otra)
sobre el mismo checkout:

- **Commiteá (o al menos stasheá) antes de cambiar de herramienta.** Ninguna
  de las dos sabe qué cambios sin guardar dejó la otra en el working tree.
- **Una sola corre por vez sobre el mismo checkout.** Si las dos van a
  trabajar en simultáneo, usá dos clones/worktrees separados y mergeá después
  — no dos agentes escribiendo archivos al mismo tiempo en la misma carpeta.
- Este archivo es el que mantiene sincronizado el contexto entre ambas — si
  una herramienta toma una decisión de arquitectura nueva (una regla de
  negocio, un gotcha nuevo), anotala acá para que la otra la vea la próxima
  vez.
