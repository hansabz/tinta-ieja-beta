# Tinta Vieja — Beta

Backend en Django. El diseño visual de referencia (estático) está en `scratchpad` de esta conversación; se irá integrando como templates en los próximos pasos.

## Puesta en marcha local

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # completar valores si hace falta (SQLite funciona sin tocar nada)
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Sin `.env`, el proyecto corre con SQLite local y sin ninguna API de IA configurada — sirve para desarrollar la parte de usuarios, roles y admin sin depender de servicios externos.

## Estructura

```
config/          # settings, urls, wsgi/asgi
apps/
  users/         # Usuario personalizado, roles, registro/login
  artists/       # perfil de artista/empleado
  gallery/       # obras, estilos, etiquetas
  chatbot/       # conversaciones y mensajes
  design_assist/ # encuesta + carpeta de referencias
  image_ai/      # generación IA opcional (Replicate) — apagada por defecto
  research/      # investigación cultural (Tavily)
  contacts/      # solicitudes de contacto
  studio/        # configuración del estudio (singleton), homepage
templates/
```

## Regla de seguridad ya implementada

El registro público (`apps/users/views.py::RegistroView`) siempre crea `rol=CLIENTE`,
`is_staff=False`, `is_superuser=False` — sin importar qué envíe el formulario. Verificado
con una prueba que intenta mandar `rol=ADMINISTRADOR` y confirma que no tiene efecto.
