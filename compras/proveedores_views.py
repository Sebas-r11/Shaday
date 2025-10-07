# compras/proveedores_views.py
# Vistas para la gestión de proveedores del módulo de compras

from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count
from django.contrib import messages

# Importaciones locales
from .models import Proveedor

# ========================================
# MIXIN DE PERMISOS PARA COMPRAS
# ========================================

class ComprasRequiredMixin(UserPassesTestMixin):
    """Mixin para verificar permisos de compras"""
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_superuser or 
            self.request.user.groups.filter(name__in=['Compras', 'Administradores']).exists() or
            self.request.user.role in ['administrador']
        )
    
    def handle_no_permission(self):
        messages.error(self.request, "No tienes permisos para acceder al módulo de Compras.")
        return redirect('accounts:dashboard')


# ========================================
# VISTAS DE GESTIÓN DE PROVEEDORES
# ========================================

class ProveedorListView(ComprasRequiredMixin, ListView):
    """Lista de proveedores"""
    model = Proveedor
    template_name = 'compras/proveedor_list.html'
    context_object_name = 'proveedores'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Proveedor.objects.select_related('ciudad', 'ciudad__departamento')
        
        # Filtros
        search = self.request.GET.get('search')
        activo = self.request.GET.get('activo')
        
        if search:
            queryset = queryset.filter(
                Q(razon_social__icontains=search) |
                Q(nombre_comercial__icontains=search) |
                Q(numero_documento__icontains=search) |
                Q(codigo__icontains=search)
            )
        
        if activo == 'true':
            queryset = queryset.filter(activo=True)
        elif activo == 'false':
            queryset = queryset.filter(activo=False)
        
        return queryset.order_by('razon_social')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filtro_search'] = self.request.GET.get('search', '')
        context['filtro_activo'] = self.request.GET.get('activo', 'all')
        return context


class ProveedorCreateView(ComprasRequiredMixin, CreateView):
    """Crear nuevo proveedor"""
    model = Proveedor
    template_name = 'compras/proveedor_form.html'
    fields = [
        'codigo', 'razon_social', 'nombre_comercial', 'tipo_documento', 
        'numero_documento', 'telefono', 'email', 'sitio_web',
        'direccion', 'ciudad', 'codigo_postal',
        'condiciones_pago', 'limite_credito', 'descuento_comercial',
        'contacto_nombre', 'contacto_cargo', 'contacto_telefono', 'contacto_email',
        'observaciones'
    ]
    
    def form_valid(self, form):
        form.instance.usuario_creacion = self.request.user
        messages.success(self.request, 'Proveedor creado exitosamente.')
        return super().form_valid(form)


class ProveedorDetailView(ComprasRequiredMixin, DetailView):
    """Detalle de proveedor"""
    model = Proveedor
    template_name = 'compras/proveedor_detail.html'
    context_object_name = 'proveedor'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Órdenes del proveedor
        context['ordenes_recientes'] = self.object.ordenes_compra.select_related(
            'usuario_creacion'
        ).order_by('-fecha_creacion')[:10]
        
        # Estadísticas
        context['total_ordenes'] = self.object.ordenes_compra.count()
        context['valor_total_ordenes'] = self.object.ordenes_compra.aggregate(
            total=Sum('total')
        )['total'] or 0
        
        return context


class ProveedorUpdateView(ComprasRequiredMixin, UpdateView):
    """Editar proveedor"""
    model = Proveedor
    template_name = 'compras/proveedor_form.html'
    fields = [
        'codigo', 'razon_social', 'nombre_comercial', 'tipo_documento', 
        'numero_documento', 'telefono', 'email', 'sitio_web',
        'direccion', 'ciudad', 'codigo_postal',
        'condiciones_pago', 'limite_credito', 'descuento_comercial',
        'contacto_nombre', 'contacto_cargo', 'contacto_telefono', 'contacto_email',
        'observaciones', 'activo'
    ]
    
    def form_valid(self, form):
        messages.success(self.request, 'Proveedor actualizado exitosamente.')
        return super().form_valid(form)


# ========================================
# FUNCIONES DE UTILIDAD Y REDIRECCIÓN
# ========================================

@login_required
def redirigir_admin_proveedores(request):
    """Redirección al admin de proveedores de inventario"""
    return redirect('/admin/inventario/productoproveedor/')


@login_required
def redirigir_admin_presentaciones(request):
    """Redirección al admin de presentaciones proveedor-producto"""
    return redirect('/admin/inventario/presentacionproveedorproducto/')


@login_required
def redirigir_alertas_stock(request):
    """Redirección a alertas de stock de inventario"""
    return redirect('/inventario/alertas-stock/')