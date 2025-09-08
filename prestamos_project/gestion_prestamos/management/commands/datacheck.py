from django.core.management.base import BaseCommand
from django.db.models import Count, Sum
from gestion_prestamos.models import Prestamo
from decimal import Decimal

class Command(BaseCommand):
    help = 'Realiza un chequeo de datos: busca duplicados y verifica métricas del panel.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- Iniciando chequeo de datos ---'))

        # --- 1. Búsqueda de préstamos duplicados ---
        self.stdout.write(self.style.WARNING('\n[PASO 1] Buscando préstamos duplicados...'))
        self.stdout.write('Se considera duplicado un préstamo con el mismo cliente, monto y fecha de desembolso.')

        duplicates = (
            Prestamo.objects.values('cliente', 'monto', 'fecha_desembolso')
            .annotate(count_id=Count('id'))
            .filter(count_id__gt=1)
        )

        if not duplicates:
            self.stdout.write(self.style.SUCCESS('No se encontraron préstamos duplicados.'))
        else:
            self.stdout.write(self.style.ERROR(f'Se encontraron {len(duplicates)} grupos de préstamos duplicados.'))
            
            self.ids_a_borrar = []
            for group in duplicates:
                prestamos = Prestamo.objects.filter(
                    cliente=group['cliente'],
                    monto=group['monto'],
                    fecha_desembolso=group['fecha_desembolso']
                ).order_by('id')

                original = prestamos.first()
                duplicados_a_borrar = prestamos[1:]
                self.ids_a_borrar.extend([d.id for d in duplicados_a_borrar])
                
                self.stdout.write(f'\nGrupo de duplicados para Cliente ID {group["cliente"], "Monto" {group["monto"]}:
')
                self.stdout.write(self.style.SUCCESS(f'  - ORIGINAL (se conservará): Préstamo ID {original.id}'))
                for dup in duplicados_a_borrar:
                    self.stdout.write(self.style.ERROR(f'  - DUPLICADO (para borrar): Préstamo ID {dup.id}'))

            self.stdout.write(self.style.WARNING(f'\nEn total, se proponen para borrar {len(self.ids_a_borrar)} préstamos.'))
            self.stdout.write('Por favor, revisa la lista. Si estás de acuerdo, puedo proceder a eliminarlos.')


        # --- 2. Diagnóstico del Panel Informativo ---
        self.stdout.write(self.style.WARNING('\n[PASO 2] Diagnosticando métricas del Panel Informativo...'))
        
        activos = Prestamo.objects.filter(estado='activo')
        total_prestado_activo = activos.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

        self.stdout.write(f'El cálculo directo desde la base de datos muestra:')
        self.stdout.write(self.style.SUCCESS(f'  - Total de Préstamos con estado "activo": {activos.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  - Suma de montos de préstamos activos: ${total_prestado_activo}'))

        if activos.count() > 0:
            ids_activos = ", ".join(str(p.id) for p in activos)
            self.stdout.write(f'  - IDs de los préstamos activos: {ids_activos}')
        
        self.stdout.write('Por favor, compara esta información con la que ves en el panel.')
        self.stdout.write(self.style.SUCCESS('\n--- Chequeo de datos finalizado ---'))
