from django.shortcuts import render, redirect, get_object_or_404
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Value, DecimalField, Count, F, Q
from django.db.models.functions import Coalesce
from gestion_prestamos.forms import ClienteForm, PrestamoForm, PagoForm, TipoPrestamoForm, GastoPrestamoForm, RequisitoForm, GaranteForm
from gestion_prestamos.models import Prestamo, Cliente, Pago, Cuota, TipoPrestamo, Capital, GastoPrestamo, TipoGasto, Requisito
from django.forms import modelformset_factory
from gestion_prestamos.utils import calcular_tabla_amortizacion, calcular_penalidad_cuota
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import date, timedelta
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
import json

# --- Vistas del Dashboard ---

@login_required
def panel_informativo(request):
    """Muestra el panel principal con datos agregados y métricas financieras."""
    hoy = timezone.now()
    
    # --- MÉTRICAS FINANCIERAS ---
    capital_obj = Capital.objects.first()
    capital_inicial = capital_obj.monto_inicial if capital_obj else Decimal('0.00')

    total_desembolsado = Prestamo.objects.aggregate(total=Coalesce(Sum('monto'), Decimal('0.00')))['total']
    total_recibido = Pago.objects.aggregate(total=Coalesce(Sum('monto_pagado'), Decimal('0.00')))['total']
    
    dinero_en_caja = capital_inicial - total_desembolsado + total_recibido

    cuotas_pagadas = Cuota.objects.filter(estado='pagada')
    ganancia_realizada = cuotas_pagadas.aggregate(total=Coalesce(Sum('interes'), Decimal('0.00')))['total']
    capital_devuelto = cuotas_pagadas.aggregate(total=Coalesce(Sum('capital'), Decimal('0.00')))['total']

    dinero_en_la_calle = total_desembolsado - capital_devuelto

    patrimonio_total = dinero_en_caja + dinero_en_la_calle

    # --- ESTADÍSTICAS GENERALES ---
    total_clientes = Cliente.objects.count()
    total_prestamos_activos = Prestamo.objects.filter(estado='activo').count()
    
    # --- AGENDA DE COBROS AMPLIADA ---
    fecha_hoy = hoy.date()
    fecha_manana = fecha_hoy + timedelta(days=1)
    fecha_semana = fecha_hoy + timedelta(days=7)

    cobros_hoy = Cuota.objects.filter(fecha_vencimiento=fecha_hoy, estado__in=['pendiente', 'pagada_parcialmente'])
    cobros_manana = Cuota.objects.filter(fecha_vencimiento=fecha_manana, estado__in=['pendiente', 'pagada_parcialmente'])
    cobros_proximos_7_dias = Cuota.objects.filter(
        fecha_vencimiento__gt=fecha_manana, 
        fecha_vencimiento__lte=fecha_semana, 
        estado__in=['pendiente', 'pagada_parcialmente']
    ).order_by('fecha_vencimiento')

    context = {
        # Métricas Financieras Reorganizadas
        'patrimonio_total': patrimonio_total,
        'dinero_en_caja': dinero_en_caja,
        'dinero_en_la_calle': dinero_en_la_calle,
        'ganancia_realizada': ganancia_realizada,
        
        # Estadísticas Generales
        'total_clientes': total_clientes,
        'total_prestamos_activos': total_prestamos_activos,
        
        # Agenda de Cobros Ampliada
        'cobros_hoy': cobros_hoy,
        'cobros_manana': cobros_manana,
        'cobros_proximos_7_dias': cobros_proximos_7_dias,

        # Valor para mostrar alerta si no se ha configurado el capital
        'capital_no_configurado': capital_obj is None,
    }
    return render(request, 'dashboard/panel.html', context)

@login_required
def profile(request):
    """Muestra la página de perfil del usuario que ha iniciado sesión."""
    return render(request, 'dashboard/profile.html')

# --- Vistas de Clientes ---

@login_required
def client_list(request):
    """Muestra una lista de todos los clientes registrados con funcionalidad de búsqueda."""
    query = request.GET.get('q')
    if query:
        clientes = Cliente.objects.filter(
            Q(id__icontains=query) |
            Q(nombres__icontains=query) |
            Q(apellidos__icontains=query) |
            Q(cedula__icontains=query)
        ).order_by('-fecha_registro')
    else:
        clientes = Cliente.objects.all().order_by('-fecha_registro')
    
    context = {
        'clientes': clientes,
        'query': query
    }
    return render(request, 'dashboard/client_list.html', context)

@login_required
def client_add(request):
    """Maneja la creación de un nuevo cliente."""
    print("--- client_add view called ---")
    if request.method == 'POST':
        print("--- POST request received ---")
        print("POST data:", request.POST)
        form = ClienteForm(request.POST)
        if form.is_valid():
            print("Form is valid")
            form.save()
            messages.success(request, 'Cliente registrado exitosamente!')
            return redirect('client_list')
        else:
            print("Form is not valid")
            print(form.errors)
    else:
        print("--- GET request received ---")
        form = ClienteForm()
    context = {
        'form': form
    }
    return render(request, 'dashboard/client_form.html', context)

@login_required
def client_edit(request, pk):
    """Maneja la edición de un cliente existente."""
    print("--- client_edit view called ---")
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        print("--- POST request received ---")
        print("POST data:", request.POST)
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            print("Form is valid")
            form.save()
            messages.success(request, 'Cliente actualizado exitosamente!')
            return redirect('client_list')
        else:
            print("Form is not valid")
            print(form.errors)
    else:
        print("--- GET request received ---")
        form = ClienteForm(instance=cliente)
    context = {
        'form': form
    }
    return render(request, 'dashboard/client_form.html', context)


@login_required
def client_detail(request, pk):
    """
    Muestra la página de perfil de un cliente, incluyendo su historial de préstamos.
    """
    cliente = get_object_or_404(Cliente, pk=pk)
    prestamos_cliente = cliente.prestamos.all().order_by('-fecha_desembolso').prefetch_related('cuotas')
    context = {
        'cliente': cliente,
        'prestamos': prestamos_cliente,
    }
    return render(request, 'dashboard/client_detail.html', context)

# --- Vistas de Préstamos ---

@login_required
def loan_add(request):
    """Maneja la creación de un nuevo préstamo, incluyendo gastos y requisitos."""
    GastoFormSet = modelformset_factory(GastoPrestamo, form=GastoPrestamoForm, extra=1, can_delete=True)
    RequisitoFormSet = modelformset_factory(Requisito, form=RequisitoForm, extra=0, can_delete=True)

    if request.method == 'POST':
        print("--- loan_add view: POST request received ---")
        form = PrestamoForm(request.POST)
        gasto_formset = GastoFormSet(request.POST, queryset=GastoPrestamo.objects.none(), prefix='gastos')
        requisito_formset = RequisitoFormSet(request.POST, queryset=Requisito.objects.none(), prefix='requisitos')
        garante_form = GaranteForm(request.POST)

        form_is_valid = form.is_valid()
        gasto_formset_is_valid = gasto_formset.is_valid()
        requisito_formset_is_valid = requisito_formset.is_valid()

        print(f"--- loan_add view: form.is_valid() -> {form_is_valid} ---")
        print(f"--- loan_add view: gasto_formset.is_valid() -> {gasto_formset_is_valid} ---")
        print(f"--- loan_add view: requisito_formset.is_valid() -> {requisito_formset_is_valid} ---")

        if form_is_valid and gasto_formset_is_valid and requisito_formset_is_valid:
            print("--- loan_add view: All forms are valid, proceeding with further validations ---")
            tipo_prestamo = form.cleaned_data.get('tipo_prestamo')
            monto_solicitado = form.cleaned_data['monto']

            # Validar garante si el monto es < 100,000
            if monto_solicitado < 100000:
                print("--- loan_add view: Loan amount is less than 100,000, validating guarantor form ---")
                if not garante_form.is_valid():
                    print("--- loan_add view: Guarantor form is NOT valid ---")
                    print(garante_form.errors)
                    messages.error(request, 'El formulario del garante no es válido. Por favor, revisa los campos.')
                    context = {'form': form, 'gasto_formset': gasto_formset, 'requisito_formset': requisito_formset, 'garante_form': garante_form}
                    return render(request, 'dashboard/loan_form.html', context)
                else:
                    print("--- loan_add view: Guarantor form is valid ---")

            # Validar que si el tipo de préstamo requiere garantía, se provea al menos una.
            if tipo_prestamo and tipo_prestamo.requiere_garantia:
                if not any(form.cleaned_data and not form.cleaned_data.get('DELETE') for form in requisito_formset):
                    messages.error(request, f'El tipo de préstamo "{tipo_prestamo.nombre}" requiere al menos un requisito o garantía.')
                    context = {'form': form, 'gasto_formset': gasto_formset, 'requisito_formset': requisito_formset, 'garante_form': garante_form}
                    return render(request, 'dashboard/loan_form.html', context)

            total_gastos = Decimal('0.00')
            for gasto_form in gasto_formset.cleaned_data:
                if gasto_form and not gasto_form.get('DELETE') and 'monto' in gasto_form:
                    total_gastos += gasto_form['monto']

            prestamo = form.save(commit=False)
            prestamo.total_gastos_asociados = total_gastos

            if prestamo.manejo_gastos == 'sumar_al_capital':
                prestamo.monto = monto_solicitado + total_gastos
                prestamo.monto_desembolsado = monto_solicitado
            else: # restar_del_desembolso
                prestamo.monto = monto_solicitado
                prestamo.monto_desembolsado = monto_solicitado - total_gastos

            # Guardar garante si es necesario
            if monto_solicitado < 100000:
                garante = garante_form.save()
                prestamo.garante = garante

            prestamo.save()

            # Guardar gastos
            for gasto_form in gasto_formset:
                if gasto_form.is_valid() and gasto_form.cleaned_data and not gasto_form.cleaned_data.get('DELETE'):
                    gasto = gasto_form.save(commit=False)
                    gasto.prestamo = prestamo
                    gasto.save()

            # Guardar requisitos/garantías
            for requisito_form in requisito_formset:
                if requisito_form.is_valid() and requisito_form.cleaned_data and not requisito_form.cleaned_data.get('DELETE'):
                    requisito = requisito_form.save(commit=False)
                    requisito.prestamo = prestamo
                    requisito.save()

            tabla_amortizacion = calcular_tabla_amortizacion(prestamo)
            for item_cuota in tabla_amortizacion:
                Cuota.objects.create(
                    prestamo=prestamo,
                    numero_cuota=item_cuota['numero_cuota'],
                    fecha_vencimiento=item_cuota['fecha_vencimiento'],
                    monto_cuota=item_cuota['cuota_fija'],
                    capital=item_cuota['capital'],
                    interes=item_cuota['interes'],
                    saldo_pendiente=item_cuota['saldo_pendiente']
                )
            
            messages.success(request, f'¡Éxito! Préstamo de ${prestamo.monto:,.2f} para {prestamo.cliente.nombres} {prestamo.cliente.apellidos} ha sido registrado correctamente.')
            return redirect('loan_list')
        else:
            # Mensaje de error principal más explícito
            error_count = len(form.errors) + len(gasto_formset.errors) + len(requisito_formset.errors)
            if garante_form.errors:
                error_count += len(garante_form.errors)
            messages.error(request, f'El formulario no es válido. Se encontraron {error_count} error(es). Por favor, revisa los campos marcados.')
            
            # Mensajes de advertencia para cada sección con errores
            if form.errors:
                messages.warning(request, 'Hay errores en la sección de Detalles del Préstamo.')
            if gasto_formset.errors:
                messages.warning(request, 'Hay errores en la sección de Gastos Asociados.')
            if requisito_formset.errors:
                messages.warning(request, 'Hay errores en la sección de Requisitos y Garantías.')
            if garante_form.errors:
                messages.warning(request, 'Hay errores en la sección de Información del Garante.')

            context = {'form': form, 'gasto_formset': gasto_formset, 'requisito_formset': requisito_formset, 'garante_form': garante_form}
            return render(request, 'dashboard/loan_form.html', context)

    else: # GET request
        form = PrestamoForm()
        gasto_formset = GastoFormSet(queryset=GastoPrestamo.objects.none(), prefix='gastos')
        requisito_formset = RequisitoFormSet(queryset=Requisito.objects.none(), prefix='requisitos')
        garante_form = GaranteForm()

    context = {
        'form': form,
        'gasto_formset': gasto_formset,
        'requisito_formset': requisito_formset,
        'garante_form': garante_form
    }
    return render(request, 'dashboard/loan_form.html', context)

@login_required
def loan_detail(request, pk):
    """Muestra los detalles de un préstamo específico y sus cuotas."""
    prestamo = get_object_or_404(Prestamo, pk=pk)
    cuotas = prestamo.cuotas.all().order_by('numero_cuota')
    total_pagado = Pago.objects.filter(cuota__prestamo=prestamo).aggregate(
        total=Coalesce(Sum('monto_pagado'), Value(0), output_field=DecimalField())
    )['total']
    ganancia_potencial = cuotas.aggregate(
        total_interes=Coalesce(Sum('interes'), Value(0), output_field=DecimalField())
    )['total_interes']

    total_faltante = Decimal('0.00')
    total_penalidades_acumuladas = Decimal('0.00')
    for cuota in cuotas:
        calcular_penalidad_cuota(cuota)
        total_penalidades_acumuladas += cuota.monto_penalidad_acumulada
        if cuota.estado != 'pagada':
            cuota_total_pagado = cuota.total_pagado if cuota.total_pagado is not None else Decimal('0.00')
            total_faltante += (cuota.monto_cuota - cuota_total_pagado)

    context = {
        'el_prestamo_actual': prestamo,
        'cuotas_del_prestamo': cuotas,
        'pago_total_realizado': total_pagado,
        'ganancia_estimada': ganancia_potencial,
        'total_faltante': total_faltante,
        'total_penalidades_acumuladas': total_penalidades_acumuladas,
    }
    return render(request, 'dashboard/loan_detail.html', context)

@login_required
def loan_list(request):
    """Muestra una lista de todos los préstamos activos con funcionalidad de búsqueda."""
    query = request.GET.get('q')
    prestamos = Prestamo.objects.filter(estado='activo').select_related('cliente').order_by('-fecha_creacion')
    if query:
        prestamos = prestamos.filter(
            Q(id__icontains=query) |
            Q(cliente__nombres__icontains=query) |
            Q(cliente__apellidos__icontains=query) |
            Q(cliente__cedula__icontains=query)
        )
    context = {
        'prestamos': prestamos,
        'query': query
    }
    return render(request, 'dashboard/loan_list.html', context)

@login_required
def paid_loan_list(request):
    """Muestra una lista de todos los préstamos pagados con funcionalidad de búsqueda."""
    query = request.GET.get('q')
    prestamos = Prestamo.objects.filter(estado='pagado').select_related('cliente').order_by('-fecha_creacion')
    if query:
        prestamos = prestamos.filter(
            Q(id__icontains=query) |
            Q(cliente__nombres__icontains=query) |
            Q(cliente__apellidos__icontains=query) |
            Q(cliente__cedula__icontains=query)
        )
    context = {
        'prestamos': prestamos,
        'query': query,
        'page_title': 'Préstamos Pagados'
    }
    return render(request, 'dashboard/loan_list.html', context)

# --- Vistas de Pagos ---

@login_required
def payment_add(request, loan_id):
    """Maneja el registro de un pago."""
    prestamo = get_object_or_404(Prestamo, pk=loan_id)
    if request.method == 'POST':
        form = PagoForm(request.POST)
        if form.is_valid():
            monto_pagado = form.cleaned_data['monto_pagado']
            prestamo.registrar_pago(monto_pagado)
            messages.success(request, f'Pago de ${monto_pagado} registrado exitosamente.')
            if prestamo.estado == 'pagado':
                messages.info(request, f'¡Felicidades! El préstamo #{prestamo.id} ha sido completamente saldado.')
            return redirect('loan_detail', pk=prestamo.pk)
    else:
        form = PagoForm()
    context = {
        'form': form,
        'prestamo': prestamo
    }
    return render(request, 'dashboard/payment_form.html', context)


@login_required
def cobros_list(request):
    """Muestra una lista de todas las cuotas vencidas y no pagadas."""
    hoy = timezone.now()
    cuotas_vencidas = Cuota.objects.filter(fecha_vencimiento__lt=hoy, estado='pendiente').annotate(
        dias_vencido=hoy - F('fecha_vencimiento')
    ).order_by('fecha_vencimiento')
    context = {
        'cuotas_vencidas': cuotas_vencidas
    }
    return render(request, 'dashboard/cobros_list.html', context)

# --- Vistas para Select2 AJAX ---

@login_required
def search_clients(request):
    term = request.GET.get('term', '')
    clientes = Cliente.objects.filter(
        Q(id__icontains=term) |
        Q(nombres__icontains=term) |
        Q(apellidos__icontains=term) |
        Q(numero_documento__icontains=term)
    )[:20]
    results = [
        {
            'id': cliente.id,
            'text': f'{cliente.nombres} {cliente.apellidos} ({cliente.get_tipo_documento_display()}: {cliente.numero_documento})'
        }
        for cliente in clientes
    ]
    return JsonResponse({'results': results})

@login_required
def search_cuotas(request):
    term = request.GET.get('term', '')
    loan_id = request.GET.get('loan_id')
    cuotas = Cuota.objects.filter(estado='pendiente')
    if loan_id:
        cuotas = cuotas.filter(prestamo_id=loan_id)
    if term:
        cuotas = cuotas.filter(
            Q(prestamo__cliente__nombres__icontains=term) |
            Q(prestamo__cliente__apellidos__icontains=term) |
            Q(prestamo__id__icontains=term) |
            Q(numero_cuota__icontains=term)
        )
    cuotas = cuotas[:20]
    results = [
        {
            'id': cuota.id,
            'text': f'Cuota #{cuota.numero_cuota} - {cuota.prestamo.cliente} (Préstamo #{cuota.prestamo.id})'
        }
        for cuota in cuotas
    ]
    return JsonResponse({'results': results})

# --- API Views ---

@login_required
def get_tipo_prestamo_details(request, pk):
    """Devuelve los detalles de un tipo de préstamo en formato JSON."""
    tipo_prestamo = get_object_or_404(TipoPrestamo, pk=pk)
    data = {
        'tasa_interes_predeterminada': str(tipo_prestamo.tasa_interes_predeterminada),
        'monto_minimo': str(tipo_prestamo.monto_minimo),
        'monto_maximo': str(tipo_prestamo.monto_maximo),
        'plazo_minimo_meses': tipo_prestamo.plazo_minimo_meses,
        'plazo_maximo_meses': tipo_prestamo.plazo_maximo_meses,
        'requiere_garantia': tipo_prestamo.requiere_garantia,
    }
    return JsonResponse(data)


@login_required
def calculate_amortization_api(request):
    if request.method == 'POST':
        form = PrestamoForm(request.POST)
        if form.is_valid():
            # Crear un objeto Prestamo temporal sin guardarlo en la BD
            prestamo = form.save(commit=False)
            try:
                tabla_amortizacion = calcular_tabla_amortizacion(prestamo)
                # Convertir objetos Decimal y date a string para la serialización JSON
                for cuota in tabla_amortizacion:
                    for key, value in cuota.items():
                        if isinstance(value, Decimal):
                            cuota[key] = f'{value:,.2f}'
                        elif isinstance(value, date):
                            cuota[key] = value.strftime('%Y-%m-%d')
                return JsonResponse({'amortization_table': tabla_amortizacion})
            except Exception as e:
                return JsonResponse({'error': f'Error al calcular la amortización: {str(e)}'}, status=400)
        else:
            # Si el formulario no es válido, devolver los errores
            return JsonResponse({'error': 'Formulario inválido', 'errors': form.errors}, status=400)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def financial_details(request):
    """Muestra una página con un desglose detallado de las métricas financieras."""
    capital_obj = Capital.objects.first()
    capital_inicial = capital_obj.monto_inicial if capital_obj else Decimal('0.00')
    total_desembolsado = Prestamo.objects.aggregate(total=Coalesce(Sum('monto'), Decimal('0.00')))['total']
    total_recibido_pagos = Pago.objects.aggregate(total=Coalesce(Sum('monto_pagado'), Decimal('0.00')))['total']
    dinero_en_caja = capital_inicial - total_desembolsado + total_recibido_pagos
    cuotas_pagadas = Cuota.objects.filter(estado='pagada')
    capital_devuelto = cuotas_pagadas.aggregate(total=Coalesce(Sum('capital'), Decimal('0.00')))['total']
    ganancia_realizada = cuotas_pagadas.aggregate(total=Coalesce(Sum('interes'), Decimal('0.00')))['total']
    cartera_activa = total_desembolsado - capital_devuelto
    ganancia_potencial = Cuota.objects.filter(
        prestamo__estado='activo', 
        estado__in=['pendiente', 'pagada_parcialmente']
    ).aggregate(total=Coalesce(Sum('interes'), Decimal('0.00')))['total']
    num_prestamos_activos = Prestamo.objects.filter(estado='activo').count()
    num_prestamos_pagados = Prestamo.objects.filter(estado='pagado').count()
    hoy = timezone.now()
    prestamos_en_atraso = Prestamo.objects.filter(
        estado='activo',
        cuotas__fecha_vencimiento__lt=hoy,
        cuotas__estado__in=['pendiente', 'pagada_parcialmente']
    ).distinct().count()
    total_prestamos = Prestamo.objects.count()
    monto_promedio = total_desembolsado / total_prestamos if total_prestamos > 0 else Decimal('0.00')
    pagos_recientes = Pago.objects.order_by('-fecha_pago')[:10]
    prestamos_recientes = Prestamo.objects.order_by('-fecha_desembolso')[:5]
    context = {
        'capital_inicial': capital_inicial,
        'total_desembolsado': total_desembolsado,
        'total_recibido_pagos': total_recibido_pagos,
        'dinero_en_caja': dinero_en_caja,
        'cartera_activa': cartera_activa,
        'ganancia_realizada': ganancia_realizada,
        'ganancia_potencial': ganancia_potencial,
        'num_prestamos_activos': num_prestamos_activos,
        'num_prestamos_pagados': num_prestamos_pagados,
        'num_prestamos_en_atraso': prestamos_en_atraso,
        'monto_promedio': monto_promedio,
        'pagos_recientes': pagos_recientes,
        'prestamos_recientes': prestamos_recientes,
    }
    return render(request, 'dashboard/financial_details.html', context)

# --- Vistas del Portal de Clientes ---

def client_login(request):
    if request.user.is_authenticated:
        logout(request)

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_staff:
                    messages.error(request, "Las credenciales son correctas, pero esta sección es solo para clientes.")
                    logout(request)
                    return redirect('client_login')
                else:
                    login(request, user)
                    return redirect('portal_dashboard')
            else:
                messages.error(request, "Número de documento o contraseña incorrectos. Por favor, inténtalo de nuevo.")
        else:
            # Si el formulario no es válido, los errores de campo se mostrarán automáticamente.
            pass
    else:
        form = AuthenticationForm()
    return render(request, 'portal/login.html', {'form': form})

@login_required
def portal_dashboard(request):
    """Muestra un panel de control mejorado para el cliente."""
    if request.user.is_staff:
        return redirect('panel_informativo')

    try:
        cliente = request.user.cliente_profile
    except Cliente.DoesNotExist:
        return redirect('client_login')

    # Obtener todos los préstamos del cliente
    prestamos = Prestamo.objects.filter(cliente=cliente).order_by('-fecha_desembolso')
    
    # Encontrar el préstamo activo y su información relevante
    prestamo_activo = prestamos.filter(estado='activo').first()
    proxima_cuota = None
    saldo_pendiente_total = Decimal('0.00')

    if prestamo_activo:
        # Usamos todas las cuotas para el saldo, pero solo las pendientes para la próxima cuota
        todas_las_cuotas = prestamo_activo.cuotas.all()
        cuotas_pendientes = todas_las_cuotas.filter(estado__in=['pendiente', 'pagada_parcialmente']).order_by('fecha_vencimiento')
        proxima_cuota = cuotas_pendientes.first()
        
        for cuota in todas_las_cuotas:
            saldo_pendiente_total += (cuota.monto_cuota - cuota.total_pagado)

    context = {
        'cliente': cliente,
        'prestamos': prestamos,
        'prestamo_activo': prestamo_activo,
        'proxima_cuota': proxima_cuota,
        'saldo_pendiente_total': saldo_pendiente_total,
    }
    return render(request, 'portal/dashboard.html', context)

class ClientPasswordChangeView(PasswordChangeView):
    template_name = 'portal/change_password_form.html'
    success_url = reverse_lazy('portal_dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        try:
            cliente = self.request.user.cliente_profile
            if cliente.debe_cambiar_contrasena:
                cliente.debe_cambiar_contrasena = False
                cliente.save()
                messages.success(self.request, 'Tu contraseña ha sido cambiada exitosamente. Ya puedes navegar por el portal.')
        except AttributeError:
            pass
        return response

client_change_password = ClientPasswordChangeView.as_view()

@login_required
def portal_loan_detail(request, pk):
    """Muestra la tabla de amortización detallada de un préstamo específico para el cliente."""
    if request.user.is_staff:
        return redirect('panel_informativo')

    try:
        cliente = request.user.cliente_profile
        # Se asegura de que el préstamo que se busca le pertenezca al cliente logueado
        prestamo = get_object_or_404(Prestamo, pk=pk, cliente=cliente)
    except (Cliente.DoesNotExist, Prestamo.DoesNotExist):
        return redirect('portal_dashboard')

    cuotas = prestamo.cuotas.all().order_by('numero_cuota')
    context = {
        'prestamo': prestamo,
        'cuotas': cuotas,
    }
    return render(request, 'portal/loan_detail.html', context)

def client_logout_view(request):
    """Cierra la sesión del cliente y muestra un mensaje de éxito."""
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente. ¡Vuelve pronto!')
    return redirect('client_login')
