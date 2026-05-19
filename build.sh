#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Ejecutar todo desde la carpeta correcta
cd prestamos_project
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python ../crear_admin.py
