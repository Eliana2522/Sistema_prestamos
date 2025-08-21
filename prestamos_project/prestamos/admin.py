from django.contrib import admin
from .models import Cliente, Prestamo, Pago

# Para una mejor visualización y manejo en el panel de administración,
# personalizamos las clases ModelAdmin para cada modelo.

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    """Configuración para el modelo Cliente en el admin."""
    # Muestra estos campos en la lista de clientes.
    list_display = ('id', 'nombres', 'apellidos', 'cedula', 'telefono', 'fecha_registro')
    # Añade una barra de búsqueda que buscará por los campos especificados.
    search_fields = ('nombres', 'apellidos', 'cedula')
    # Añade un filtro por fecha de registro en la barra lateral.
    list_filter = ('fecha_registro',)

@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    """Configuración para el modelo Prestamo en el admin."""
    list_display = ('id', 'cliente', 'monto', 'tasa_interes', 'plazo', 'estado', 'fecha_desembolso')
    # Permite buscar préstamos por el nombre, apellido o cédula del cliente.
    search_fields = ('cliente__nombres', 'cliente__apellidos', 'cliente__cedula', 'id')
    # Añade filtros útiles.
    list_filter = ('estado', 'fecha_desembolso')
    # `raw_id_fields` es muy útil cuando tienes muchos clientes.
    # En lugar de un menú desplegable con todos los clientes, te da un campo de búsqueda.
    raw_id_fields = ('cliente',)

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    """Configuración para el modelo Pago en el admin."""
    list_display = ('id', 'get_prestamo_id', 'cuota', 'monto_pagado', 'fecha_pago')
    search_fields = ('cuota__prestamo__id', 'cuota__prestamo__cliente__nombres')
    list_filter = ('fecha_pago',)
    raw_id_fields = ('cuota',)

    def get_prestamo_id(self, obj):
        return obj.cuota.prestamo.id
    get_prestamo_id.short_description = 'Préstamo ID'

# El decorador `@admin.register(Modelo)` es una forma moderna y limpia de registrar los modelos
# con su clase de administración personalizada, haciendo lo mismo que `admin.site.register(Modelo, ModeloAdmin)`.