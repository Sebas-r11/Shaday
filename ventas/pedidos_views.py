# ventas/pedidos_views.py
"""
Vistas especializadas para gestión de pedidos
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

from .models import Pedido, ItemPedido, Cliente
from inventario.models import Producto
from .forms import PedidoForm
# from .forms import CambiarEstadoPedidoForm  # No existe


class VentasRequiredMixin(UserPassesTestMixin):
    """Mixin para verificar permisos de ventas"""
    def test_func(self):
        return self.request.user.can_create_sales()


class BodegaRequiredMixin(UserPassesTestMixin):
    """Mixin para verificar permisos de bodega"""
    def test_func(self):
        return self.request.user.can_prepare_orders()


# ============= VISTAS DE PEDIDOS =============

class VentasYBodegaMixin(UserPassesTestMixin):
    """Mixin para permitir acceso tanto a ventas como a bodega"""
    def test_func(self):
        return (self.request.user.can_create_sales() or 
                self.request.user.can_prepare_orders())

class PedidoListView(VentasYBodegaMixin, ListView):
    """Lista de pedidos"""
    model = Pedido
    template_name = 'ventas/pedido_list.html'
    context_object_name = 'pedidos'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Pedido.objects.select_related('cliente', 'asignado_a')
        
        # Filtros
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(numero__icontains=search) |
                Q(cliente__nombre__icontains=search) |
                Q(cliente__documento__icontains=search)
            )
        
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        vendedor = self.request.GET.get('vendedor')
        if vendedor:
            queryset = queryset.filter(vendedor__id=vendedor)
        
        fecha_desde = self.request.GET.get('fecha_desde')
        if fecha_desde:
            queryset = queryset.filter(fecha_creacion__date__gte=fecha_desde)
        
        fecha_hasta = self.request.GET.get('fecha_hasta')
        if fecha_hasta:
            queryset = queryset.filter(fecha_creacion__date__lte=fecha_hasta)
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_pedidos'] = Pedido.objects.count()
        context['pedidos_pendientes'] = Pedido.objects.filter(estado='pendiente').count()
        context['pedidos_alistamiento'] = Pedido.objects.filter(estado='alistamiento').count()
        context['pedidos_completados'] = Pedido.objects.filter(estado='completado').count()
        return context


class PedidoCreateView(VentasRequiredMixin, CreateView):
    """Crear nuevo pedido"""
    model = Pedido
    form_class = PedidoForm
    template_name = 'ventas/pedido_form.html'
    success_url = reverse_lazy('ventas:pedido_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # FormSet temporalmente desactivado - PedidoItemFormSet no existe
        # if self.request.POST:
        #     context['items_formset'] = PedidoItemFormSet(self.request.POST)
        # else:
        #     context['items_formset'] = PedidoItemFormSet()
        return context
    
    def form_valid(self, form):
        # context = self.get_context_data()
        # items_formset = context['items_formset']
        
        # FormSet temporalmente desactivado
        # if form.is_valid() and items_formset.is_valid():
        if form.is_valid():
            form.instance.vendedor = self.request.user
            pedido = form.save()
            
            items_formset.instance = pedido
            items_formset.save()
            
            # Calcular totales
            pedido.calcular_totales()
            pedido.save()
            
            messages.success(self.request, f'Pedido {pedido.numero} creado exitosamente.')
            return redirect('ventas:pedido_detail', pk=pedido.pk)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class PedidoDetailView(VentasRequiredMixin, DetailView):
    """Detalle de pedido"""
    model = Pedido
    template_name = 'ventas/pedido_detail.html'
    context_object_name = 'pedido'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['puede_cambiar_estado'] = self.request.user.can_manage_inventory()
        # context['form_estado'] = CambiarEstadoPedidoForm(instance=self.object)  # Form no existe
        return context


class PedidoUpdateView(VentasRequiredMixin, UpdateView):
    """Editar pedido"""
    model = Pedido
    form_class = PedidoForm
    template_name = 'ventas/pedido_form.html'
    
    def get_queryset(self):
        # Solo permitir editar pedidos pendientes
        return Pedido.objects.filter(estado='pendiente')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # FormSet temporalmente desactivado - PedidoItemFormSet no existe  
        # if self.request.POST:
        #     context['items_formset'] = PedidoItemFormSet(
        #         self.request.POST, 
        #         instance=self.object
        #     )
        # else:
        #     context['items_formset'] = PedidoItemFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        # context = self.get_context_data()
        # items_formset = context['items_formset']
        
        # FormSet temporalmente desactivado
        # if form.is_valid() and items_formset.is_valid():
        if form.is_valid():
            pedido = form.save()
            # items_formset.save()
            
            # Recalcular totales
            pedido.calcular_totales()
            pedido.save()
            
            messages.success(self.request, f'Pedido {pedido.numero} actualizado exitosamente.')
            return redirect('ventas:pedido_detail', pk=pedido.pk)
        else:
            return self.render_to_response(self.get_context_data(form=form))


# ============= ACCIONES DE PEDIDOS =============

# FUNCIÓN TEMPORALMENTE DESACTIVADA - CambiarEstadoPedidoForm no existe
# @login_required
# def cambiar_estado_pedido(request, pk):
#     """Cambiar estado del pedido"""
#     if not request.user.can_manage_inventory():
#         messages.error(request, 'No tienes permisos para cambiar el estado de pedidos.')
#         return redirect('ventas:pedido_list')
#     
#     pedido = get_object_or_404(Pedido, pk=pk)
#     
#     if request.method == 'POST':
#         form = CambiarEstadoPedidoForm(request.POST, instance=pedido)
#         if form.is_valid():
#             nuevo_estado = form.cleaned_data['estado']
#             
#             # Validaciones de cambio de estado
#             if pedido.estado == 'pendiente' and nuevo_estado == 'alistamiento':
#                 # Verificar stock disponible
#                 stock_suficiente = True
#                 items_sin_stock = []
#                 
#                 for item in pedido.items.all():
#                     if item.producto.stock < item.cantidad:
#                         stock_suficiente = False
#                         items_sin_stock.append(f"{item.producto.nombre} (Disponible: {item.producto.stock}, Requerido: {item.cantidad})")
#                 
#                 if not stock_suficiente:
#                     messages.error(request, f'Stock insuficiente para los siguientes productos: {", ".join(items_sin_stock)}')
#                     return redirect('ventas:pedido_detail', pk=pk)
#                 
#                 # Reservar stock
#                 for item in pedido.items.all():
#                     item.producto.stock -= item.cantidad
#                     item.producto.save()
#                 
#                 pedido.estado = 'alistamiento'
#                 pedido.fecha_alistamiento = timezone.now()
#                 
#             elif pedido.estado == 'alistamiento' and nuevo_estado == 'completado':
#                 pedido.estado = 'completado'
#                 pedido.fecha_completado = timezone.now()
#                 
#             elif pedido.estado == 'alistamiento' and nuevo_estado == 'pendiente':
#                 # Liberar stock reservado
#                 for item in pedido.items.all():
#                     item.producto.stock += item.cantidad
#                     item.producto.save()
#                 
#                 pedido.estado = 'pendiente'
#                 pedido.fecha_alistamiento = None
#                 
#             else:
#                 messages.error(request, 'Cambio de estado no válido.')
#                 return redirect('ventas:pedido_detail', pk=pk)
#             
#             pedido.save()
#             messages.success(request, f'Estado del pedido cambiado a {pedido.get_estado_display()}')
#     
#     return redirect('ventas:pedido_detail', pk=pk)


@login_required
def cancelar_pedido(request, pk):
    """Cancelar pedido"""
    if not request.user.can_create_sales():
        messages.error(request, 'No tienes permisos para cancelar pedidos.')
        return redirect('ventas:pedido_list')
    
    pedido = get_object_or_404(Pedido, pk=pk)
    
    if pedido.estado in ['completado', 'facturado']:
        messages.error(request, 'No se puede cancelar un pedido completado o facturado.')
        return redirect('ventas:pedido_detail', pk=pk)
    
    if pedido.estado == 'alistamiento':
        # Liberar stock reservado
        for item in pedido.items.all():
            item.producto.stock += item.cantidad
            item.producto.save()
    
    pedido.estado = 'cancelado'
    pedido.fecha_cancelacion = timezone.now()
    pedido.usuario_cancelacion = request.user
    pedido.save()
    
    messages.success(request, f'Pedido {pedido.numero} cancelado exitosamente.')
    return redirect('ventas:pedido_detail', pk=pk)


@login_required
def convertir_pedido_factura(request, pk):
    """Convertir pedido a factura"""
    if not request.user.can_create_sales():
        messages.error(request, 'No tienes permisos para crear facturas.')
        return redirect('ventas:pedido_list')
    
    pedido = get_object_or_404(Pedido, pk=pk)
    
    if pedido.estado != 'completado':
        messages.error(request, 'Solo se pueden facturar pedidos completados.')
        return redirect('ventas:pedido_detail', pk=pk)
    
    from .models import Factura, FacturaItem
    
    # Crear factura
    factura = Factura.objects.create(
        cliente=pedido.cliente,
        vendedor=pedido.vendedor,
        pedido=pedido,
        observaciones=f"Generada desde pedido {pedido.numero}",
        subtotal=pedido.subtotal,
        impuestos=pedido.impuestos,
        total=pedido.total,
        estado='pendiente'
    )
    
    # Copiar items
    for item in pedido.items.all():
        FacturaItem.objects.create(
            factura=factura,
            producto=item.producto,
            cantidad=item.cantidad,
            precio_unitario=item.precio_unitario,
            descuento=item.descuento,
            subtotal=item.subtotal
        )
    
    # Marcar pedido como facturado
    pedido.estado = 'facturado'
    pedido.save()
    
    messages.success(request, f'Pedido convertido a factura {factura.numero} exitosamente.')
    return redirect('ventas:factura_detail', pk=factura.pk)


# ============= VISTAS DE ALISTAMIENTO =============

class PedidosAlistamientoView(BodegaRequiredMixin, ListView):
    """Vista para bodegueros - pedidos en alistamiento"""
    model = Pedido
    template_name = 'ventas/pedidos_alistamiento.html'
    context_object_name = 'pedidos'
    
    def get_queryset(self):
        return Pedido.objects.filter(
            estado='alistamiento'
        ).order_by('fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_alistamiento'] = self.get_queryset().count()
        # Agregar contadores para otros estados que el template pueda necesitar
        context['total_proceso'] = Pedido.objects.filter(estado='proceso').count()
        context['total_pendiente'] = Pedido.objects.filter(estado='pendiente').count()
        context['total_completado'] = Pedido.objects.filter(estado='completado').count()
        return context


@login_required
def completar_alistamiento(request, pk):
    """Completar alistamiento de pedido"""
    if not request.user.can_manage_inventory():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    pedido = get_object_or_404(Pedido, pk=pk)
    
    if pedido.estado != 'alistamiento':
        return JsonResponse({'error': 'Pedido no está en alistamiento'}, status=400)
    
    pedido.estado = 'completado'
    pedido.fecha_completado = timezone.now()
    pedido.usuario_completado = request.user
    pedido.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Pedido {pedido.numero} completado exitosamente'
    })


# ============= API PEDIDOS =============

@login_required
def obtener_pedidos_pendientes(request):
    """API para obtener pedidos pendientes"""
    if not request.user.can_manage_inventory():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    pedidos = Pedido.objects.filter(estado='pendiente').select_related('cliente')
    
    data = []
    for pedido in pedidos:
        data.append({
            'id': pedido.id,
            'numero': pedido.numero,
            'cliente': pedido.cliente.nombre_completo,
            'total': float(pedido.total),
            'fecha_creacion': pedido.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            'items_count': pedido.items.count()
        })
    
    return JsonResponse(data, safe=False)