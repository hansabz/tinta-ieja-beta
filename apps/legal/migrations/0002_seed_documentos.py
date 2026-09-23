from django.db import migrations

AVISO_BETA = (
    "Este documento es un modelo estándar para la etapa beta de este sitio. Antes de un "
    "lanzamiento comercial real, te recomendamos que un profesional legal lo revise y lo "
    "adapte a la legislación de tu país."
)

PRIVACIDAD = "\n\n".join([
    AVISO_BETA,
    "En esta política te contamos qué información recopilamos cuando usás el sitio, para qué "
    "la usamos y qué derechos tenés sobre ella.",
    "Datos que recopilamos: cuando creás una cuenta guardamos tu nombre, usuario, email y "
    "contraseña (encriptada, nunca en texto plano). Si el estudio te registra como cliente "
    "para agendarte un turno, también se guarda tu historial de citas y, si autorizás la "
    "publicación de tu tatuaje en el portafolio, la foto del resultado. Si iniciás sesión con "
    "Google, recibimos tu nombre y email desde tu cuenta de Google, nunca tu contraseña.",
    "Para qué usamos tus datos: gestionar tus turnos, contactarte por WhatsApp, email o el "
    "chat del sitio, mostrarte tu historial de citas, y responder tus consultas a través del "
    "asistente virtual. Nunca vendemos tus datos a terceros.",
    "Con quién se comparte: solo con los proveedores técnicos que hacen posible el sitio "
    "(hosting, base de datos, almacenamiento de imágenes y el proveedor de inteligencia "
    "artificial que procesa los mensajes del chat), y únicamente en la medida necesaria para "
    "que el servicio funcione.",
    "Cuánto tiempo conservamos tus datos: el historial de citas terminadas se conserva por un "
    "tiempo limitado y después se elimina automáticamente. Tu cuenta se conserva mientras la "
    "mantengas activa; si querés que la eliminemos, escribinos desde la sección de contacto.",
    "Tus derechos: podés pedirnos en cualquier momento acceder, corregir o eliminar tus datos "
    "personales, escribiéndonos por el formulario de contacto o el WhatsApp del estudio.",
    "Menores de edad: hacerse un tatuaje suele requerir ser mayor de edad o contar con la "
    "autorización de un padre, madre o tutor, según la legislación de cada país. El estudio "
    "puede pedir una identificación y, si corresponde, la autorización firmada antes de "
    "agendar o realizar cualquier sesión.",
    "Seguridad: usamos conexión cifrada (HTTPS) en todo el sitio y nunca almacenamos "
    "contraseñas en texto plano.",
    "Cambios a esta política: si la actualizamos, la nueva fecha va a aparecer al principio "
    "de esta página.",
])

TERMINOS_CONDICIONES = "\n\n".join([
    AVISO_BETA,
    "Al usar este sitio aceptás estos términos. Si no estás de acuerdo, te pedimos que no lo "
    "uses.",
    "Uso del sitio: podés navegar la galería, conocer a los artistas, consultar estilos y "
    "hablar con nuestro asistente virtual libremente. Crear una cuenta te permite además ver "
    "tu propio historial de turnos.",
    "Tu cuenta: sos responsable de mantener tu contraseña segura y de que los datos que nos "
    "das (nombre, email, teléfono) sean reales. Los turnos en este sitio los carga el estudio "
    "(un empleado o la administración) — no existe un formulario público de autorreserva, así "
    "que cualquier mensaje o cuenta que intente simular eso no representa al estudio.",
    "El asistente virtual: es un sistema automático que puede cometer errores y no reemplaza "
    "el criterio profesional de un tatuador. Cuando no puede resolver tu consulta, deriva la "
    "conversación a una persona real del estudio.",
    "Propiedad intelectual: el diseño del sitio, los textos y las fotos publicadas en la "
    "galería pertenecen al estudio o a sus artistas, salvo que se indique lo contrario. No "
    "está permitido copiarlos o reutilizarlos sin autorización.",
    "Enlaces a otros sitios: este sitio puede enlazar a redes sociales externas (como "
    "Instagram o TikTok). No somos responsables del contenido ni de las políticas de esos "
    "sitios externos.",
    "Límite de responsabilidad: hacemos nuestro mejor esfuerzo para que el sitio funcione "
    "correctamente, pero al ser un servicio en etapa beta puede tener interrupciones o "
    "errores. No garantizamos disponibilidad ininterrumpida.",
    "Cambios a estos términos: podemos actualizar este documento en cualquier momento; la "
    "fecha de la última actualización figura al principio de esta página.",
    "Ley aplicable: estos términos se rigen por las leyes del país donde opera el estudio. "
    "[A completar por el estudio antes del lanzamiento real].",
])

TERMINOS_SERVICIO = "\n\n".join([
    "Este documento es un modelo estándar para la etapa beta de este sitio y describe las "
    "condiciones del servicio de tatuajes en sí (no el uso del sitio web, que están en "
    "Términos y condiciones). Antes de un lanzamiento comercial real, te recomendamos que un "
    "profesional legal lo revise y lo adapte a la legislación de tu país.",
    "Reserva de turnos: los turnos los carga un empleado del estudio (en su propia agenda) o "
    "la administración — el cliente no reserva por su cuenta desde el sitio. Para agendar una "
    "sesión, escribinos por el chat, WhatsApp o el formulario de contacto.",
    "Requisitos para tatuarte: necesitás ser mayor de edad o, si tu legislación lo permite, "
    "contar con la autorización de un padre, madre o tutor. También te podemos pedir que "
    "confirmes que no tenés contraindicaciones de salud (alergias, embarazo, medicación que "
    "afecte la coagulación, etc.) y que no te presentes bajo los efectos del alcohol o de "
    "otras sustancias — nos reservamos el derecho de reprogramar o cancelar la sesión si no "
    "se cumplen estas condiciones.",
    "Cancelaciones y reprogramaciones: [a completar por el estudio: con cuánta anticipación "
    "se puede cancelar o reprogramar sin costo, y si existe una seña o depósito].",
    "Uso de tu imagen: si el resultado de tu tatuaje queda bien y vos lo autorizás, el estudio "
    "puede publicar la foto en su portafolio público, dando crédito al artista. Podés pedir "
    "en cualquier momento que se retire una foto tuya de la galería.",
    "Cuidados posteriores: sos responsable de seguir las indicaciones de cuidado "
    "post-tatuaje que te da el estudio (ver la sección \"Cuidados post-tatuaje\" del sitio). "
    "No seguirlas puede afectar la cicatrización y el resultado final, y el estudio no se "
    "hace responsable por complicaciones derivadas de un cuidado inadecuado.",
    "Derecho de admisión: el estudio puede negarse a realizar un tatuaje por razones de "
    "salud, de criterio profesional o si el diseño solicitado no es viable técnicamente.",
    "Esto no es un consejo médico: la información sobre cuidados o contraindicaciones que te "
    "damos es general — ante cualquier duda de salud, consultá con un profesional médico.",
])

COOKIES = "\n\n".join([
    "Este sitio usa cookies, que son pequeños archivos que se guardan en tu navegador para "
    "que algunas funciones trabajen correctamente.",
    "Cookies esenciales: usamos cookies técnicas necesarias para que el sitio funcione — "
    "mantener tu sesión iniciada y proteger los formularios contra ataques (cookie de "
    "seguridad CSRF). Estas cookies no se pueden desactivar sin que el sitio deje de "
    "funcionar correctamente.",
    "Cookies que NO usamos: por ahora este sitio no usa cookies de analítica ni de "
    "publicidad de terceros. Si en el futuro se agregan, esta política se va a actualizar y "
    "se va a pedir tu consentimiento antes de activarlas.",
    "El aviso de cookies: la primera vez que entrás al sitio te mostramos un aviso para que "
    "confirmes que entendés esto. Podés aceptar o rechazar las cookies no esenciales — igual "
    "vas a poder navegar el sitio con normalidad, porque hoy no dependemos de ellas.",
    "Cómo controlar las cookies desde tu navegador: además de nuestro aviso, todos los "
    "navegadores permiten borrar o bloquear cookies desde su configuración de privacidad.",
    "Cambios a esta política: si empezamos a usar cookies nuevas, vamos a actualizar este "
    "documento y a pedirte tu consentimiento de nuevo.",
])

DOCUMENTOS = [
    ("privacidad", "Política de privacidad", PRIVACIDAD),
    ("terminos-y-condiciones", "Términos y condiciones de uso del sitio", TERMINOS_CONDICIONES),
    ("terminos-del-servicio", "Términos del servicio de tatuaje", TERMINOS_SERVICIO),
    ("cookies", "Política de cookies", COOKIES),
]


def crear_documentos(apps, schema_editor):
    DocumentoLegal = apps.get_model("legal", "DocumentoLegal")
    for tipo, titulo, contenido in DOCUMENTOS:
        DocumentoLegal.objects.get_or_create(
            tipo=tipo, defaults={"titulo": titulo, "contenido": contenido}
        )


def eliminar_documentos(apps, schema_editor):
    DocumentoLegal = apps.get_model("legal", "DocumentoLegal")
    DocumentoLegal.objects.filter(tipo__in=[t for t, _, _ in DOCUMENTOS]).delete()


class Migration(migrations.Migration):
    dependencies = [("legal", "0001_initial")]
    operations = [migrations.RunPython(crear_documentos, eliminar_documentos)]
