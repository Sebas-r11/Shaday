"""
Vistas especializadas para gestión de oportunidades de venta
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count, Avg, Case, When, Value, F
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import Oportunidad, Actividad, NotaOportunidad, EstadoOportunidad
from ventas.models import Cliente

# ============= MIXINS =============

class CRMRequiredMixin(UserPassesTestMixin):
    """Mixin para verificar permisos de CRM"""
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_superuser or 
            self.request.user.groups.filter(name__in=['Ventas', 'Administradores']).exists()
        )
    
    def handle_no_permission(self):
        messages.error(self.request, "No tienes permisos para acceder al módulo CRM.")
        return redirect('accounts:dashboard')

# ============= VISTAS OPORTUNIDADES =============

class OportunidadListView(CRMRequiredMixin, ListView):
    """Lista de oportunidades con filtros"""
    model = Oportunidad
    template_name = 'crm/oportunidad_list.html'
    context_object_name = 'oportunidades'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Oportunidad.objects.select_related(
            'cliente', 'vendedor'
        ).prefetch_related('actividades')
        
        # Filtros
        estado = self.request.GET.get('estado')
        vendedor = self.request.GET.get('vendedor')
        cliente = self.request.GET.get('cliente')
        prioridad = self.request.GET.get('prioridad')
        search = self.request.GET.get('search')
        
        if estado and estado != 'all':
            queryset = queryset.filter(estado=estado)
        
        if vendedor:
            queryset = queryset.filter(vendedor_id=vendedor)
        
        if cliente:
            queryset = queryset.filter(cliente_id=cliente)
        
        if prioridad:
            queryset = queryset.filter(prioridad=prioridad)
        
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(cliente__nombre__icontains=search) |
                Q(cliente__razon_social__icontains=search) |
                Q(descripcion__icontains=search)
            )
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estados'] = EstadoOportunidad.choices
        context['filtro_estado'] = self.request.GET.get('estado', 'all')
        context['filtro_search'] = self.request.GET.get('search', '')
        return context

class OportunidadCreateView(CRMRequiredMixin, CreateView):
    """Crear nueva oportunidad"""
    model = Oportunidad
    template_name = 'crm/oportunidad_form.html'
    fields = [
        'nombre', 'cliente', 'valor_estimado', 'probabilidad', 
        'estado', 'prioridad', 'fuente', 'fecha_cierre_estimada',
        'vendedor', 'descripcion', 'productos_interes', 'competencia'
    ]
    
    def form_valid(self, form):
        form.instance.usuario_creacion = self.request.user
        if not form.instance.vendedor:
            form.instance.vendedor = self.request.user
        
        messages.success(self.request, 'Oportunidad creada exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('crm:oportunidad_detail', kwargs={'pk': self.object.pk})

class OportunidadDetailView(CRMRequiredMixin, DetailView):
    """Detalle de oportunidad"""
    model = Oportunidad
    template_name = 'crm/oportunidad_detail.html'
    context_object_name = 'oportunidad'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Actividades relacionadas
        context['actividades'] = self.object.actividades.select_related(
            'responsable'
        ).order_by('-fecha_actividad')
        
        # Notas relacionadas
        context['notas'] = self.object.notas.select_related(
            'usuario_creacion'
        ).order_by('-fecha_creacion')
        
        # Cotizaciones relacionadas (si existen)
        try:
            from ventas.models import Cotizacion
            context['cotizaciones'] = Cotizacion.objects.filter(
                cliente=self.object.cliente
            ).order_by('-fecha_creacion')[:5]
        except:
            context['cotizaciones'] = []
        
        return context

class OportunidadUpdateView(CRMRequiredMixin, UpdateView):
    """Editar oportunidad"""
    model = Oportunidad
    template_name = 'crm/oportunidad_form.html'
    fields = [
        'nombre', 'cliente', 'valor_estimado', 'probabilidad', 
        'estado', 'prioridad', 'fuente', 'fecha_cierre_estimada',
        'vendedor', 'descripcion', 'productos_interes', 'competencia'
    ]
    
    def form_valid(self, form):
        # Si se marca como cerrada, establecer fecha de cierre
        if form.instance.estado in ['cerrado_ganado', 'cerrado_perdido']:
            if not form.instance.fecha_cierre_real:
                form.instance.fecha_cierre_real = timezone.now()
        
        messages.success(self.request, 'Oportunidad actualizada exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('crm:oportunidad_detail', kwargs={'pk': self.object.pk})

# ============= FUNCIONES AJAX =============

@login_required
def agregar_nota_oportunidad(request, pk):
    """Agregar nota a oportunidad via AJAX"""
    if request.method == 'POST':
        oportunidad = get_object_or_404(Oportunidad, pk=pk)
        contenido = request.POST.get('contenido')
        
        if contenido:
            nota = NotaOportunidad.objects.create(
                oportunidad=oportunidad,
                contenido=contenido,
                usuario_creacion=request.user
            )
            
            return JsonResponse({
                'success': True,
                'nota': {
                    'id': nota.id,
                    'contenido': nota.contenido,
                    'autor': nota.usuario_creacion.get_full_name(),
                    'fecha': nota.fecha_creacion.strftime('%d/%m/%Y %H:%M')
                }
            })
    
    return JsonResponse({'success': False})