from django.utils import timezone
import datetime
from decimal import Decimal

def calcular_tabla_amortizacion(prestamo):
    """
    Calcula la tabla de amortización para un préstamo dado, 
    delegando en el método de cálculo especificado por el tipo de préstamo.

    Args:
        prestamo (Prestamo): El objeto Prestamo para el cual calcular la tabla.

    Returns:
        list: Una lista de diccionarios, donde cada diccionario representa una cuota.
    """
    metodo_calculo = prestamo.tipo_prestamo.metodo_calculo if prestamo.tipo_prestamo else 'frances'

    if metodo_calculo == 'frances':
        return _calcular_metodo_frances(prestamo)
    # elif metodo_calculo == 'aleman':
    #     return _calcular_metodo_aleman(prestamo)
    else:
        # Por defecto, o si el método no es reconocido, usamos el francés.
        return _calcular_metodo_frances(prestamo)

def _calcular_metodo_frances(prestamo):
    """
    Calcula la tabla de amortización usando el método francés (cuotas fijas).
    """
    monto_pendiente = prestamo.monto
    # Determinar la tasa de interés anual REAL basada en el tipo de préstamo
    tasa_interes_nominal = prestamo.tasa_interes / Decimal(100)
    if prestamo.tipo_prestamo and prestamo.tipo_prestamo.periodo_tasa == 'mensual':
        # Si la tasa es mensual, se anualiza para los cálculos estándar.
        tasa_interes_anual = tasa_interes_nominal * 12
    else:
        # Si es anual o no se especifica tipo, se toma como está.
        tasa_interes_anual = tasa_interes_nominal
    plazo_meses = prestamo.plazo
    fecha_inicio = prestamo.fecha_desembolso
    frecuencia = prestamo.frecuencia_pago

    tabla_amortizacion = []

    if frecuencia == 'mensual':
        pagos_por_anio = 12
        tasa_interes_periodo = tasa_interes_anual / Decimal(pagos_por_anio)
        numero_pagos = plazo_meses
        
        if tasa_interes_periodo > 0:
            cuota_fija = (monto_pendiente * tasa_interes_periodo) / (1 - (1 + tasa_interes_periodo)**(-numero_pagos))
        else:
            cuota_fija = monto_pendiente / numero_pagos

        for i in range(1, numero_pagos + 1):
            interes_periodo = monto_pendiente * tasa_interes_periodo
            capital_periodo = cuota_fija - interes_periodo
            monto_pendiente -= capital_periodo

            # --- Lógica de Fecha de Vencimiento Mensual Corregida ---
            # Se calcula el mes y año de la próxima cuota.
            mes_futuro = fecha_inicio.month + i
            año_futuro = fecha_inicio.year + (mes_futuro - 1) // 12
            mes_futuro = (mes_futuro - 1) % 12 + 1

            # Se previene un error si el día de desembolso no existe en el mes futuro (ej. 31 de Febrero)
            if mes_futuro == 12:
                ultimo_dia_del_mes = 31
            else:
                ultimo_dia_del_mes = (datetime.date(año_futuro, mes_futuro + 1, 1) - datetime.timedelta(days=1)).day
            
            dia_vencimiento = min(fecha_inicio.day, ultimo_dia_del_mes)
            fecha_vencimiento = datetime.date(año_futuro, mes_futuro, dia_vencimiento)

            # Ajuste final para la última cuota para que el saldo sea exactamente cero.
            if i == numero_pagos:
                capital_periodo += monto_pendiente
                monto_pendiente = Decimal(0)

            tabla_amortizacion.append({
                'numero_cuota': i,
                'fecha_vencimiento': fecha_vencimiento,
                'cuota_fija': cuota_fija.quantize(Decimal('0.01')),
                'interes': interes_periodo.quantize(Decimal('0.01')),
                'capital': capital_periodo.quantize(Decimal('0.01')),
                'saldo_pendiente': monto_pendiente.quantize(Decimal('0.01')),
            })

    elif frecuencia == 'quincenal':
        pagos_por_anio = 24
        tasa_interes_periodo = tasa_interes_anual / Decimal(pagos_por_anio)
        numero_pagos = plazo_meses * 2

        if tasa_interes_periodo > 0:
            cuota_fija = (monto_pendiente * tasa_interes_periodo) / (1 - (1 + tasa_interes_periodo)**(-numero_pagos))
        else:
            cuota_fija = monto_pendiente / numero_pagos

        for i in range(1, numero_pagos + 1):
            interes_periodo = monto_pendiente * tasa_interes_periodo
            capital_periodo = cuota_fija - interes_periodo
            monto_pendiente -= capital_periodo

            # Ajuste final para la última cuota.
            if i == numero_pagos:
                capital_periodo += monto_pendiente
                monto_pendiente = Decimal(0)
            
            # Se revierte a la lógica simple y estable de timedelta para quincenas.
            fecha_vencimiento = fecha_inicio + datetime.timedelta(days=15 * i)

            tabla_amortizacion.append({
                'numero_cuota': i,
                'fecha_vencimiento': fecha_vencimiento,
                'cuota_fija': cuota_fija.quantize(Decimal('0.01')),
                'interes': interes_periodo.quantize(Decimal('0.01')),
                'capital': capital_periodo.quantize(Decimal('0.01')),
                'saldo_pendiente': monto_pendiente.quantize(Decimal('0.01')),
            })

    return tabla_amortizacion

def calcular_penalidad_cuota(cuota):
    """
    Calcula y actualiza la penalidad acumulada para una cuota específica.
    La penalidad se calcula sobre el monto pendiente de la cuota.
    """
    hoy = timezone.localdate() # Usar timezone.localdate() para la fecha actual
    
    # Solo calcular penalidad si la cuota está pendiente o parcialmente pagada y vencida
    if cuota.estado in ['pendiente', 'pagada_parcialmente'] and cuota.fecha_vencimiento < hoy:
        
        # Obtener la tasa de penalidad y días de gracia del tipo de préstamo
        tipo_prestamo = cuota.prestamo.tipo_prestamo
        if not tipo_prestamo:
            return # No hay tipo de préstamo, no se puede calcular penalidad

        tasa_penalidad_diaria = tipo_prestamo.tasa_penalidad_diaria
        dias_gracia = tipo_prestamo.dias_gracia

        # Calcular la fecha a partir de la cual se aplica la penalidad
        fecha_inicio_penalidad = cuota.fecha_vencimiento + datetime.timedelta(days=dias_gracia)

        # Si la fecha de inicio de penalidad es en el futuro, no hay penalidad aún
        if fecha_inicio_penalidad >= hoy:
            return

        # Determinar la fecha desde la que se debe calcular la penalidad
        # Si ya se calculó antes, empezar desde el día siguiente a la última fecha calculada
        # Si no se ha calculado nunca, empezar desde la fecha de inicio de penalidad
        fecha_desde_calculo = cuota.fecha_ultima_penalidad_calculada or fecha_inicio_penalidad
        
        # Asegurarse de no calcular penalidad para el día actual si ya se calculó
        if fecha_desde_calculo < hoy:
            dias_atraso_calculo = (hoy - fecha_desde_calculo).days
            
            # Monto base para la penalidad: monto_cuota menos lo ya pagado de esa cuota
            monto_base_penalidad = cuota.monto_cuota - (cuota.total_pagado if cuota.total_pagado is not None else Decimal('0.00'))
            
            # Asegurarse de que el monto base no sea negativo
            monto_base_penalidad = max(Decimal('0.00'), monto_base_penalidad)

            penalidad_calculada = monto_base_penalidad * tasa_penalidad_diaria * dias_atraso_calculo
            
            cuota.monto_penalidad_acumulada += penalidad_calculada.quantize(Decimal('0.01'))
            cuota.fecha_ultima_penalidad_calculada = hoy
            cuota.save()