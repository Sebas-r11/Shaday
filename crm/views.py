from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count, Avg, Case, When, Value, F
from django.contrib import messages
from django.http import JsonResponse
from datetime import datetime, timedelta, date
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import DecimalField

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

# ============= DASHBOARD CRM =============

@login_required
def crm_dashboard(request):
    """Dashboard principal del CRM"""
    
    # Filtros de fecha - último trimestre por defecto
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=90)
    
    # KPIs principales
    total_oportunidades = Oportunidad.objects.count()
    oportunidades_abiertas = Oportunidad.objects.exclude(
        estado__in=['cerrado_ganado', 'cerrado_perdido']
    ).count()
    
    # Valor del pipeline
    pipeline_value = Oportunidad.objects.exclude(
        estado__in=['cerrado_ganado', 'cerrado_perdido']
    ).aggregate(
        total=Sum('valor_estimado'),
        ponderado=Sum(
            Case(
                When(valor_estimado__isnull=False, then=F('valor_estimado') * F('probabilidad') / 100),
                default=Value(0),
                output_field=DecimalField(max_digits=15, decimal_places=2)
            )
        )
    )
    
    # Oportunidades por estado
    oportunidades_por_estado = Oportunidad.objects.values('estado').annotate(
        count=Count('id'),
        valor=Sum('valor_estimado')
    ).order_by('estado')
    
    # Actividades pendientes del usuario
    actividades_pendientes = Actividad.objects.filter(
        responsable=request.user,
        completada=False,
        fecha_actividad__gte=timezone.now()
    ).order_by('fecha_actividad')[:5]
    
    # Actividades vencidas
    actividades_vencidas = Actividad.objects.filter(
        responsable=request.user,
        completada=False,
        fecha_actividad__lt=timezone.now()
    ).count()
    
    # Oportunidades recientes
    oportunidades_recientes = Oportunidad.objects.select_related(
        'cliente', 'vendedor'
    ).order_by('-fecha_creacion')[:5]
    
    # Conversiones del mes
    mes_actual = timezone.now().replace(day=1)
    oportunidades_ganadas = Oportunidad.objects.filter(
        estado='cerrado_ganado',
        fecha_cierre_real__gte=mes_actual
    ).count()
    
    oportunidades_cerradas_mes = Oportunidad.objects.filter(
        fecha_cierre_real__gte=mes_actual,
        estado__in=['cerrado_ganado', 'cerrado_perdido']
    ).count()
    
    tasa_conversion = 0
    if oportunidades_cerradas_mes > 0:
        tasa_conversion = (oportunidades_ganadas / oportunidades_cerradas_mes) * 100
    
    # Top vendedores
    top_vendedores = Oportunidad.objects.filter(
        estado='cerrado_ganado',
        fecha_cierre_real__gte=mes_actual
    ).values('vendedor__first_name', 'vendedor__last_name').annotate(
        total_valor=Sum('valor_estimado'),
        count=Count('id')
    ).order_by('-total_valor')[:5]
    
    context = {
        'total_oportunidades': total_oportunidades,
        'oportunidades_abiertas': oportunidades_abiertas,
        'pipeline_total': pipeline_value['total'] or 0,
        'pipeline_ponderado': pipeline_value['ponderado'] or 0,
        'oportunidades_por_estado': oportunidades_por_estado,
        'actividades_pendientes': actividades_pendientes,
        'actividades_vencidas': actividades_vencidas,
        'oportunidades_recientes': oportunidades_recientes,
        'tasa_conversion': round(tasa_conversion, 1),
        'top_vendedores': top_vendedores,
        'estados_oportunidad': EstadoOportunidad.choices,
    }
    
    return render(request, 'crm/dashboard.html', context)

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

# ============= VISTAS AJAX =============

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

# ============= REPORTES =============

@login_required
def reporte_pipeline(request):
    """Reporte del pipeline de ventas"""
    
    # Datos por estado
    pipeline_data = []
    for estado_value, estado_label in EstadoOportunidad.choices:
        oportunidades = Oportunidad.objects.filter(estado=estado_value)
        valor_total = oportunidades.aggregate(Sum('valor_estimado'))['valor_estimado__sum'] or 0
        
        pipeline_data.append({
            'estado': estado_label,
            'count': oportunidades.count(),
            'valor': valor_total
        })
    
    context = {
        'pipeline_data': pipeline_data,
    }
    
    return render(request, 'crm/reporte_pipeline.html', context)
