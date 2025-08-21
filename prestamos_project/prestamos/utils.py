import datetime
from decimal import Decimal

def calcular_tabla_amortizacion(prestamo):
    """
    Calcula la tabla de amortización para un préstamo dado.

    Args:
        prestamo (Prestamo): El objeto Prestamo para el cual calcular la tabla.

    Returns:
        list: Una lista de diccionarios, donde cada diccionario representa una cuota.
    """
    
    monto_pendiente = prestamo.monto
    tasa_interes_anual = prestamo.tasa_interes / Decimal(100) # Convertir a decimal y porcentaje
    plazo_meses = prestamo.plazo
    fecha_inicio = prestamo.fecha_desembolso
    frecuencia = prestamo.frecuencia_pago

    tabla_amortizacion = []

    if frecuencia == 'mensual':
        pagos_por_anio = 12
        tasa_interes_periodo = tasa_interes_anual / Decimal(pagos_por_anio)
        numero_pagos = plazo_meses
        
        # Calcular la cuota fija mensual (Método Francés)
        if tasa_interes_periodo > 0:
            cuota_fija = (monto_pendiente * tasa_interes_periodo) / (1 - (1 + tasa_interes_periodo)**(-numero_pagos))
        else:
            cuota_fija = monto_pendiente / numero_pagos

        for i in range(1, numero_pagos + 1):
            interes_periodo = monto_pendiente * tasa_interes_periodo
            capital_periodo = cuota_fija - interes_periodo
            monto_pendiente -= capital_periodo

            # Asegurarse de que el último pago ajuste el saldo a cero
            if i == numero_pagos:
                capital_periodo += monto_pendiente # Ajustar el capital para que el saldo sea 0
                monto_pendiente = Decimal(0)
            
            # Calcular fecha de vencimiento
            fecha_vencimiento = fecha_inicio + datetime.timedelta(days=30 * i) # Aproximación mensual
            # Ajuste para el mes correcto
            target_month = (fecha_inicio.month + i - 1) % 12 + 1
            target_year = fecha_inicio.year + (fecha_inicio.month + i - 1) // 12
            # Intentar mantener el día, si no es posible, usar el último día del mes
            try:
                fecha_vencimiento = datetime.date(target_year, target_month, fecha_inicio.day)
            except ValueError:
                fecha_vencimiento = datetime.date(target_year, target_month, 1) + datetime.timedelta(days=-1)

            tabla_amortizacion.append({
                'numero_cuota': i,
                'fecha_vencimiento': fecha_vencimiento,
                'cuota_fija': cuota_fija.quantize(Decimal('0.01')),
                'interes': interes_periodo.quantize(Decimal('0.01')),
                'capital': capital_periodo.quantize(Decimal('0.01')),
                'saldo_pendiente': monto_pendiente.quantize(Decimal('0.01')),
            })

    elif frecuencia == 'quincenal':
        pagos_por_anio = 24 # 24 quincenas en un año
        tasa_interes_periodo = tasa_interes_anual / Decimal(pagos_por_anio)
        numero_pagos = plazo_meses * 2 # 2 quincenas por mes

        if tasa_interes_periodo > 0:
            cuota_fija = (monto_pendiente * tasa_interes_periodo) / (1 - (1 + tasa_interes_periodo)**(-numero_pagos))
        else:
            cuota_fija = monto_pendiente / numero_pagos

        for i in range(1, numero_pagos + 1):
            interes_periodo = monto_pendiente * tasa_interes_periodo
            capital_periodo = cuota_fija - interes_periodo
            monto_pendiente -= capital_periodo

            if i == numero_pagos:
                capital_periodo += monto_pendiente
                monto_pendiente = Decimal(0)
            
            # Calcular fecha de vencimiento (aproximación quincenal)
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
