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
    print("--- Iniciando reseteo de la base de datos ---")

    print("\n--- Reiniciando IDs de las tablas ---")
    with connection.cursor() as cursor:
        print("Truncando tablas de PostgreSQL...")
        # El comando TRUNCATE borra todos los datos y reinicia los contadores de ID.
        # CASCADE se encarga de borrar también los datos en tablas relacionadas.
        cursor.execute("TRUNCATE TABLE prestamos_pago, prestamos_cuota, prestamos_prestamo, prestamos_cliente, prestamos_tipo_prestamo RESTART IDENTITY CASCADE;")
        print("Tablas de PostgreSQL reseteadas.")

    print("\n--- Reseteo completado ---")

if __name__ == '__main__':
    # Advertencia de seguridad
    confirmacion = input("¡ADVERTENCIA! Estás a punto de borrar TODOS los datos de clientes, préstamos, cuotas y pagos de forma irreversible. ¿Estás seguro de que quieres continuar? (escribe 'si' para confirmar): ")
    if confirmacion.lower() == 'si':
        reset_database()
    else:
        print("Reseteo cancelado por el usuario.")
