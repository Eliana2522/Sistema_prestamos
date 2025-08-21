from django.urls import path
from . import views

# Este archivo define las URLs que son específicas de la app `dashboard`.
urlpatterns = [
    path('', views.panel_informativo, name='panel_informativo'),
    path('profile/', views.profile, name='profile'),

    # --- URLs para Clientes ---
    # Muestra la tabla de clientes.
    path('clientes/', views.client_list, name='client_list'),
    # Muestra el formulario para añadir un nuevo cliente.
    path('clientes/nuevo/', views.client_add, name='client_add'),
    # Muestra el formulario para editar un cliente existente.
    path('clientes/<int:pk>/editar/', views.client_edit, name='client_edit'),

    # --- URLs para Préstamos ---
    # Muestra el formulario para añadir un nuevo préstamo.
    path('prestamos/nuevo/', views.loan_add, name='loan_add'),
    # Muestra los detalles de un préstamo específico y su tabla de amortización.
    path('prestamos/<int:pk>/', views.loan_detail, name='loan_detail'),
    # Muestra la lista de préstamos activos.
    path('prestamos/activos/', views.loan_list, name='loan_list'),

    # --- URLs para Pagos ---
    # Muestra el formulario para registrar un nuevo pago.
    path('pagos/nuevo/', views.payment_add, name='payment_add'),

    # --- URLs para Cobros ---
    path('cobros/', views.cobros_list, name='cobros_list'),
]