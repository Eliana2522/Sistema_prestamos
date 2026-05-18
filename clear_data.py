import os
import django
import sys

# --- Configuración Manual de Django ---
# Cambiamos al directorio del proyecto para asegurar que encuentre db.sqlite3 y .env
project_path = os.path.join(os.getcwd(), 'prestamos_project')
if os.path.exists(project_path):
    os.chdir(project_path)

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.apps import apps
from django.db import transaction

def clear_system_data():
    print("--- Iniciando limpieza de DATOS (sin borrar tablas) ---")
    
    # Lista de modelos a limpiar en orden para evitar problemas de claves foráneas
    # O simplemente iteramos sobre las apps 'gestion_prestamos' y 'dashboard'
    app_labels = ['gestion_prestamos', 'dashboard']
    
    confirmacion = input("¿Estás seguro de que quieres borrar TODOS los registros de préstamos, pagos, clientes, etc.? (escribe 'si' para confirmar): ")
    
    if confirmacion.lower() == 'si':
        try:
            with transaction.atomic():
                for app_label in app_labels:
                    app_config = apps.get_app_config(app_label)
                    for model in app_config.get_models():
                        count = model.objects.all().count()
                        model.objects.all().delete()
                        print(f"Borrados {count} registros del modelo {model.__name__}")
            print("\n--- Limpieza completada con éxito ---")
        except Exception as e:
            print(f"\nError durante la limpieza: {e}")
    else:
        print("Operación cancelada.")

if __name__ == '__main__':
    clear_system_data()
