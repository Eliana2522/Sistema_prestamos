#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Entramos a la carpeta del proyecto
cd prestamos_project

# Preparamos los archivos y la base de datos
python manage.py collectstatic --no-input
python manage.py migrate

# Creamos el administrador automáticamente
python ../crear_admin.py
