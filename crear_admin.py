import os
import django
import sys

# Añadimos la ruta del proyecto para que Django encuentre los módulos
sys.path.append(os.path.join(os.getcwd(), 'prestamos_project'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

# --- CONFIGURACIÓN DEL ADMIN ---
# Puedes cambiar estos valores si lo deseas
USERNAME = 'admin'
EMAIL = 'admin@example.com'
PASSWORD = 'adminpassword123'

def create_admin():
    try:
        if not User.objects.filter(username=USERNAME).exists():
            User.objects.create_superuser(USERNAME, EMAIL, PASSWORD)
            print(f"--- ÉXITO: Superusuario '{USERNAME}' creado correctamente ---")
            print(f"Usuario: {USERNAME}")
            print(f"Password: {PASSWORD}")
        else:
            print(f"--- AVISO: El usuario '{USERNAME}' ya existe en la base de datos ---")
    except Exception as e:
        print(f"--- ERROR al crear el usuario: {e} ---")

if __name__ == '__main__':
    create_admin()
