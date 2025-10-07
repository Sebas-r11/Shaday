from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, 
    UpdateView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta, datetime

from ventas.models import Cliente
from .models import AsignacionCliente, VisitaCliente, ConfiguracionRutas
from .forms import AsignacionClienteForm, VisitaClienteForm

User = get_user_model()


class RutasViewMixin(LoginRequiredMixin):
    """Mixin base para vistas de rutas"""
    pass


class AdminRutasMixin(UserPassesTestMixin):
    """Mixin para funciones que solo puede usar el administrador"""
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name='admin').exists()


class VendedorMixin(UserPassesTestMixin):
    """Mixin para vendedores"""
    def test_func(self):
        return (self.request.user.groups.filter(name__in=['vendedor', 'admin']).exists() or 
                self.request.user.is_superuser)


# ============= DASHBOARD PRINCIPAL =============

class RutasDashboardView(RutasViewMixin, TemplateView):
    """Dashboard principal del módulo de rutas"""
    template_name = 'rutas/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Estadísticas generales para administradores
        if user.is_superuser or user.groups.filter(name='admin').exists():
            context.update({
                'total_asignaciones': AsignacionCliente.objects.filter(activa=True).count(),
                'total_vendedores': User.objects.filter(
                    groups__name='vendedor', is_active=True
                ).count(),
                'visitas_hoy': VisitaCliente.objects.filter(
                    fecha_programada__date=timezone.now().date(),
                    estado='programada'
                ).count(),
                'visitas_vencidas': AsignacionCliente.objects.filter(
                    activa=True,
                    proxima_visita__lt=timezone.now()
                ).count(),
                'es_admin': True
            })
        
        # Datos específicos para vendedores
        if user.groups.filter(name='vendedor').exists():
            mis_asignaciones = AsignacionCliente.objects.filter(
                vendedor=user, activa=True
            )
            context.update({
                'mis_clientes_count': mis_asignaciones.count(),
                'visitas_pendientes': mis_asignaciones.filter(
                    proxima_visita__lte=timezone.now() + timedelta(days=7)
                ).count(),
                'visitas_vencidas_personal': mis_asignaciones.filter(
                    proxima_visita__lt=timezone.now()
                ).count(),
                'es_vendedor': True
            })
        
        return context


# ============= GESTIÓN DE ASIGNACIONES =============

class AsignacionListView(RutasViewMixin, AdminRutasMixin, ListView):
    """Lista de todas las asignaciones de clientes"""
    model = AsignacionCliente
    template_name = 'rutas/asignaciones_list.html'
    context_object_name = 'asignaciones'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = AsignacionCliente.objects.select_related(
            'vendedor', 'cliente'
        ).filter(activa=True)
        
        # Filtros
        vendedor_id = self.request.GET.get('vendedor')
        frecuencia = self.request.GET.get('frecuencia')
        estado = self.request.GET.get('estado')
        
        if vendedor_id:
            queryset = queryset.filter(vendedor_id=vendedor_id)
        
        if frecuencia:
            queryset = queryset.filter(frecuencia_visita=frecuencia)
        
        if estado == 'vencidas':
            queryset = queryset.filter(proxima_visita__lt=timezone.now())
        elif estado == 'proximas':
            queryset = queryset.filter(
                proxima_visita__gte=timezone.now(),
                proxima_visita__lte=timezone.now() + timedelta(days=7)
            )
        
        return queryset.order_by('proxima_visita')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendedores'] = User.objects.filter(
            groups__name='vendedor', is_active=True
        ).order_by('first_name', 'last_name')
        context['frecuencias'] = AsignacionCliente.FRECUENCIA_CHOICES
        return context


class AsignacionCreateView(RutasViewMixin, AdminRutasMixin, CreateView):
    """Crear nueva asignación de cliente a vendedor"""
    model = AsignacionCliente
    template_name = 'rutas/asignacion_form.html'
    fields = ['vendedor', 'cliente', 'frecuencia_visita', 'notas']
    success_url = reverse_lazy('rutas:asignaciones')
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            f'Cliente "{form.instance.cliente.nombre_completo}" asignado exitosamente a '
            f'{form.instance.vendedor.get_full_name() or form.instance.vendedor.username}'
        )
        return super().form_valid(form)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Filtrar solo vendedores activos
        form.fields['vendedor'].queryset = User.objects.filter(
            groups__name='vendedor', is_active=True
        ).order_by('first_name', 'last_name')
        
        # Filtrar solo clientes sin asignar
        form.fields['cliente'].queryset = Cliente.objects.filter(
            asignacion_vendedor__isnull=True, activo=True
        ).order_by('nombre_completo')
        
        return form


class AsignacionUpdateView(RutasViewMixin, AdminRutasMixin, UpdateView):
    """Editar asignación existente"""
    model = AsignacionCliente
    template_name = 'rutas/asignacion_form.html'
    fields = ['vendedor', 'frecuencia_visita', 'activa', 'notas']
    success_url = reverse_lazy('rutas:asignaciones')
    
    def form_valid(self, form):
        messages.success(self.request, 'Asignación actualizada exitosamente.')
        return super().form_valid(form)


class AsignacionDeleteView(RutasViewMixin, AdminRutasMixin, DeleteView):
    """Eliminar asignación existente"""
    model = AsignacionCliente
    template_name = 'rutas/asignacion_confirm_delete.html'
    success_url = reverse_lazy('rutas:asignaciones')
    context_object_name = 'asignacion'
    
    def delete(self, request, *args, **kwargs):
        asignacion = self.get_object()
        messages.success(
            request, 
            f'Asignación de {asignacion.cliente.nombre_completo} eliminada exitosamente.'
        )
        return super().delete(request, *args, **kwargs)


class AsignacionDetailView(RutasViewMixin, DetailView):
    """Detalle de una asignación con historial de visitas"""
    model = AsignacionCliente
    template_name = 'rutas/asignacion_detail.html'
    context_object_name = 'asignacion'
    
    def get_queryset(self):
        return AsignacionCliente.objects.select_related(
            'vendedor', 'cliente'
        ).prefetch_related(
            Prefetch(
                'visitas',
                queryset=VisitaCliente.objects.order_by('-fecha_programada')
            )
        )


# ============= VISTA PARA VENDEDORES =============

class MisClientesView(RutasViewMixin, VendedorMixin, ListView):
    """Vista para vendedores: sus clientes asignados"""
    template_name = 'rutas/mis_clientes.html'
    context_object_name = 'asignaciones'
    paginate_by = 20
    
    def get_queryset(self):
        return AsignacionCliente.objects.filter(
            vendedor=self.request.user, activa=True
        ).select_related('cliente').order_by('proxima_visita')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas para el vendedor
        mis_asignaciones = self.get_queryset()
        context.update({
            'total_clientes': mis_asignaciones.count(),
            'visitas_vencidas': mis_asignaciones.filter(
                proxima_visita__lt=timezone.now()
            ).count(),
            'visitas_esta_semana': mis_asignaciones.filter(
                proxima_visita__gte=timezone.now(),
                proxima_visita__lte=timezone.now() + timedelta(days=7)
            ).count(),
        })
        
        return context


class ClienteDetailView(RutasViewMixin, VendedorMixin, DetailView):
    """Detalle de un cliente para el vendedor"""
    model = Cliente
    template_name = 'rutas/cliente_detail.html'
    context_object_name = 'cliente'
    pk_url_kwarg = 'cliente_id'
    
    def get_object(self, queryset=None):
        cliente = super().get_object(queryset)
        
        # Verificar que el vendedor tenga acceso a este cliente
        if not self.request.user.is_superuser:
            try:
                asignacion = AsignacionCliente.objects.get(
                    cliente=cliente, vendedor=self.request.user, activa=True
                )
            except AsignacionCliente.DoesNotExist:
                raise PermissionError("No tienes acceso a este cliente")
        
        return cliente
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            asignacion = AsignacionCliente.objects.get(
                cliente=self.object,
                vendedor=self.request.user,
                activa=True
            )
            context['asignacion'] = asignacion
            context['visitas'] = VisitaCliente.objects.filter(
                asignacion=asignacion
            ).order_by('-fecha_programada')[:10]
        except AsignacionCliente.DoesNotExist:
            context['asignacion'] = None
        
        return context


# ============= GESTIÓN DE VISITAS =============

class VisitaCreateView(RutasViewMixin, VendedorMixin, CreateView):
    """Crear nueva visita"""
    model = VisitaCliente
    template_name = 'rutas/visita_form.html'
    form_class = VisitaClienteForm
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.creada_por = self.request.user
        
        # Si el usuario no es superusuario, verificar que la asignación le pertenece
        if not self.request.user.is_superuser:
            asignacion = form.instance.asignacion
            if asignacion.vendedor != self.request.user:
                messages.error(
                    self.request, 
                    'No tienes permisos para registrar visitas para este cliente.'
                )
                return self.form_invalid(form)
        
        messages.success(self.request, 'Visita programada exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener la lista de clientes para el datalist
        if self.request.user.is_superuser:
            asignaciones = AsignacionCliente.objects.filter(activa=True).select_related('cliente', 'vendedor')
        else:
            asignaciones = AsignacionCliente.objects.filter(
                vendedor=self.request.user, 
                activa=True
            ).select_related('cliente')
        
        context['clientes_list'] = [
            {
                'id': asig.id,
                'nombre': asig.cliente.nombre_completo,
                'vendedor': asig.vendedor.get_full_name() if self.request.user.is_superuser else None
            }
            for asig in asignaciones
        ]
        
        return context
    
    def get_success_url(self):
        return reverse_lazy('rutas:mis_clientes')


class CompletarVisitaView(RutasViewMixin, VendedorMixin, UpdateView):
    """Marcar visita como completada"""
    model = VisitaCliente
    template_name = 'rutas/completar_visita.html'
    fields = ['resultado', 'observaciones', 'productos_mostrados', 'requiere_seguimiento']
    
    def form_valid(self, form):
        # Marcar como realizada
        form.instance.estado = 'realizada'
        form.instance.fecha_realizada = timezone.now()
        
        messages.success(self.request, 'Visita completada exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('rutas:mis_clientes')


# ============= VISTAS AJAX =============

class ClientesDisponiblesAjaxView(RutasViewMixin, AdminRutasMixin, JsonResponse):
    """API para obtener clientes disponibles (sin asignar)"""
    
    def get(self, request, *args, **kwargs):
        clientes = Cliente.objects.filter(
            asignacion_vendedor__isnull=True, 
            activo=True
        ).values('id', 'nombre_completo', 'email')
        
        return JsonResponse({
            'clientes': list(clientes)
        })


class VendedoresDisponiblesAjaxView(RutasViewMixin, AdminRutasMixin, JsonResponse):
    """API para obtener vendedores disponibles"""
    
    def get(self, request, *args, **kwargs):
        vendedores = User.objects.filter(
            groups__name='vendedor', 
            is_active=True
        ).values('id', 'username', 'first_name', 'last_name')
        
        return JsonResponse({
            'vendedores': list(vendedores)
        })