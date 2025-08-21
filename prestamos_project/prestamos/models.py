from django.db import models

# ==================================================
# === MODELO CLIENTE ===
# ==================================================
# Almacena la información personal de cada prestatario.
class Cliente(models.Model):
    # CharField es para campos de texto cortos. `max_length` es obligatorio.
    # `verbose_name` es el nombre legible que se mostrará en el panel de administración de Django.
    nombres = models.CharField(max_length=100, verbose_name="Nombres")
    apellidos = models.CharField(max_length=100, verbose_name="Apellidos")
    
    # `unique=True` asegura que no puedan existir dos clientes con la misma cédula.
    cedula = models.CharField(max_length=20, unique=True, verbose_name="Cédula o Identificación")
    
    # TextField es para campos de texto largos. `blank=True` y `null=True` hacen que el campo sea opcional.
    direccion = models.TextField(blank=True, null=True, verbose_name="Dirección")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    
    # DateTimeField guarda una fecha y hora. `auto_now_add=True` establece automáticamente la fecha y hora
    # de creación cuando se registra un nuevo cliente.
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")

    # El método `__str__` le dice a Django cómo "imprimir" un objeto Cliente.
    # Es muy útil en el panel de administración para ver una representación legible de cada cliente.
    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

    # La clase Meta permite configurar metadatos para el modelo.
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"


# ==================================================
# === MODELO PRESTAMO ===
# ==================================================
# Almacena los detalles de cada préstamo otorgado a un cliente.
class Prestamo(models.Model):
    # Define las opciones para el campo `estado`. Esto crea un menú desplegable en el admin.
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('pagado', 'Pagado'),
        ('vencido', 'Vencido'),
    ]
    # Nuevas opciones para la frecuencia de pago
    FRECUENCIA_CHOICES = [
        ('mensual', 'Mensual'),
        ('quincenal', 'Quincenal'),
    ]

    # `ForeignKey` crea una relación "muchos a uno" con el modelo Cliente. 
    # Un cliente puede tener muchos préstamos, pero un préstamo pertenece a un solo cliente.
    # `on_delete=models.CASCADE` significa que si se borra un cliente, todos sus préstamos se borrarán en cascada.
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="prestamos")
    
    # `DecimalField` es ideal para guardar dinero, ya que evita problemas de redondeo.
    # `max_digits` es el número total de dígitos, y `decimal_places` es el número de decimales.
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto del Préstamo")
    tasa_interes = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Tasa de Interés Anual", help_text="En porcentaje (%)")
    
    # `IntegerField` es para números enteros.
    plazo = models.IntegerField(verbose_name="Plazo", help_text="En meses")
    
    # `DateField` es para guardar solo fechas (sin hora).
    fecha_desembolso = models.DateField(verbose_name="Fecha de Desembolso")
    
    # `choices` limita los valores de este campo a las opciones definidas en `ESTADO_CHOICES`.
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activo', verbose_name="Estado")
    
    # Nuevo campo para la frecuencia de pago
    frecuencia_pago = models.CharField(
        max_length=10,
        choices=FRECUENCIA_CHOICES,
        default='mensual',
        verbose_name="Frecuencia de Pago"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")

    def __str__(self):
        return f"Préstamo #{self.id} - {self.cliente.nombres} {self.cliente.apellidos}"

    class Meta:
        verbose_name = "Préstamo"
        verbose_name_plural = "Préstamos"


# ==================================================
# === MODELO CUOTA ===
# ==================================================
# Almacena el plan de pagos (amortización) de cada préstamo.
class Cuota(models.Model):
    ESTADO_CUOTA_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('vencida', 'Vencida'),
    ]

    prestamo = models.ForeignKey(Prestamo, on_delete=models.CASCADE, related_name="cuotas")
    numero_cuota = models.IntegerField(verbose_name="Número de Cuota")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento")
    monto_cuota = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto de la Cuota")
    capital = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Capital")
    interes = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Interés")
    saldo_pendiente = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Saldo Pendiente")
    estado = models.CharField(max_length=10, choices=ESTADO_CUOTA_CHOICES, default='pendiente', verbose_name="Estado")

    def __str__(self):
        return f"Cuota {self.numero_cuota} del préstamo #{self.prestamo.id}"

    class Meta:
        verbose_name = "Cuota"
        verbose_name_plural = "Cuotas"
        unique_together = ('prestamo', 'numero_cuota')
        ordering = ['prestamo', 'numero_cuota']


# ==================================================
# === MODELO PAGO ===
# ==================================================
# Almacena cada pago individual realizado para una cuota específica.
class Pago(models.Model):
    # Relación con la cuota que se está pagando.
    cuota = models.OneToOneField(Cuota, on_delete=models.CASCADE, related_name="pago")
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto Pagado")
    fecha_pago = models.DateField(verbose_name="Fecha de Pago")

    def __str__(self):
        return f"Pago de {self.monto_pagado} para la cuota #{self.cuota.numero_cuota} del préstamo #{self.cuota.prestamo.id}"

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
