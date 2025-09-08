import os
import django
import sys
from decimal import Decimal
import argparse

# --- Configuración Manual de Django ---
sys.path.append(os.path.join(os.path.dirname(__file__), 'prestamos_project'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
# --- Fin de la Configuración ---

from django.db.models import Count, Sum
from gestion_prestamos.models import Prestamo, Cuota

def run_check(delete_duplicates=False, delete_id=None):
    """
    Realiza un chequeo de datos y, opcionalmente, elimina datos específicos.
    """
    print('--- Iniciando chequeo de datos (Modo Directo) ---')

    # --- Lógica de Eliminación de ID específico (se ejecuta primero) ---
    if delete_id:
        print(f'\n[ACCIÓN] Intentando eliminar préstamo con ID: {delete_id}')
        try:
            prestamo_a_borrar = Prestamo.objects.get(pk=delete_id)
            # Al borrar el préstamo, las cuotas se borran en cascada.
            prestamo_a_borrar.delete()
            print(f'  - ÉXITO: Se ha eliminado el préstamo con ID {delete_id}.')
        except Prestamo.DoesNotExist:
            print(f'  - ERROR: No se encontró un préstamo con ID {delete_id}.')
        except Exception as e:
            print(f'  - ERROR: Ocurrió un error inesperado durante la eliminación: {e}')

    # --- Análisis de Datos (se ejecuta después de una posible eliminación) ---
    print('\n[ANÁLISIS] Verificando estado actual de la base de datos...')
    
    # Verificación de Existencia de Cuotas
    total_prestamos = Prestamo.objects.count()
    total_cuotas = Cuota.objects.count()
    print(f'  - Préstamos existentes: {total_prestamos}')
    print(f'  - Cuotas existentes: {total_cuotas}')
    if total_prestamos > 0 and total_cuotas == 0:
        print('  - ADVERTENCIA: Aún existen préstamos sin cuotas. Es necesario borrarlos o arreglarlos.')

    # Diagnóstico del Panel Informativo
    activos = Prestamo.objects.filter(estado='activo')
    total_prestado_activo = activos.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    print(f'  - Préstamos activos: {activos.count()} (Suma total: ${total_prestado_activo})')

    print('\n--- Chequeo de datos finalizado ---')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Chequeo y limpieza de datos de préstamos.')
    parser.add_argument(
        '--delete-id',
        type=int,
        help='Elimina un préstamo específico por su ID.'
    )
    # El argumento de duplicados se mantiene por si es útil en el futuro, pero no se usa en este flujo.
    parser.add_argument(
        '--delete-duplicates',
        action='store_true',
        help='Activa la eliminación de los préstamos duplicados encontrados.'
    )
    args = parser.parse_args()

    run_check(delete_duplicates=args.delete_duplicates, delete_id=args.delete_id)