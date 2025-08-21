from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Value, DecimalField, Count, F
from django.db.models.functions import Coalesce
from prestamos.models import Prestamo, Cliente, Pago, Cuota
from prestamos.forms import ClienteForm, PrestamoForm, PagoForm
from prestamos.utils import calcular_tabla_amortizacion
from django.contrib import messages
from datetime import date, timedelta

# --- Vistas del Dashboard ---

@login_required
def panel_informativo(request):
    """Muestra el panel principal con datos agregados de los préstamos."""
    hoy = date.today()
    manana = hoy + timedelta(days=1)

    # Indicadores clave usando consultas eficientes a la BD
    total_prestado_activo = Prestamo.objects.filter(estado='activo').aggregate(
        total=Coalesce(Sum('monto'), Value(0), output_field=DecimalField())
    )['total']
    
    total_clientes = Cliente.objects.count()

    ganancias_totales = Pago.objects.aggregate(
        total_interes=Coalesce(Sum('cuota__interes'), Value(0), output_field=DecimalField())
    )['total_interes']

    # Consultas directas al modelo Cuota para mayor eficiencia
    cobros_hoy = Cuota.objects.filter(fecha_vencimiento=hoy, estado='pendiente')
    cobros_manana = Cuota.objects.filter(fecha_vencimiento=manana, estado='pendiente')
    
    # Últimos pagos registrados
    ingresos_recientes = Pago.objects.order_by('-fecha_pago')[:5]

    context = {
        'total_prestado_activo': total_prestado_activo,
        'ganancias_totales': ganancias_totales,
        'total_clientes': total_clientes,
        'cobros_hoy': cobros_hoy,
        'cobros_manana': cobros_manana,
        'ingresos_recientes': ingresos_recientes,
    }
    return render(request, 'dashboard/panel.html', context)

@login_required
def profile(request):
    """Muestra la página de perfil del usuario que ha iniciado sesión."""
    return render(request, 'dashboard/profile.html')

# --- Vistas de Clientes ---

@login_required
def client_list(request):
    """Muestra una lista de todos los clientes registrados."""
    clientes = Cliente.objects.all().order_by('-fecha_registro')
    context = {
        'clientes': clientes
    }
    return render(request, 'dashboard/client_list.html', context)

@login_required
def client_add(request):
    """Maneja la creación de un nuevo cliente."""
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente registrado exitosamente!')
            return redirect('client_list')
    else:
        form = ClienteForm()
    context = {
        'form': form
    }
    return render(request, 'dashboard/client_form.html', context)

@login_required
def client_edit(request, pk):
    """Maneja la edición de un cliente existente."""
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado exitosamente!')
            return redirect('client_list')
    else:
        form = ClienteForm(instance=cliente)
    context = {
        'form': form
    }
    return render(request, 'dashboard/client_form.html', context)

# --- Vistas de Préstamos ---

@login_required
def loan_add(request):
    """Maneja la creación de un nuevo préstamo y genera su tabla de amortización."""
    if request.method == 'POST':
        form = PrestamoForm(request.POST)
        if form.is_valid():
            prestamo = form.save()
            # Al crear un préstamo, generamos y guardamos su plan de pagos (cuotas) en la BD.
            tabla_amortizacion = calcular_tabla_amortizacion(prestamo)
            for item_cuota in tabla_amortizacion:
                Cuota.objects.create(
                    prestamo=prestamo,
                    numero_cuota=item_cuota['numero_cuota'],
                    fecha_vencimiento=item_cuota['fecha_vencimiento'],
                    monto_cuota=item_cuota['cuota_fija'],
                    capital=item_cuota['abono_capital'],
                    interes=item_cuota['interes'],
                    saldo_pendiente=item_cuota['saldo_restante']
                )
            messages.success(request, 'Préstamo registrado y tabla de amortización generada exitosamente!')
            return redirect('panel_informativo')
    else:
        form = PrestamoForm()
    context = {
        'form': form
    }
    return render(request, 'dashboard/loan_form.html', context)

@login_required
def loan_detail(request, pk):
    """Muestra los detalles de un préstamo específico y sus cuotas."""
    prestamo = get_object_or_404(Prestamo, pk=pk)
    
    # Las cuotas ya están en la base de datos, solo las consultamos.
    cuotas = prestamo.cuotas.all().order_by('numero_cuota')
    
    # Calculamos el total pagado para este préstamo.
    total_pagado = Pago.objects.filter(cuota__prestamo=prestamo).aggregate(
        total=Coalesce(Sum('monto_pagado'), Value(0), output_field=DecimalField())
    )['total']
    
    # Calculamos la ganancia potencial total sumando los intereses de todas las cuotas.
    ganancia_potencial = cuotas.aggregate(
        total_interes=Coalesce(Sum('interes'), Value(0), output_field=DecimalField())
    )['total_interes']

    context = {
        'prestamo': prestamo,
        'cuotas': cuotas,
        'total_pagado': total_pagado,
        'ganancia_potencial': ganancia_potencial,
    }
    return render(request, 'dashboard/loan_detail.html', context)

@login_required
def loan_list(request):
    """Muestra una lista de todos los préstamos activos."""
    prestamos = Prestamo.objects.filter(estado='activo').order_by('-fecha_creacion')
    context = {
        'prestamos': prestamos
    }
    return render(request, 'dashboard/loan_list.html', context)

# --- Vistas de Pagos ---

@login_required
def payment_add(request):
    """Maneja el registro de un nuevo pago para una cuota."""
    if request.method == 'POST':
        form = PagoForm(request.POST)
        if form.is_valid():
            pago = form.save(commit=False)
            cuota_a_pagar = pago.cuota
            
            # Si el pago es igual o mayor al monto de la cuota, la marcamos como pagada.
            if pago.monto_pagado >= cuota_a_pagar.monto_cuota:
                cuota_a_pagar.estado = 'pagada'
            
            cuota_a_pagar.save()
            pago.save()
            
            # Verificamos si todas las cuotas del préstamo están pagadas para actualizar el estado del préstamo.
            prestamo_asociado = cuota_a_pagar.prestamo
            if not prestamo_asociado.cuotas.filter(estado='pendiente').exists():
                prestamo_asociado.estado = 'pagado'
                prestamo_asociado.save()

            messages.success(request, 'Pago registrado exitosamente!')
            return redirect('loan_detail', pk=prestamo_asociado.pk)
    else:
        form = PagoForm()
        # Pre-seleccionar la cuota si su ID viene en la URL (ej. desde un botón de 'Pagar').
        cuota_id = request.GET.get('cuota_id')
        if cuota_id:
            form.fields['cuota'].initial = cuota_id

    context = {
        'form': form
    }
    return render(request, 'dashboard/payment_form.html', context)


@login_required
def cobros_list(request):
    """Muestra una lista de todas las cuotas vencidas y no pagadas."""
    hoy = date.today()
    
    # Usamos una consulta directa y eficiente para obtener las cuotas vencidas.
    cuotas_vencidas = Cuota.objects.filter(fecha_vencimiento__lt=hoy, estado='pendiente').annotate(
        dias_vencido=hoy - F('fecha_vencimiento') # Calculamos los días de vencimiento en la BD.
    ).order_by('fecha_vencimiento')

    context = {
        'cuotas_vencidas': cuotas_vencidas
    }
    return render(request, 'dashboard/cobros_list.html', context)