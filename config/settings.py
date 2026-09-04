"""
Configuración central del proyecto Django "Tinta Vieja".

Todo lo que puede cambiar entre tu computadora, la beta y un futuro despliegue
real (claves, base de datos, etc.) se lee desde el archivo .env (ver .env.example
para la lista completa) — así el código nunca tiene secretos escritos adentro.
Si .env no existe o una variable está vacía, cada sección de acá abajo tiene un
valor por defecto pensado para que el proyecto funcione igual en tu máquina
(SQLite local, sin IA configurada, etc.) — ver env_str()/env_list() más abajo.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")


def env_str(name, default=""):
    """Como env.str(), pero una variable presente y vacía en .env (ej. `SECRET_KEY=`)
    se trata igual que si no estuviera definida, en vez de devolver '' literal."""
    valor = env.str(name, default="").strip()
    return valor if valor else default


def env_list(name, default=None):
    valor = env_str(name, default="")
    if not valor:
        return list(default or [])
    return [parte.strip() for parte in valor.split(",") if parte.strip()]


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env_str("SECRET_KEY", default="django-insecure-dev-only-change-me")

DEBUG = env.bool("DEBUG", default=True)

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "testserver"])

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", default=[])

# Render define esta variable automáticamente en cada despliegue con el dominio
# público real (ej. tinta-vieja.onrender.com) — así no hace falta escribirlo a
# mano en ALLOWED_HOSTS/CSRF_TRUSTED_ORIGINS ni actualizarlo si el nombre cambia.
RENDER_EXTERNAL_HOSTNAME = env_str("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")


# Application definition
# Las apps propias del proyecto viven en la carpeta apps/ (una por función:
# usuarios, artistas, galería, chatbot, etc.) — cada una es un módulo Django
# normal con sus propios models.py / views.py / admin.py / urls.py.

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.users",
    "apps.artists",
    "apps.gallery",
    "apps.chatbot",
    "apps.design_assist",
    "apps.image_ai",
    "apps.research",
    "apps.contacts",
    "apps.studio",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.studio.context_processors.configuracion_estudio",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

AUTH_USER_MODEL = "users.Usuario"


# Database
# Free-tier beta: Neon Postgres in production via DATABASE_URL, SQLite for local dev
# by default so no external service is required just to start coding.

DATABASES = {
    "default": env.db_url_config(
        env_str("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
    )
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization

LANGUAGE_CODE = "es"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True


# Static & media files

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Storage de imágenes en la nube — cualquier proveedor compatible con S3 sirve
# (Cloudflare R2, Backblaze B2, etc.), por eso las variables son genéricas
# (STORAGE_*, no atadas a un proveedor). Se activa automáticamente cuando están
# presentes; si no, se usa el disco local (MEDIA_ROOT) para desarrollo.
AWS_ACCESS_KEY_ID = env_str("STORAGE_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env_str("STORAGE_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env_str("STORAGE_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = env_str("STORAGE_ENDPOINT_URL")
AWS_S3_REGION_NAME = env_str("STORAGE_REGION_NAME")
AWS_S3_CUSTOM_DOMAIN = env_str("STORAGE_PUBLIC_DOMAIN")  # solo si el bucket es público
AWS_DEFAULT_ACL = None
# El bucket de la beta es privado (evita depender de que el proveedor cobre por
# habilitar acceso público) — por eso las URLs se firman con una fecha de
# vencimiento en vez de ser links públicos fijos. Si en el futuro el bucket pasa
# a ser público, esto se puede poner en False.
AWS_QUERYSTRING_AUTH = True

if AWS_ACCESS_KEY_ID and AWS_STORAGE_BUCKET_NAME:
    STORAGES["default"] = {"BACKEND": "storages.backends.s3.S3Storage"}


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Claves de servicios de IA — nunca se exponen al frontend ni al modelo (ver services/ai/).
GROQ_API_KEY = env_str("GROQ_API_KEY")
GROQ_MODEL = env_str("GROQ_MODEL", default="openai/gpt-oss-120b")
GEMINI_API_KEY = env_str("GEMINI_API_KEY")
GEMINI_MODEL = env_str("GEMINI_MODEL", default="gemini-2.5-flash-lite")
TAVILY_API_KEY = env_str("TAVILY_API_KEY")
REPLICATE_API_TOKEN = env_str("REPLICATE_API_TOKEN")


# Seguridad — activa cabeceras estrictas fuera de DEBUG (producción/Render).
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

X_FRAME_OPTIONS = "DENY"

LOGIN_URL = "users:login"
LOGIN_REDIRECT_URL = "studio:inicio"
LOGOUT_REDIRECT_URL = "studio:inicio"


# Logging — nunca registrar contraseñas, API keys ni tokens (ver arquitectura, sección 50).
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
