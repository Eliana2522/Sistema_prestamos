from django import forms
from .models import Cliente, Prestamo, Pago, Cuota, TipoPrestamo, GastoPrestamo, TipoGasto
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
            'tipo_documento',
            'numero_documento',
            'direccion',
            'telefono',
            'email',
        ]
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
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
            'plazo',
            'fecha_desembolso',
            'frecuencia_pago', # Nuevo campo añadido al formulario
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
            'plazo': forms.NumberInput(attrs={'class': 'form-control'}),
            'fecha_desembolso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'frecuencia_pago': forms.Select(attrs={'class': 'form-control'}), # Widget para el nuevo campo
        }
        labels = {
            'monto': 'Monto Solicitado por el Cliente',
        }

    def clean(self):
        cleaned_data = super().clean()
        cliente = cleaned_data.get("cliente")
        estado = cleaned_data.get("estado")
        tipo_prestamo = cleaned_data.get("tipo_prestamo")
        monto = cleaned_data.get("monto")
        plazo = cleaned_data.get("plazo")

        # Validaciones si se ha seleccionado un tipo de préstamo
        if tipo_prestamo and monto is not None:
            if monto < tipo_prestamo.monto_minimo:
                self.add_error('monto', f"El monto debe ser de al menos {tipo_prestamo.monto_minimo:,.2f}.")
            if monto > tipo_prestamo.monto_maximo:
                self.add_error('monto', f"El monto no puede exceder {tipo_prestamo.monto_maximo:,.2f}.")

        if tipo_prestamo and plazo is not None:
            if plazo < tipo_prestamo.plazo_minimo_meses:
                self.add_error('plazo', f"El plazo debe ser de al menos {tipo_prestamo.plazo_minimo_meses} meses.")
            if plazo > tipo_prestamo.plazo_maximo_meses:
                self.add_error('plazo', f"El plazo no puede exceder los {tipo_prestamo.plazo_maximo_meses} meses.")

        # Validación de préstamo activo existente
        is_new = self.instance.pk is None
        if cliente and estado == 'activo' and is_new:
            if Prestamo.objects.filter(cliente=cliente, estado='activo').exists():
                raise forms.ValidationError(
                    "Este cliente ya tiene un préstamo activo. No se puede registrar uno nuevo hasta que el anterior sea saldado."
                )
        
        return cleaned_data

class GastoPrestamoForm(forms.ModelForm):
    class Meta:
        model = GastoPrestamo
        fields = ['tipo_gasto', 'monto', 'descripcion']
        widgets = {
            'tipo_gasto': forms.Select(attrs={'class': 'form-select'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
        }

# Django ModelForm para el modelo Pago.
class PagoForm(forms.Form):
    monto_pagado = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
