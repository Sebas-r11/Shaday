# ventas/entregas_views.py
"""
Vistas especializadas para gestión de entregas y repartidores
Extraído de ventas/views.py para mejorar organización
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import datetime

from .models import Entrega, Pedido, Factura
# from .models import EntregaItem  # No existe
from .forms import CompletarEntregaForm
# from .forms import EntregaForm, AsignarRepartidorForm  # No existen


class VentasRequiredMixin(UserPassesTestMixin):
    """Mixin para verificar permisos de ventas"""
    def test_func(self):
        return self.request.user.can_create_sales()


class RepartidorRequiredMixin(UserPassesTestMixin):
    """Mixin para verificar permisos de repartidor"""
    def test_func(self):
        return self.request.user.is_repartidor()


# ============= VISTAS DE ENTREGAS =============

class EntregaListView(VentasRequiredMixin, ListView):
    """Lista de entregas"""
    model = Entrega
    template_name = 'ventas/entrega_list.html'
    context_object_name = 'entregas'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Entrega.objects.select_related('pedido', 'repartidor')
        
        # Filtros
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(numero__icontains=search) |
                Q(pedido__numero__icontains=search) |
                Q(factura__numero__icontains=search) |
                Q(cliente_nombre__icontains=search)
            )
        
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        repartidor = self.request.GET.get('repartidor')
        if repartidor:
            queryset = queryset.filter(repartidor__id=repartidor)
        
        fecha_desde = self.request.GET.get('fecha_desde')
        if fecha_desde:
            queryset = queryset.filter(fecha_programada__date__gte=fecha_desde)
        
        fecha_hasta = self.request.GET.get('fecha_hasta')
        if fecha_hasta:
            queryset = queryset.filter(fecha_programada__date__lte=fecha_hasta)
        
        return queryset.order_by('-fecha_programada')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_entregas'] = Entrega.objects.count()
        context['entregas_pendientes'] = Entrega.objects.filter(estado='pendiente').count()
        context['entregas_en_ruta'] = Entrega.objects.filter(estado='en_ruta').count()
        context['entregas_entregadas'] = Entrega.objects.filter(estado='entregada').count()
        return context


# CLASE TEMPORALMENTE DESACTIVADA - EntregaForm no existe
# class EntregaCreateView(VentasRequiredMixin, CreateView):
#     """Crear nueva entrega"""
#     model = Entrega
#     form_class = EntregaForm
#     template_name = 'ventas/entrega_form.html'
#     success_url = reverse_lazy('ventas:entrega_list')
#     
#     def form_valid(self, form):
#         messages.success(self.request, f'Entrega {form.instance.numero} creada exitosamente.')
#         return super().form_valid(form)


class EntregaDetailView(VentasRequiredMixin, DetailView):
    """Detalle de entrega"""
    model = Entrega
    template_name = 'ventas/entrega_detail.html'
    context_object_name = 'entrega'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['puede_asignar'] = self.request.user.can_create_sales()
        context['es_repartidor'] = self.request.user.is_repartidor()
        # context['form_asignar'] = AsignarRepartidorForm(instance=self.object)  # Form no existe
        return context


# ============= VISTAS PARA REPARTIDORES =============

class EntregasRepartidorView(RepartidorRequiredMixin, ListView):
    """Vista para repartidores - sus entregas asignadas"""
    model = Entrega
    template_name = 'ventas/entregas_repartidor.html'
    context_object_name = 'entregas'
    
    def get_queryset(self):
        return Entrega.objects.filter(
            repartidor=self.request.user,
            estado__in=['asignada', 'en_ruta']
        ).order_by('fecha_programada')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entregas_pendientes'] = self.get_queryset().filter(estado='asignada').count()
        context['entregas_en_ruta'] = self.get_queryset().filter(estado='en_ruta').count()
        return context


# ============= ACCIONES DE ENTREGAS =============

# FUNCIÓN TEMPORALMENTE DESACTIVADA - AsignarRepartidorForm no existe
# @login_required
# def asignar_repartidor(request, pk):
#     """Asignar repartidor a entrega"""
#     if not request.user.can_create_sales():
#         messages.error(request, 'No tienes permisos para asignar repartidores.')
#         return redirect('ventas:entrega_list')
#     
#     entrega = get_object_or_404(Entrega, pk=pk)
#     
#     if request.method == 'POST':
#         form = AsignarRepartidorForm(request.POST, instance=entrega)
#         if form.is_valid():
#             entrega = form.save()
#             entrega.estado = 'asignada'
#             entrega.fecha_asignacion = timezone.now()
#             entrega.save()
#             
#             messages.success(request, f'Repartidor asignado a entrega {entrega.numero}.')
#     
#     return redirect('ventas:entrega_detail', pk=pk)


@login_required
def iniciar_entrega(request, pk):
    """Repartidor inicia la entrega"""
    if not request.user.is_repartidor():
        return JsonResponse({'error': 'Solo repartidores pueden iniciar entregas'}, status=403)
    
    entrega = get_object_or_404(Entrega, pk=pk, repartidor=request.user)
    
    if entrega.estado != 'asignada':
        return JsonResponse({'error': 'La entrega ya fue iniciada o completada'}, status=400)
    
    entrega.estado = 'en_ruta'
    entrega.fecha_inicio = timezone.now()
    entrega.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Entrega {entrega.numero} iniciada exitosamente'
    })


@login_required
def completar_entrega(request, pk):
    """Repartidor completa la entrega"""
    if not request.user.is_repartidor():
        messages.error(request, 'Solo repartidores pueden completar entregas.')
        return redirect('ventas:entrega_list')
    
    entrega = get_object_or_404(Entrega, pk=pk, repartidor=request.user)
    
    if entrega.estado != 'en_ruta':
        messages.error(request, 'La entrega no está en ruta.')
        return redirect('ventas:entregas_repartidor')
    
    if request.method == 'POST':
        observaciones = request.POST.get('observaciones', '')
        
        entrega.estado = 'entregada'
        entrega.fecha_entrega = timezone.now()
        entrega.observaciones_entrega = observaciones
        entrega.save()
        
        messages.success(request, f'Entrega {entrega.numero} completada exitosamente.')
        return redirect('ventas:entregas_repartidor')
    
    return render(request, 'ventas/completar_entrega.html', {'entrega': entrega})


@login_required
def reportar_problema_entrega(request, pk):
    """Reportar problema en entrega"""
    if not request.user.is_repartidor():
        return JsonResponse({'error': 'Solo repartidores pueden reportar problemas'}, status=403)
    
    entrega = get_object_or_404(Entrega, pk=pk, repartidor=request.user)
    
    if request.method == 'POST':
        problema = request.POST.get('problema', '')
        
        entrega.estado = 'problema'
        entrega.fecha_problema = timezone.now()
        entrega.observaciones_problema = problema
        entrega.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Problema reportado para entrega {entrega.numero}'
        })
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


# ============= API DE ENTREGAS =============

@login_required
def completar_entrega_api(request, pk):
    """API para completar entrega desde móvil"""
    if not request.user.is_repartidor():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    entrega = get_object_or_404(Entrega, pk=pk, repartidor=request.user)
    
    if entrega.estado != 'en_ruta':
        return JsonResponse({'error': 'Entrega no está en ruta'}, status=400)
    
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        
        entrega.estado = 'entregada'
        entrega.fecha_entrega = timezone.now()
        entrega.observaciones_entrega = data.get('observaciones', '')
        entrega.latitud_entrega = data.get('latitud')
        entrega.longitud_entrega = data.get('longitud')
        entrega.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Entrega {entrega.numero} completada exitosamente'
        })
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def obtener_entregas_repartidor(request):
    """API para obtener entregas del repartidor"""
    if not request.user.is_repartidor():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    entregas = Entrega.objects.filter(
        repartidor=request.user,
        estado__in=['asignada', 'en_ruta']
    ).select_related('pedido')
    
    data = []
    for entrega in entregas:
        data.append({
            'id': entrega.id,
            'numero': entrega.numero,
            'cliente_nombre': entrega.cliente_nombre,
            'direccion': entrega.direccion_entrega,
            'telefono': entrega.telefono_contacto,
            'estado': entrega.estado,
            'fecha_programada': entrega.fecha_programada.strftime('%d/%m/%Y %H:%M') if entrega.fecha_programada else '',
            'observaciones': entrega.observaciones,
            'valor_total': float(entrega.valor_total) if entrega.valor_total else 0
        })
    
    return JsonResponse(data, safe=False)


@login_required
def actualizar_ubicacion_repartidor(request):
    """API para actualizar ubicación del repartidor"""
    if not request.user.is_repartidor():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        
        latitud = data.get('latitud')
        longitud = data.get('longitud')
        
        # Actualizar ubicación en el perfil del usuario o crear un modelo de seguimiento
        # Por ahora solo devolvemos éxito
        
        return JsonResponse({
            'success': True,
            'message': 'Ubicación actualizada'
        })
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


# ============= REPORTES DE ENTREGAS =============

@login_required
def reporte_entregas_periodo(request):
    """Reporte de entregas por período"""
    if not request.user.can_create_sales():
        return HttpResponse('Sin permisos', status=403)
    
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if not fecha_desde or not fecha_hasta:
        messages.error(request, 'Debe especificar fecha desde y fecha hasta.')
        return redirect('ventas:entrega_list')
    
    entregas = Entrega.objects.filter(
        fecha_programada__date__gte=fecha_desde,
        fecha_programada__date__lte=fecha_hasta
    ).select_related('repartidor', 'pedido')
    
    # Estadísticas
    total_entregas = entregas.count()
    entregas_completadas = entregas.filter(estado='entregada').count()
    entregas_pendientes = entregas.filter(estado__in=['pendiente', 'asignada', 'en_ruta']).count()
    entregas_problemas = entregas.filter(estado='problema').count()
    
    # Entregas por repartidor
    entregas_repartidor = entregas.values(
        'repartidor__first_name',
        'repartidor__last_name'
    ).annotate(
        total=Count('id'),
        completadas=Count('id', filter=Q(estado='entregada'))
    ).order_by('-total')
    
    context = {
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'entregas': entregas,
        'total_entregas': total_entregas,
        'entregas_completadas': entregas_completadas,
        'entregas_pendientes': entregas_pendientes,
        'entregas_problemas': entregas_problemas,
        'entregas_repartidor': entregas_repartidor
    }
    
    return render(request, 'ventas/reporte_entregas.html', context)


@login_required
def estadisticas_entregas_api(request):
    """API para estadísticas de entregas"""
    if not request.user.can_create_sales():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    # Entregas del día
    from django.utils import timezone
    hoy = timezone.now().date()
    
    entregas_hoy = Entrega.objects.filter(fecha_programada__date=hoy)
    
    stats = {
        'entregas_hoy': entregas_hoy.count(),
        'completadas_hoy': entregas_hoy.filter(estado='entregada').count(),
        'en_ruta_hoy': entregas_hoy.filter(estado='en_ruta').count(),
        'pendientes_hoy': entregas_hoy.filter(estado__in=['pendiente', 'asignada']).count(),
        'problemas_hoy': entregas_hoy.filter(estado='problema').count()
    }
    
    return JsonResponse(stats)