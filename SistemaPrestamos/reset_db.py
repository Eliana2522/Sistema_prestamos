import os
import django
import sys

# --- Configuración Manual de Django ---
sys.path.append(os.path.join(os.path.dirname(__file__), 'prestamos_project'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
# --- Fin de la Configuración ---

from django.db import connection

def reset_database():
    print("--- Iniciando reseteo COMPLETO de la base de datos ---")
    with connection.cursor() as cursor:
        print("Obteniendo todas las tablas...")
        # Get all table names
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'prestamos_%%' OR table_name LIKE 'django_%%' OR table_name LIKE 'auth_%%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Drop all tables
        if tables:
            print(f"Borrando las siguientes tablas: {tables}")
            cursor.execute(f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;")
            print("Tablas borradas.")
        else:
            print("No se encontraron tablas para borrar.")

    print("\n--- Reseteo completado ---")

if __name__ == '__main__':
    # Advertencia de seguridad
    confirmacion = input("¡ADVERTENCIA! Estás a punto de borrar TODAS las tablas de la base de datos de forma irreversible. ¿Estás seguro de que quieres continuar? (escribe 'si' para confirmar): ")
    if confirmacion.lower() == 'si':
        reset_database()
    else:
        print("Reseteo cancelado por el usuario.")