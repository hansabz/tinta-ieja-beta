#!/usr/bin/env bash
# Script de build que corre Render antes de cada despliegue.
# 1) instala dependencias, 2) junta los archivos estáticos (CSS/JS) en un solo
# lugar para que whitenoise los sirva, 3) aplica las migraciones pendientes a
# la base de datos (Neon) para que el esquema quede al día automáticamente.
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate
