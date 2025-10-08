# ventas/clientes_views.py
"""
Vistas especializadas para gestión de clientes
Extraído de ventas/views.py para mejorar organización
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from .models import Cliente, Pedido, Factura
from .forms import ClienteForm, ClienteFilterForm


class VentasRequiredMixin(UserPassesTestMixin):
    """Mixin para verificar permisos de ventas"""
    def test_func(self):
        return self.request.user.can_create_sales()


# ============= VISTAS DE CLIENTES =============

class ClienteListView(VentasRequiredMixin, ListView):
    """Lista de clientes con filtros"""
    model = Cliente
    template_name = 'ventas/cliente_list.html'
    context_object_name = 'clientes'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Cliente.objects.all()
        
        # Filtros básicos
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(documento__icontains=search) |
                Q(email__icontains=search) |
                Q(telefono__icontains=search)
            )
        
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(activo=estado == 'activo')
        
        tipo = self.request.GET.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo_cliente=tipo)
        
        ciudad = self.request.GET.get('ciudad')
        if ciudad:
            queryset = queryset.filter(ciudad__id=ciudad)
        
        return queryset.order_by('nombre_completo')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ClienteFilterForm(self.request.GET)
        context['total_clientes'] = Cliente.objects.count()
        context['clientes_activos'] = Cliente.objects.filter(activo=True).count()
        return context


class ClienteCreateView(VentasRequiredMixin, CreateView):
    """Crear nuevo cliente"""
    model = Cliente
    form_class = ClienteForm
    template_name = 'ventas/cliente_form.html'
    success_url = reverse_lazy('ventas:cliente_list')
    
    def form_valid(self, form):
        form.instance.usuario_creacion = self.request.user
        messages.success(self.request, f'Cliente {form.instance.nombre_completo} creado exitosamente.')
        return super().form_valid(form)


class ClienteDetailView(VentasRequiredMixin, DetailView):
    """Detalle de cliente con histórico de ventas"""
    model = Cliente
    template_name = 'ventas/cliente_detail.html'
    context_object_name = 'cliente'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = self.object
        
        # Histórico de pedidos
        context['pedidos'] = Pedido.objects.filter(
            cliente=cliente
        ).order_by('-fecha_creacion')[:10]
        
        # Histórico de facturas
        context['facturas'] = Factura.objects.filter(
            cliente=cliente
        ).order_by('-fecha_creacion')[:10]
        
        # Estadísticas del cliente
        context['total_pedidos'] = Pedido.objects.filter(cliente=cliente).count()
        context['total_facturas'] = Factura.objects.filter(cliente=cliente).count()
        context['valor_total_facturas'] = Factura.objects.filter(
            cliente=cliente,
            estado='pagada'
        ).aggregate(Sum('total'))['total__sum'] or 0
        
        return context


class ClienteUpdateView(VentasRequiredMixin, UpdateView):
    """Editar cliente"""
    model = Cliente
    form_class = ClienteForm
    template_name = 'ventas/cliente_form.html'
    success_url = reverse_lazy('ventas:cliente_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Cliente {form.instance.nombre_completo} actualizado exitosamente.')
        return super().form_valid(form)


# ============= API CLIENTES =============

@login_required
def buscar_clientes_api(request):
    """API para buscar clientes (usado en autocompletado)"""
    if not request.user.can_create_sales():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    # Aceptar tanto 'q' como 'term' para compatibilidad
    term = request.GET.get('q', '') or request.GET.get('term', '')
    if len(term) < 2:
        return JsonResponse({'clientes': []})
    
    clientes = Cliente.objects.filter(
        Q(nombre_completo__icontains=term) |
        Q(numero_documento__icontains=term),
        activo=True
    )[:10]
    
    results = []
    for cliente in clientes:
        results.append({
            'id': cliente.id,
            'nombre_completo': cliente.nombre_completo,
            'numero_documento': cliente.numero_documento,
            'tipo_documento': cliente.tipo_documento,
            'telefono': cliente.telefono,
            'direccion': cliente.direccion,
            'ciudad': cliente.ciudad if isinstance(cliente.ciudad, str) else (cliente.ciudad.nombre if cliente.ciudad else ''),
            'tipo_cliente': cliente.tipo_cliente,
            'limite_credito': float(cliente.limite_credito)
        })
    
    return JsonResponse({'clientes': results})