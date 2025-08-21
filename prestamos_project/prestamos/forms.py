from django import forms
from .models import Cliente, Prestamo, Pago, Cuota
from django_select2.forms import Select2Widget

# Django ModelForm para el modelo Cliente.
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'nombres',
            'apellidos',
            'cedula',
            'direccion',
            'telefono',
        ]
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }

# Django ModelForm para el modelo Prestamo.
class PrestamoForm(forms.ModelForm):
    class Meta:
        model = Prestamo
        fields = [
            'cliente',
            'monto',
            'tasa_interes',
            'plazo',
            'fecha_desembolso',
            'estado',
            'frecuencia_pago', # Nuevo campo añadido al formulario
        ]
        widgets = {
            'cliente': Select2Widget(attrs={'class': 'form-control'}), # Usamos el widget de Select2
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tasa_interes': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'plazo': forms.NumberInput(attrs={'class': 'form-control'}),
            'fecha_desembolso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'frecuencia_pago': forms.Select(attrs={'class': 'form-control'}), # Widget para el nuevo campo
        }

# Django ModelForm para el modelo Pago.
class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = [
            'cuota',
            'monto_pagado',
            'fecha_pago',
        ]
        widgets = {
            'cuota': Select2Widget(attrs={'class': 'form-control'}), # También podemos usarlo aquí
            'monto_pagado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fecha_pago': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }