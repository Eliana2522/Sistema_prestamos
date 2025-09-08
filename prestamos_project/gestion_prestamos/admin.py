from django.contrib import admin, messages
from django.contrib.auth.models import User
from .models import Cliente, Prestamo, Cuota, Pago, TipoPrestamo, Capital, TipoGasto, GastoPrestamo
import secrets
import string

# ==================================================
# === ACCIONES PERSONALIZADAS PARA EL ADMIN ===
# ==================================================

@admin.action(description="Generar y asignar contraseña temporal")
def generate_temporary_password(modeladmin, request, queryset):
    """
    Genera una contraseña aleatoria para los usuarios de los clientes seleccionados.
    """
    password_list = []
    for cliente in queryset:
        if cliente.user:
            # Genera una contraseña aleatoria de 10 caracteres alfanuméricos
            alphabet = string.ascii_letters + string.digits
            temp_password = ''.join(secrets.choice(alphabet) for i in range(10))
            cliente.user.set_password(temp_password)
            cliente.user.save()

            # Activamos la bandera para forzar el cambio en el próximo login
            if hasattr(cliente, 'debe_cambiar_contrasena'):
                cliente.debe_cambiar_contrasena = True
                cliente.save()

            password_list.append(f"{cliente.nombres} {cliente.apellidos}: <strong>{temp_password}</strong>")
        else:
            messages.warning(request, f"El cliente {cliente} no tiene un usuario de sistema asociado y no se le pudo generar una contraseña.")

    if password_list:
        # Muestra las contraseñas generadas al administrador
        from django.utils.html import format_html
        message_html = format_html("Se generaron las siguientes contraseñas temporales:<br/>" + "<br/>".join(password_list))
        messages.success(request, message_html)

# ==================================================
# === CONFIGURACIÓN DEL PANEL DE ADMINISTRACIÓN ===
# ==================================================

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombres', 'apellidos', 'numero_documento', 'user', 'fecha_registro')
    search_fields = ('nombres', 'apellidos', 'numero_documento', 'user__username')
    list_filter = ('fecha_registro',)
    actions = [generate_temporary_password]


@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'monto', 'tasa_interes', 'plazo', 'estado', 'fecha_desembolso')
    search_fields = ('cliente__nombres', 'cliente__apellidos', 'id')
    list_filter = ('estado', 'fecha_desembolso', 'tipo_prestamo')
    # Para facilitar la navegación, hacemos que el campo 'cliente' sea un enlace a la página de edición del cliente.
    list_display_links = ('id', 'cliente')

@admin.register(Cuota)
class CuotaAdmin(admin.ModelAdmin):
    list_display = ('id', 'prestamo', 'numero_cuota', 'monto_cuota', 'fecha_vencimiento', 'estado')
    search_fields = ('prestamo__cliente__nombres', 'prestamo__id')
    list_filter = ('estado', 'fecha_vencimiento')

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cuota', 'monto_pagado', 'fecha_pago')
    search_fields = ('cuota__prestamo__id',)
    list_filter = ('fecha_pago',)

@admin.register(TipoPrestamo)
class TipoPrestamoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tasa_interes_predeterminada', 'monto_minimo', 'monto_maximo', 'plazo_maximo_meses')
    search_fields = ('nombre',)

@admin.register(Capital)
class CapitalAdmin(admin.ModelAdmin):
    list_display = ('monto_inicial', 'fecha_registro')

@admin.register(TipoGasto)
class TipoGastoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)

@admin.register(GastoPrestamo)
class GastoPrestamoAdmin(admin.ModelAdmin):
    list_display = ('prestamo', 'tipo_gasto', 'monto')
    search_fields = ('prestamo__id', 'tipo_gasto__nombre')
    list_filter = ('tipo_gasto',)