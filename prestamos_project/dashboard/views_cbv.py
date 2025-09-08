from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy
from gestion_prestamos.models import Cliente, Prestamo
from gestion_prestamos.forms import ClienteForm
from django.db.models import Q

class ClientListView(ListView):
    model = Cliente
    template_name = 'dashboard/client_list.html'
    context_object_name = 'clientes'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-fecha_registro')
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(id__icontains=query) |
                Q(nombres__icontains=query) |
                Q(apellidos__icontains=query) |
                Q(numero_documento__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context

class ClientCreateView(CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'dashboard/client_form.html'
    success_url = reverse_lazy('client_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Añadir Nuevo Cliente'
        return context

class ClientUpdateView(UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'dashboard/client_form.html'
    success_url = reverse_lazy('client_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Editar Cliente'
        return context

class LoanListView(ListView):
    model = Prestamo
    template_name = 'dashboard/loan_list.html'
    context_object_name = 'prestamos'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().filter(estado='activo').select_related('cliente').order_by('-fecha_creacion')
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(id__icontains=query) |
                Q(cliente__nombres__icontains=query) |
                Q(cliente__apellidos__icontains=query) |
                Q(cliente__numero_documento__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['page_title'] = 'Préstamos Activos'
        return context
