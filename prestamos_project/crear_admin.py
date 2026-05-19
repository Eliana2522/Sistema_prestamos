import os
import django
import sys

# Conseguir la ruta de la carpeta donde está este script (prestamos_project)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

# --- CONFIGURACIÓN DEL ADMIN ---
USERNAME = 'admin'
EMAIL = 'admin@example.com'
PASSWORD = 'adminpassword123'

def create_admin():
    try:
        if not User.objects.filter(username=USERNAME).exists():
            User.objects.create_superuser(USERNAME, EMAIL, PASSWORD)
            print(f"--- ÉXITO: Superusuario '{USERNAME}' creado ---")
        else:
            print(f"--- AVISO: El usuario '{USERNAME}' ya existe ---")
    except Exception as e:
        print(f"--- ERROR: {e} ---")

if __name__ == '__main__':
    create_admin()
