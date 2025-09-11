from django import forms
from .models import Cliente, Prestamo, Pago, Cuota, TipoPrestamo, GastoPrestamo, TipoGasto, Requisito, Garante
from django_select2.forms import Select2Widget
from datetime import date
import re

# Django ModelForm para el modelo Cliente.
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'nombres',
            'apellidos',
            'apodo',
            'sexo',
            'estado_civil',
            'fecha_nacimiento',
            'tipo_documento',
            'numero_documento',
            'direccion',
            'telefono',
            'email',
            'nombre_empresa',
            'cargo',
            'telefono_trabajo',
            'ingresos_mensuales',
            'fecha_ingreso_trabajo',
            'trabajo_actual',
        ]
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'apodo': forms.TextInput(attrs={'class': 'form-control'}),
            'sexo': forms.Select(attrs={'class': 'form-control'}),
            'estado_civil': forms.Select(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nombre_empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_trabajo': forms.TextInput(attrs={'class': 'form-control'}),
            'ingresos_mensuales': forms.NumberInput(attrs={'class': 'form-control'}),
            'fecha_ingreso_trabajo': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'trabajo_actual': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_nombres(self):
        nombres = self.cleaned_data.get('nombres')
        if nombres and any(char.isdigit() for char in nombres):
            raise forms.ValidationError("El nombre no debe contener números.")
        return nombres

    def clean_apellidos(self):
        apellidos = self.cleaned_data.get('apellidos')
        if apellidos and any(char.isdigit() for char in apellidos):
            raise forms.ValidationError("Los apellidos no deben contener números.")
        return apellidos

    def clean(self):
        cleaned_data = super().clean()
        tipo_documento = cleaned_data.get('tipo_documento')
        numero_documento = cleaned_data.get('numero_documento')

        if tipo_documento == 'cedula':
            if not numero_documento or not (numero_documento.isdigit() and len(numero_documento) == 11):
                self.add_error('numero_documento', "La cédula debe contener exactamente 11 dígitos numéricos.")
        elif tipo_documento == 'pasaporte':
            if not numero_documento or not len(numero_documento) == 8:
                self.add_error('numero_documento', "El pasaporte debe contener exactamente 8 caracteres.")

        # Comprobar si el número de documento ya existe
        if numero_documento and Cliente.objects.filter(numero_documento=numero_documento).exclude(pk=self.instance.pk).exists():
            self.add_error('numero_documento', "Ya existe un cliente registrado con este número de documento.")
            
        return cleaned_data

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono and Cliente.objects.filter(telefono=telefono).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ya existe un cliente registrado con este número de teléfono.")
        return telefono

# Formulario para el nuevo modelo TipoPrestamo
class TipoPrestamoForm(forms.ModelForm):
    class Meta:
        model = TipoPrestamo
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tasa_interes_predeterminada': forms.NumberInput(attrs={'class': 'form-control'}),
            'periodo_tasa': forms.Select(attrs={'class': 'form-control'}),
            'monto_minimo': forms.NumberInput(attrs={'class': 'form-control'}),
            'monto_maximo': forms.NumberInput(attrs={'class': 'form-control'}),
            'plazo_maximo_meses': forms.NumberInput(attrs={'class': 'form-control'}),
            'metodo_calculo': forms.Select(attrs={'class': 'form-control'}),
            'comision_por_desembolso': forms.NumberInput(attrs={'class': 'form-control'}),
        }

# Django ModelForm para el modelo Prestamo.
class PrestamoForm(forms.ModelForm):
    class Meta:
        model = Prestamo
        fields = [
            'cliente',
            'tipo_prestamo',
            'monto',
            'tasa_interes',
            'periodo_tasa',
            'plazo',
            'fecha_desembolso',
            'frecuencia_pago',
            'tipo_amortizacion',
            'tasa_mora',
            'fecha_inicio_pago',
            'manejo_gastos',
        ]
        widgets = {
            'cliente': Select2Widget(
                attrs={
                    'class': 'form-control',
                    'data-ajax--url': '/search/clients/',
                    'data-placeholder': 'Busca un cliente por nombre, cédula o ID...'
                }
            ),
            'tipo_prestamo': forms.Select(attrs={'class': 'form-control'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tasa_interes': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'periodo_tasa': forms.Select(attrs={'class': 'form-control'}),
            'plazo': forms.NumberInput(attrs={'class': 'form-control'}),
            'fecha_desembolso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'frecuencia_pago': forms.Select(attrs={'class': 'form-control'}),
            'tipo_amortizacion': forms.Select(attrs={'class': 'form-control'}),
            'tasa_mora': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fecha_inicio_pago': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'manejo_gastos': forms.RadioSelect(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'monto': 'Monto Solicitado por el Cliente',
            'tasa_interes': 'Tasa de Interés',
            'periodo_tasa': 'Período de la Tasa',
            'tasa_mora': 'Tasa de Mora',
            'fecha_inicio_pago': 'Fecha de Inicio de Pago',
            'tipo_amortizacion': 'Tipo de Amortización',
            'manejo_gastos': 'Manejo de Gastos Adicionales',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['tipo_prestamo'].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        cliente = cleaned_data.get("cliente")
        tipo_prestamo = cleaned_data.get("tipo_prestamo")
        monto = cleaned_data.get("monto")
        plazo = cleaned_data.get("plazo")

        if not tipo_prestamo:
            raise forms.ValidationError("Debe seleccionar un tipo de préstamo.")

        if monto is not None:
            if monto < tipo_prestamo.monto_minimo:
                self.add_error('monto', f"El monto para el tipo de préstamo '{tipo_prestamo.nombre}' debe ser de al menos ${tipo_prestamo.monto_minimo:,.2f}.")
            if monto > tipo_prestamo.monto_maximo:
                self.add_error('monto', f"El monto para el tipo de préstamo '{tipo_prestamo.nombre}' no puede exceder los ${tipo_prestamo.monto_maximo:,.2f}.")

        if plazo is not None:
            if plazo < tipo_prestamo.plazo_minimo_meses:
                self.add_error('plazo', f"El plazo para el tipo de préstamo '{tipo_prestamo.nombre}' debe ser de al menos {tipo_prestamo.plazo_minimo_meses} meses.")
            if plazo > tipo_prestamo.plazo_maximo_meses:
                self.add_error('plazo', f"El plazo para el tipo de préstamo '{tipo_prestamo.nombre}' no puede exceder los {tipo_prestamo.plazo_maximo_meses} meses.")

        is_new = self.instance.pk is None
        if cliente and is_new:
            if Prestamo.objects.filter(cliente=cliente, estado='activo').exists():
                raise forms.ValidationError(
                    f"El cliente {cliente} ya tiene un préstamo activo. No se puede registrar uno nuevo hasta que el anterior sea saldado."
                )
        
        return cleaned_data

class GastoPrestamoForm(forms.ModelForm):
    class Meta:
        model = GastoPrestamo
        fields = ['tipo_gasto', 'monto', 'descripcion']
        widgets = {
            'tipo_gasto': forms.Select(attrs={'class': 'form-select', 'data-placeholder': 'Seleccione un tipo de gasto'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Monto del gasto'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descripción detallada'}),
        }
        labels = {
            'tipo_gasto': 'Tipo de Gasto',
            'monto': 'Monto',
            'descripcion': 'Detalle',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo_gasto'].required = False
        self.fields['monto'].required = False
        self.fields['descripcion'].required = False

    def clean(self):
        cleaned_data = super().clean()
        
        # No validar si el formulario está marcado para eliminación
        if cleaned_data.get('DELETE', False):
            return cleaned_data

        tipo_gasto = cleaned_data.get('tipo_gasto')
        monto = cleaned_data.get('monto')

        # Si el formulario está completamente vacío (sin datos ingresados), es válido.
        if not self.has_changed():
            return cleaned_data
        
        # Si un campo se llena, los otros dos también deben llenarse.
        if tipo_gasto and not monto:
            self.add_error('monto', 'Debe ingresar un monto si selecciona un tipo de gasto.')
        if monto and not tipo_gasto:
            self.add_error('tipo_gasto', 'Debe seleccionar un tipo de gasto si ingresa un monto.')

        # Si el formulario no está vacío, al menos el tipo y el monto son obligatorios.
        if self.has_changed() and (not tipo_gasto or not monto):
            if not tipo_gasto:
                self.add_error('tipo_gasto', 'Este campo es obligatorio.')
            if not monto:
                self.add_error('monto', 'Este campo es obligatorio.')

        return cleaned_data

# Django ModelForm para el modelo Pago.
class PagoForm(forms.Form):
    monto_pagado = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

class RequisitoForm(forms.ModelForm):
    class Meta:
        model = Requisito
        fields = ['tipo', 'descripcion', 'valor_estimado']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descripción del requisito'}),
            'valor_estimado': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Valor (si aplica)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo'].required = False
        self.fields['descripcion'].required = False

    def clean(self):
        cleaned_data = super().clean()
        
        if cleaned_data.get('DELETE', False):
            return cleaned_data

        if not self.has_changed():
            return cleaned_data

        tipo = cleaned_data.get('tipo')
        descripcion = cleaned_data.get('descripcion')

        if tipo and not descripcion:
            self.add_error('descripcion', 'Este campo es requerido si se selecciona un tipo de requisito.')
        
        if descripcion and not tipo:
            self.add_error('tipo', 'Este campo es requerido si se ingresa una descripción.')

        return cleaned_data

class GaranteForm(forms.ModelForm):
    class Meta:
        model = Garante
        fields = ['nombre_completo', 'cedula', 'lugar_trabajo', 'ingresos_mensuales']
        widgets = {
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            'lugar_trabajo': forms.TextInput(attrs={'class': 'form-control'}),
            'ingresos_mensuales': forms.NumberInput(attrs={'class': 'form-control'}),
        }
