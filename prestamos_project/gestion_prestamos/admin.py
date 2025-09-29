from django.contrib import admin, messages
from .models import Cliente, Prestamo, Cuota, Pago, TipoPrestamo, Capital, TipoGasto, GastoPrestamo
from django.contrib.auth.models import User
import secrets
import string

# ==================================================
# === ACCIONES PERSONALIZADAS PARA EL ADMIN ===
# ==================================================

@admin.action(description="Restablecer contraseña al Nº de Documento")
def generate_temporary_password(modeladmin, request, queryset):
    """
    Restablece la contraseña del usuario al número de documento del cliente.
    """
    updated_count = 0
    for cliente in queryset:
        if cliente.user and cliente.numero_documento:
            password = cliente.numero_documento
            cliente.user.set_password(password)
            cliente.user.save()

            # Activamos la bandera para forzar el cambio en el próximo login
            cliente.debe_cambiar_contrasena = True
            cliente.save()
            updated_count += 1
        else:
            if not cliente.user:
                messages.warning(request, f"El cliente {cliente} no tiene un usuario de sistema asociado.")
            elif not cliente.numero_documento:
                messages.warning(request, f"El cliente {cliente} no tiene un número de documento para usar como contraseña.")

    if updated_count > 0:
        messages.success(request, f"Se restableció la contraseña de {updated_count} cliente(s) a su número de documento.")

# ==================================================
# === CONFIGURACIÓN DE INLINES ===
# ==================================================

class GastoPrestamoInline(admin.TabularInline):
    model = GastoPrestamo
    extra = 1
    classes = ['collapse']

class CuotaInline(admin.TabularInline):
    model = Cuota
    extra = 0
    readonly_fields = ('numero_cuota', 'fecha_vencimiento', 'monto_cuota', 'capital', 'interes', 'saldo_pendiente', 'estado', 'monto_penalidad_acumulada')
    can_delete = False
    classes = ['collapse']

    def has_add_permission(self, request, obj=None):
        return False

# ==================================================
# === CONFIGURACIÓN DE MODELADMINS ===
# ==================================================

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombres', 'apellidos', 'numero_documento', 'user', 'fecha_registro')
    search_fields = ('nombres', 'apellidos', 'numero_documento', 'user__username')
    list_filter = ('fecha_registro', 'estado_civil', 'sexo')
    actions = [generate_temporary_password]
    readonly_fields = ('fecha_registro',)

    fieldsets = (
        ('Información Personal', {
            'fields': (('nombres', 'apellidos'), 'apodo', ('sexo', 'estado_civil'), 'fecha_nacimiento')
        }),
        ('Información de Contacto', {
            'fields': ('email', 'telefono', 'direccion')
        }),
        ('Documentación', {
            'fields': (('tipo_documento', 'numero_documento'),)
        }),
        ('Información Laboral', {
            'classes': ('collapse',),
            'fields': ('nombre_empresa', 'cargo', 'telefono_trabajo', 'ingresos_mensuales', 'fecha_ingreso_trabajo', 'trabajo_actual')
        }),
        ('Portal de Acceso', {
            'fields': ('user', 'debe_cambiar_contrasena')
        }),
    )

@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'monto', 'estado', 'fecha_desembolso', 'frecuencia_pago')
    search_fields = ('cliente__nombres', 'cliente__apellidos', 'id')
    list_filter = ('estado', 'frecuencia_pago', 'tipo_prestamo', 'fecha_desembolso')
    list_display_links = ('id', 'cliente')
    readonly_fields = ('fecha_creacion', 'total_gastos_asociados', 'monto_desembolsado')
    inlines = [GastoPrestamoInline, CuotaInline]

    fieldsets = (
        (None, {
            'fields': (('cliente', 'tipo_prestamo'), 'estado')
        }),
        ('Detalles Financieros', {
            'fields': ('monto', ('tasa_interes', 'periodo_tasa'), 'manejo_gastos', 'total_gastos_asociados', 'monto_desembolsado')
        }),
        ('Plazos y Frecuencia', {
            'fields': (('plazo', 'frecuencia_pago'), ('fecha_desembolso', 'fecha_inicio_pago'))
        }),
        ('Configuración Adicional', {
            'classes': ('collapse',),
            'fields': ('tipo_amortizacion', 'garante', 'fecha_creacion')
        }),
    )

@admin.register(TipoPrestamo)
class TipoPrestamoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tasa_interes_predeterminada', 'monto_minimo', 'monto_maximo', 'plazo_maximo_meses')
    search_fields = ('nombre',)

@admin.register(Capital)
class CapitalAdmin(admin.ModelAdmin):
    list_display = ('monto_inicial', 'fecha_registro')
    readonly_fields = ('fecha_registro',)

    def has_add_permission(self, request):
        # Permitir añadir solo si no existe ningún registro de capital
        return not Capital.objects.exists()

@admin.register(TipoGasto)
class TipoGastoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)