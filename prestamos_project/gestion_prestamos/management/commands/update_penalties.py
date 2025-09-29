from django.core.management.base import BaseCommand
from django.utils import timezone
from gestion_prestamos.models import Cuota
from gestion_prestamos.utils import calcular_penalidad_cuota
from decimal import Decimal

class Command(BaseCommand):
    help = 'Calcula y actualiza las penalidades por mora para todas las cuotas vencidas.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- Iniciando cálculo de penalidades por mora ---'))

        hoy = timezone.localdate()

        # Seleccionar cuotas que son candidatas para tener penalidades
        # 1. Deben estar 'pendientes' o 'pagada_parcialmente'.
        # 2. Su fecha de vencimiento debe ser anterior a hoy.
        cuotas_vencidas = Cuota.objects.filter(
            estado__in=['pendiente', 'pagada_parcialmente'],
            fecha_vencimiento__lt=hoy
        )

        if not cuotas_vencidas.exists():
            self.stdout.write(self.style.SUCCESS('No se encontraron cuotas vencidas para calcular penalidades.'))
            self.stdout.write(self.style.SUCCESS('--- Proceso finalizado ---'))
            return

        self.stdout.write(f'Se encontraron {cuotas_vencidas.count()} cuotas vencidas para procesar.')

        cuotas_actualizadas = 0
        for cuota in cuotas_vencidas:
            self.stdout.write('---')
            self.stdout.write(f'Procesando Cuota #{cuota.id}:')
            self.stdout.write(f'  - Fecha de Vencimiento: {cuota.fecha_vencimiento}')

            tipo_prestamo = cuota.prestamo.tipo_prestamo
            if not tipo_prestamo:
                self.stdout.write(self.style.ERROR('  - ERROR: No tiene tipo de préstamo asociado.'))
                continue

            dias_gracia = tipo_prestamo.dias_gracia
            fecha_inicio_penalidad = cuota.fecha_vencimiento + timezone.timedelta(days=dias_gracia)

            self.stdout.write(f'  - Días de Gracia: {dias_gracia}')
            self.stdout.write(f'  - Hoy es: {hoy}')
            self.stdout.write(f'  - La penalidad empieza el: {fecha_inicio_penalidad}')

            if fecha_inicio_penalidad >= hoy:
                self.stdout.write(self.style.WARNING('  - RESULTADO: La cuota está en período de gracia. No se calcula penalidad.'))
                continue

            penalidad_anterior = cuota.monto_penalidad_acumulada
            
            # La lógica de cálculo está en utils.py
            calcular_penalidad_cuota(cuota)
            
            # Refrescar la cuota desde la BD para obtener el valor actualizado
            cuota.refresh_from_db()
            
            if cuota.monto_penalidad_acumulada > penalidad_anterior:
                cuotas_actualizadas += 1
                self.stdout.write(
                    f'  - Cuota #{cuota.numero_cuota} (Préstamo #{cuota.prestamo.id}): ' 
                    f'Penalidad actualizada de ${penalidad_anterior:,.2f} a ${cuota.monto_penalidad_acumulada:,.2f}'
                )

        self.stdout.write(self.style.WARNING(f'\nSe actualizaron penalidades en {cuotas_actualizadas} cuota(s).'))
        self.stdout.write(self.style.SUCCESS('\n--- Cálculo de penalidades finalizado ---'))
