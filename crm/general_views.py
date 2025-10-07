"""
Vistas generales del módulo CRM - Actividades y funciones de apoyo
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

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

# ============= VISTAS ACTIVIDADES =============

class ActividadCreateView(CRMRequiredMixin, CreateView):
    """Crear nueva actividad"""
    model = Actividad
    template_name = 'crm/actividad_form.html'
    fields = [
        'oportunidad', 'tipo', 'asunto', 'descripcion',
        'fecha_actividad', 'duracion_minutos', 'responsable'
    ]
    
    def get_initial(self):
        initial = super().get_initial()
        oportunidad_id = self.request.GET.get('oportunidad')
        if oportunidad_id:
            initial['oportunidad'] = oportunidad_id
        initial['responsable'] = self.request.user
        return initial
    
    def form_valid(self, form):
        form.instance.usuario_creacion = self.request.user
        messages.success(self.request, 'Actividad programada exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('crm:oportunidad_detail', kwargs={'pk': self.object.oportunidad.pk})

class ActividadUpdateView(CRMRequiredMixin, UpdateView):
    """Editar actividad"""
    model = Actividad
    template_name = 'crm/actividad_form.html'
    fields = [
        'tipo', 'asunto', 'descripcion', 'fecha_actividad', 
        'duracion_minutos', 'responsable', 'completada', 
        'resultado', 'proxima_accion'
    ]
    
    def form_valid(self, form):
        messages.success(self.request, 'Actividad actualizada exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('crm:oportunidad_detail', kwargs={'pk': self.object.oportunidad.pk})

# ============= FUNCIONES AJAX =============

@login_required
def marcar_actividad_completada(request, pk):
    """Marcar actividad como completada via AJAX"""
    if request.method == 'POST':
        actividad = get_object_or_404(Actividad, pk=pk)
        actividad.completada = True
        actividad.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Actividad marcada como completada'
        })
    
    return JsonResponse({'success': False})