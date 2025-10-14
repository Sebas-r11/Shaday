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
    """Mixin para permitir acceso tanto a ventas como a bodega y repartidores"""
    def test_func(self):
        return (self.request.user.can_create_sales() or 
                self.request.user.can_prepare_orders() or
                self.request.user.can_deliver_orders())

class PedidoListView(VentasYBodegaMixin, ListView):
    """Lista de pedidos"""
    model = Pedido
    template_name = 'ventas/pedido_list.html'
    context_object_name = 'pedidos'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Pedido.objects.select_related('cliente', 'asignado_a')
        
        # Lógica específica para repartidores
        if self.request.user.can_deliver_orders() and not self.request.user.can_create_sales():
            # Repartidores solo ven pedidos completados (alistados) y disponibles para entrega
            queryset = queryset.filter(
                estado='completado',
                # Solo pedidos sin entrega asignada (relacionada con 'entregas')
                entregas__isnull=True
            ).distinct()
        
        # Filtros comunes
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(numero__icontains=search) |
                Q(cliente__nombre__icontains=search) |
                Q(cliente__documento__icontains=search)
            )
        
        estado = self.request.GET.get('estado')
        if estado and not (self.request.user.can_deliver_orders() and not self.request.user.can_create_sales()):
            # Los repartidores no pueden filtrar por estado (ya están pre-filtrados)
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
        
        # Contexto específico para repartidores
        if self.request.user.can_deliver_orders() and not self.request.user.can_create_sales():
            context['es_repartidor'] = True
            context['total_disponibles'] = Pedido.objects.filter(
                estado='completado', 
                entregas__isnull=True
            ).count()
            context['title'] = 'Pedidos Disponibles para Entrega'
        else:
            context['es_repartidor'] = False
            context['total_pedidos'] = Pedido.objects.count()
            context['pedidos_pendientes'] = Pedido.objects.filter(estado='pendiente').count()
            context['pedidos_alistamiento'] = Pedido.objects.filter(estado='alistamiento').count()
            context['pedidos_completados'] = Pedido.objects.filter(estado='completado').count()
            context['title'] = 'Lista de Pedidos'
        
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
        context['puede_cambiar_estado'] = self.request.user.can_adjust_inventory()
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
        usuario_actual = self.request.user
        filtro_estado = self.request.GET.get('estado')
        
        # Debug detallado
        print("=== DEBUG ALISTAMIENTO ===")
        print(f"Usuario: {usuario_actual}")
        print(f"Filtro: {filtro_estado}")
        
        # Mostrar TODOS los pedidos para debug
        todos_pedidos = Pedido.objects.all().values('numero', 'estado', 'asignado_a__username')
        print("Todos los pedidos en la BD:")
        for pedido in todos_pedidos:
            print(f"  - {pedido['numero']}: estado='{pedido['estado']}', asignado_a={pedido['asignado_a__username']}")
        
        if filtro_estado == 'pendiente':
            queryset = Pedido.objects.filter(
                Q(estado='pendiente') |
                Q(estado='proceso', asignado_a__isnull=True)
            )
            pedidos = list(queryset.order_by('fecha_creacion'))
        elif filtro_estado == 'proceso':
            queryset = Pedido.objects.filter(
                estado='proceso',
                asignado_a=usuario_actual
            )
            pedidos = list(queryset.order_by('fecha_creacion'))
        else:
            queryset = Pedido.objects.filter(
                Q(estado='pendiente') |
                Q(estado='proceso', asignado_a__isnull=True) |
                Q(estado='proceso', asignado_a=usuario_actual)
            )
            pedidos = list(queryset.order_by('fecha_creacion'))
        # Verificar stock por cada item de cada pedido
        from inventario.models import Stock
        # Enriquecer cada pedido con una lista de items con atributos extra
        for pedido in pedidos:
            items_enriquecidos = []
            for item in pedido.items.all():
                bodega_usuario = self.request.user.bodega
                stock_disponible = 0
                stock_obj = None
                if bodega_usuario:
                    stock_obj = Stock.objects.filter(producto=item.producto, bodega=bodega_usuario).first()
                    if stock_obj:
                        stock_disponible = stock_obj.cantidad - stock_obj.cantidad_reservada
                    else:
                        stock_disponible = 0
                else:
                    stock_disponible = 0
                print(f"DEBUG STOCK: Producto={item.producto.codigo} | Cantidad={stock_obj.cantidad if stock_obj else 'N/A'} | Reservado={stock_obj.cantidad_reservada if stock_obj else 'N/A'} | Disponible={stock_disponible} | Fórmula: {stock_obj.cantidad if stock_obj else 0} - {stock_obj.cantidad_reservada if stock_obj else 0}")
                item.stock_disponible = stock_disponible
                item.stock_suficiente = stock_disponible >= item.cantidad
                item.sin_stock = stock_disponible < item.cantidad
                items_enriquecidos.append(item)
            pedido.items_enriquecidos = items_enriquecidos
        print(f"DEBUG FINAL: Se retorna {len(pedidos)} pedidos en alistamiento")
        return pedidos
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_actual = self.request.user
        
        # Contadores específicos para el usuario actual
        context['usuario_actual'] = usuario_actual
        
        # Pendientes: estado pendiente + proceso sin asignar (disponibles)
        context['total_pendientes'] = Pedido.objects.filter(
            Q(estado='pendiente') | Q(estado='proceso', asignado_a__isnull=True)
        ).count()
        
        # En proceso: solo los asignados a mí
        context['total_proceso'] = Pedido.objects.filter(
            estado='proceso',
            asignado_a=usuario_actual
        ).count()
        
        # Total de alistamiento
        context['total_alistamiento'] = context['total_pendientes'] + context['total_proceso']
        context['total_completado'] = Pedido.objects.filter(estado='completado').count()
        return context


@login_required
def completar_alistamiento(request, pk):
    """Completar alistamiento de pedido"""
    if not request.user.can_adjust_inventory():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    pedido = get_object_or_404(Pedido, pk=pk)
    
    if pedido.estado != 'proceso':
        return JsonResponse({'error': 'Pedido no está en proceso'}, status=400)

    # Validar que todos los items tengan suficiente stock en la bodega del usuario
    bodega_usuario = request.user.bodega
    from inventario.models import Stock
    items_sin_stock = []
    for item in pedido.items.all():
        if bodega_usuario:
            stock_qs = Stock.objects.filter(producto=item.producto, bodega=bodega_usuario)
            stock_disponible = sum([s.cantidad - s.cantidad_reservada for s in stock_qs])
        else:
            stock_disponible = 0
        if stock_disponible < item.cantidad:
            items_sin_stock.append(f"{item.producto.nombre} (Disponible: {stock_disponible}, Requerido: {item.cantidad})")

    if items_sin_stock:
        return JsonResponse({
            'error': 'No se puede completar el alistamiento. Stock insuficiente en los siguientes productos:',
            'items': items_sin_stock
        }, status=400)

    # Reservar el stock de cada item en la bodega del usuario
    import logging
    logger = logging.getLogger("django")
    for item in pedido.items.all():
        if bodega_usuario:
            from inventario.models import Stock
            stock_obj = Stock.objects.filter(producto=item.producto, bodega=bodega_usuario).first()
            if stock_obj:
                resultado = stock_obj.reservar(item.cantidad, usuario=request.user, pedido_id=pedido.id, observaciones="Reserva por alistamiento")
                logger.info(f"Reserva pedido {pedido.numero} - Producto: {item.producto.codigo} - Cantidad: {item.cantidad} - Resultado: {resultado} - Reservado ahora: {stock_obj.cantidad_reservada}")
            else:
                logger.warning(f"No se encontró Stock para producto {item.producto.codigo} en bodega {bodega_usuario}")

    pedido.estado = 'completado'
    pedido.save()

    from django.shortcuts import redirect
    return redirect('ventas:pedidos_alistamiento')


# ============= FUNCIONES PARA REPARTIDORES =============

@login_required
def tomar_pedido_repartidor(request, pk):
    """Permite a un repartidor tomar un pedido disponible"""
    if not request.user.can_deliver_orders():
        return JsonResponse({'error': 'Sin permisos para tomar pedidos'}, status=403)
    
    pedido = get_object_or_404(Pedido, pk=pk)
    
    # Verificar que el pedido esté disponible
    if pedido.estado != 'completado':
        return JsonResponse({'error': 'Pedido no está disponible para entrega'}, status=400)
    
    # Verificar que no tenga entrega asignada
    if pedido.entregas.exists():
        return JsonResponse({'error': 'Pedido ya tiene entrega asignada'}, status=400)
    
    # Crear entrega y asignar al repartidor actual
    from .models import Entrega
    try:
        entrega = Entrega.objects.create(
            pedido=pedido,
            repartidor=request.user,
            direccion_entrega=pedido.cliente.direccion,
            telefono_contacto=pedido.cliente.telefono,
            estado='asignada',
            fecha_programada=timezone.now()
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Pedido {pedido.numero} asignado exitosamente',
            'entrega_id': entrega.id
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Error al asignar pedido: {str(e)}'}, status=500)


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


@login_required
def crear_entregas_masivas(request):
    """Permite a repartidores crear múltiples entregas de una vez"""
    if not request.user.can_deliver_orders():
        return JsonResponse({'error': 'Sin permisos para crear entregas'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        pedido_ids = data.get('pedidos', [])
        fecha_programada = data.get('fecha_programada', None)
        
        if not pedido_ids:
            return JsonResponse({'error': 'No se seleccionaron pedidos'}, status=400)
        
        # Verificar que los pedidos estén disponibles
        pedidos = Pedido.objects.filter(
            id__in=pedido_ids,
            estado='completado',
            entregas__isnull=True
        )
        
        if pedidos.count() != len(pedido_ids):
            return JsonResponse({'error': 'Algunos pedidos ya no están disponibles'}, status=400)
        
        # Procesar fecha programada
        if fecha_programada:
            from datetime import datetime
            try:
                fecha_programada = datetime.strptime(fecha_programada, '%Y-%m-%d %H:%M')
            except ValueError:
                fecha_programada = timezone.now()
        else:
            fecha_programada = timezone.now()
        
        # Crear entregas
        from .models import Entrega
        entregas_creadas = []
        
        for pedido in pedidos:
            entrega = Entrega.objects.create(
                pedido=pedido,
                repartidor=request.user,
                direccion_entrega=pedido.cliente.direccion,
                telefono_contacto=pedido.cliente.telefono,
                estado='asignada',
                fecha_programada=fecha_programada
            )
            entregas_creadas.append(entrega)
        
        return JsonResponse({
            'success': True,
            'message': f'Se crearon {len(entregas_creadas)} entregas exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Error al crear entregas: {str(e)}'}, status=500)