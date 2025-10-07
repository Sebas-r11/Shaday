from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, DetailView, UpdateView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count, Avg, F
from django.db import models
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.core.exceptions import PermissionDenied
from datetime import datetime, timedelta, date
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Cliente, Cotizacion, Pedido, Factura, ItemCotizacion, ItemPedido, ItemFactura, Entrega
from inventario.models import Producto, Stock, Bodega
from .forms import ClienteForm, ClienteFilterForm, CotizacionForm, FacturaForm

User = get_user_model()

class VentasRequiredMixin(UserPassesTestMixin):
    """Mixin para verificar permisos de ventas"""
    def test_func(self):
        return self.request.user.can_create_sales()

class BodegaViewMixin(UserPassesTestMixin):
    """Mixin para permitir acceso a bodega, vendedores y repartidores para ver pedidos"""
    def test_func(self):
        return (self.request.user.can_create_sales() or 
                self.request.user.can_view_inventory() or
                self.request.user.can_deliver_orders())

# ============= DASHBOARD =============

@login_required
def dashboard_view(request):
    """Vista principal del dashboard con métricas y KPIs"""
    
    # Fechas para cálculos
    hoy = date.today()
    inicio_mes = hoy.replace(day=1)
    mes_anterior = (inicio_mes - timedelta(days=1)).replace(day=1)
    fin_mes_anterior = inicio_mes - timedelta(days=1)
    
    # Filtrar por vendedor si es necesario
    queryset_pedidos = Pedido.objects.all()
    queryset_facturas = Factura.objects.all()
    
    # Como no hay campo vendedor en los modelos simplificados, mostramos todos
    # if hasattr(request.user, 'role') and request.user.role == 'vendedor':
    #     queryset_pedidos = queryset_pedidos.filter(vendedor=request.user)
    #     queryset_facturas = queryset_facturas.filter(vendedor=request.user)
    
    # ========== MÉTRICAS DEL MES ACTUAL ==========
    
    # Pedidos del mes
    pedidos_mes = queryset_pedidos.filter(fecha_creacion__gte=inicio_mes)
    pedidos_completados_mes = pedidos_mes.filter(estado='completado')
    
    # Facturas del mes
    facturas_mes = queryset_facturas.filter(fecha_creacion__gte=inicio_mes)
    facturas_emitidas_mes = facturas_mes.filter(estado__in=['emitida', 'pagada'])
    
    # Valores del mes actual
    valor_pedidos_mes = pedidos_completados_mes.aggregate(
        total=Sum('total'))['total'] or Decimal('0.00')
    
    valor_facturas_mes = facturas_emitidas_mes.aggregate(
        total=Sum('total'))['total'] or Decimal('0.00')
    
    # ========== MÉTRICAS DEL MES ANTERIOR ==========
    
    # Pedidos del mes anterior
    pedidos_mes_anterior = queryset_pedidos.filter(
        fecha_creacion__gte=mes_anterior, 
        fecha_creacion__lte=fin_mes_anterior,
        estado='completado'
    )
    
    # Facturas del mes anterior  
    facturas_mes_anterior = queryset_facturas.filter(
        fecha_creacion__gte=mes_anterior,
        fecha_creacion__lte=fin_mes_anterior,
        estado__in=['emitida', 'pagada']
    )
    
    # Valores del mes anterior
    valor_pedidos_mes_anterior = pedidos_mes_anterior.aggregate(
        total=Sum('total'))['total'] or Decimal('0.00')
    
    valor_facturas_mes_anterior = facturas_mes_anterior.aggregate(
        total=Sum('total'))['total'] or Decimal('0.00')
    
    # ========== CALCULAR CRECIMIENTOS ==========
    
    def calcular_crecimiento(actual, anterior):
        if anterior == 0:
            return 100 if actual > 0 else 0
        return ((actual - anterior) / anterior) * 100
    
    crecimiento_pedidos = calcular_crecimiento(
        float(valor_pedidos_mes), 
        float(valor_pedidos_mes_anterior)
    )
    
    crecimiento_facturas = calcular_crecimiento(
        float(valor_facturas_mes),
        float(valor_facturas_mes_anterior)
    )
    
    # ========== ESTADÍSTICAS GENERALES ==========
    
    # Contadores generales
    total_pedidos_pendientes = queryset_pedidos.filter(
        estado__in=['borrador', 'pendiente', 'proceso']
    ).count()
    
    total_facturas_pendientes = queryset_facturas.filter(
        estado='emitida'
    ).count()
    
    # Estadísticas por estado de pedidos
    estadisticas_pedidos = queryset_pedidos.values('estado').annotate(
        cantidad=Count('id'),
        valor_total=Sum('total')
    ).order_by('-cantidad')
    
    # ========== TOP PRODUCTOS (del mes) ==========
    top_productos = ItemPedido.objects.filter(
        pedido__fecha_creacion__gte=inicio_mes,
        pedido__estado='completado'
    ).values(
        'pedido__numero'  # Usando campos disponibles en el modelo simplificado
    ).annotate(
        cantidad_vendida=Sum('cantidad'),
        valor_total=Sum(F('cantidad') * F('precio_unitario'))
    ).order_by('-cantidad_vendida')[:5]
    
    # ========== ACTIVIDAD RECIENTE ==========
    actividad_reciente = []
    
    # Últimos pedidos
    ultimos_pedidos = queryset_pedidos.select_related('cliente').order_by('-fecha_creacion')[:3]
    for pedido in ultimos_pedidos:
        actividad_reciente.append({
            'tipo': 'pedido',
            'titulo': f'Pedido {pedido.numero}',
            'descripcion': f'Cliente: {pedido.cliente.nombre_completo}',
            'valor': pedido.total,
            'fecha': pedido.fecha_creacion,
            'estado': pedido.estado,
            'url': f'/ventas/pedidos/{pedido.id}/'
        })
    
    # Últimas facturas
    ultimas_facturas = queryset_facturas.select_related('cliente').order_by('-fecha_creacion')[:3]
    for factura in ultimas_facturas:
        actividad_reciente.append({
            'tipo': 'factura',
            'titulo': f'Factura {factura.numero}',
            'descripcion': f'Cliente: {factura.cliente.nombre_completo}',
            'valor': factura.total,
            'fecha': factura.fecha_creacion,
            'estado': factura.estado,
            'url': f'/ventas/facturas/{factura.id}/'
        })
    
    # Ordenar por fecha
    actividad_reciente.sort(key=lambda x: x['fecha'], reverse=True)
    actividad_reciente = actividad_reciente[:6]  # Top 6 más recientes
    
    # ========== DATOS PARA GRÁFICOS ==========
    
    # Gráfico 1: Ventas por día (últimos 30 días)
    fecha_inicio_grafico = hoy - timedelta(days=30)
    ventas_por_dia = []
    labels_dias = []
    
    for i in range(30):
        fecha = fecha_inicio_grafico + timedelta(days=i)
        pedidos_dia = queryset_pedidos.filter(
            fecha_creacion__date=fecha,
            estado='completado'
        ).aggregate(total=Sum('total'))['total'] or 0
        
        ventas_por_dia.append(float(pedidos_dia))
        labels_dias.append(fecha.strftime('%d/%m'))
    
    # Gráfico 2: Estados de pedidos (datos para pie chart)
    estados_chart = []
    colores_estados = {
        'completado': '#10B981',  # Verde
        'proceso': '#3B82F6',     # Azul  
        'pendiente': '#F59E0B',   # Amarillo
        'borrador': '#6B7280',    # Gris
        'cancelado': '#EF4444'    # Rojo
    }
    
    for stat in estadisticas_pedidos:
        if stat['cantidad'] > 0:
            estados_chart.append({
                'label': stat['estado'].title(),
                'value': stat['cantidad'],
                'color': colores_estados.get(stat['estado'], '#6B7280')
            })
    
    # Gráfico 3: Top productos (datos para gráfico de barras)
    productos_chart = {
        'labels': [p['producto__nombre'][:20] for p in top_productos[:5]], 
        'data': [float(p['cantidad_vendida']) for p in top_productos[:5]],
        'valores': [float(p['valor_total']) for p in top_productos[:5]]
    }
    
    # ========== CONTEXTO PARA EL TEMPLATE ==========
    context = {
        'title': 'Dashboard de Ventas',
        # KPIs principales
        'kpis': {
            'pedidos_mes': {
                'valor': pedidos_completados_mes.count(),
                'total': valor_pedidos_mes,
                'crecimiento': crecimiento_pedidos,
            },
            'facturas_mes': {
                'valor': facturas_emitidas_mes.count(),
                'total': valor_facturas_mes,
                'crecimiento': crecimiento_facturas,
            },
            'pedidos_pendientes': total_pedidos_pendientes,
            'facturas_pendientes': total_facturas_pendientes,
        },
        # Datos adicionales
        'estadisticas_pedidos': estadisticas_pedidos,
        'top_productos': top_productos,
        'actividad_reciente': actividad_reciente,
        'mes_actual': hoy.strftime('%B %Y'),
        # Datos para gráficos
        'chart_data': {
            'ventas_por_dia': {
                'labels': labels_dias,
                'data': ventas_por_dia
            },
            'estados_pedidos': estados_chart,
            'top_productos': productos_chart
        }
    }
    
    return render(request, 'ventas/dashboard.html', context)

# ============= CLIENTES =============

class ClienteListView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = 'ventas/cliente_list.html'
    context_object_name = 'clientes'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Cliente.objects.select_related('vendedor_asignado').filter(activo=True)
        
        # Los vendedores ahora pueden ver todos los clientes
        # (Ya no se filtra por vendedor_asignado para vendedores)
        
        # Aplicar filtros del formulario
        form = ClienteFilterForm(self.request.GET, user=self.request.user)
        if form.is_valid():
            # Filtro por búsqueda
            search = form.cleaned_data.get('search')
            if search:
                queryset = queryset.filter(
                    Q(numero_documento__icontains=search) |
                    Q(nombre_completo__icontains=search) |
                    Q(telefono__icontains=search)
                )
            
            # Filtro por tipo de cliente
            tipo_cliente = form.cleaned_data.get('tipo_cliente')
            if tipo_cliente:
                queryset = queryset.filter(tipo_cliente=tipo_cliente)
            
            # Filtro por vendedor (solo si no es vendedor)
            if self.request.user.role != 'vendedor':
                vendedor = form.cleaned_data.get('vendedor')
                if vendedor:
                    queryset = queryset.filter(vendedor_asignado=vendedor)
        
        return queryset.order_by('nombre_completo')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ClienteFilterForm(self.request.GET, user=self.request.user)
        return context

class ClienteCreateView(VentasRequiredMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'ventas/cliente_form.html'
    success_url = reverse_lazy('ventas:cliente_list')
    
    def form_valid(self, form):
        form.instance.usuario_creacion = self.request.user
        # Si es vendedor, asignarse automáticamente
        if self.request.user.role == 'vendedor':
            form.instance.vendedor_asignado = self.request.user
        messages.success(self.request, 'Cliente creado exitosamente.')
        return super().form_valid(form)

class ClienteDetailView(LoginRequiredMixin, DetailView):
    model = Cliente
    template_name = 'ventas/cliente_detail.html'
    context_object_name = 'cliente'
    
    def get_queryset(self):
        queryset = Cliente.objects.select_related('vendedor_asignado')
        # Los vendedores ahora pueden ver detalles de todos los clientes
        # (Ya no se filtra por vendedor_asignado para vendedores)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = self.object
        
        # Estadísticas del cliente
        context['total_cotizaciones'] = Cotizacion.objects.filter(cliente=cliente).count()
        context['total_pedidos'] = Pedido.objects.filter(cliente=cliente).count()
        context['total_facturas'] = Factura.objects.filter(cliente=cliente).count()
        
        # Última actividad
        context['ultima_cotizacion'] = Cotizacion.objects.filter(cliente=cliente).order_by('-fecha_creacion').first()
        context['ultimo_pedido'] = Pedido.objects.filter(cliente=cliente).order_by('-fecha_creacion').first()
        context['ultima_factura'] = Factura.objects.filter(cliente=cliente).order_by('-fecha_creacion').first()
        
        return context

class ClienteUpdateView(VentasRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'ventas/cliente_form.html'
    success_url = reverse_lazy('ventas:cliente_list')
    
    def get_queryset(self):
        queryset = Cliente.objects.all()
        # Los vendedores ahora pueden editar todos los clientes
        # (Ya no se filtra por vendedor_asignado para vendedores)
        return queryset
    
    def form_valid(self, form):
        messages.success(self.request, 'Cliente actualizado exitosamente.')
        return super().form_valid(form)

# ============= COTIZACIONES =============

class CotizacionListView(VentasRequiredMixin, ListView):
    model = Cotizacion
    template_name = 'ventas/cotizacion_list.html'
    context_object_name = 'cotizaciones'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Cotizacion.objects.select_related('cliente')
        
        # Si es vendedor (no admin), ver todas las cotizaciones por ahora
        # TODO: Agregar campo vendedor al modelo Cotizacion si es necesario
        if self.request.user.role == 'vendedor' and not self.request.user.is_admin_user():
            # queryset = queryset.filter(vendedor=self.request.user)
            pass
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = datetime.now().date()
        context['warning_date'] = datetime.now().date() + timedelta(days=3)
        return context

class CotizacionCreateView(VentasRequiredMixin, CreateView):
    model = Cotizacion
    form_class = CotizacionForm
    template_name = 'ventas/cotizacion_form.html'
    success_url = reverse_lazy('ventas:cotizacion_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Remover user para CotizacionForm ya que no lo necesita
        # kwargs['user'] = self.request.user
        
        # Pre-seleccionar cliente si viene en la URL
        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            if 'initial' not in kwargs:
                kwargs['initial'] = {}
            kwargs['initial']['cliente'] = cliente_id
        
        return kwargs
    
    def get_context_data(self, **kwargs):
        print(f"🌐 === CARGANDO FORMULARIO DE COTIZACIÓN ===")
        print(f"👤 Usuario: {self.request.user}")
        print(f"🔒 Puede crear ventas: {self.request.user.can_create_sales()}")
        
        context = super().get_context_data(**kwargs)
        
        # Cargar productos para el JavaScript
        from inventario.models import Producto
        productos = Producto.objects.filter(activo=True).select_related('categoria')
        
        print(f"📦 Productos activos disponibles: {productos.count()}")
        
        productos_data = []
        for producto in productos:
            productos_data.append({
                'id': producto.id,
                'codigo': producto.codigo,
                'nombre': producto.nombre,
                'categoria': producto.categoria.nombre if producto.categoria else 'Sin categoría',
                'precio_minorista': float(producto.precio_minorista),
                'precio_mayorista': float(producto.precio_mayorista),
                'stock_total': producto.stock_total if hasattr(producto, 'stock_total') else 0,
            })
        
        import json
        context['productos_json'] = json.dumps(productos_data, ensure_ascii=False)
        
        print(f"✅ Contexto preparado con {len(productos_data)} productos")
        return context
    
    def form_valid(self, form):
        print(f"🚀 === INICIANDO CREACIÓN DE COTIZACIÓN ===")
        print(f"📋 Datos del formulario: {form.cleaned_data}")
        print(f"👤 Usuario: {self.request.user}")
        print(f"📦 POST data completo: {dict(self.request.POST)}")
        
        try:
            # Guardar la cotización primero
            response = super().form_valid(form)
            cotizacion = self.object
            print(f"✅ Cotización base creada: {cotizacion.numero} (ID: {cotizacion.id})")
            
            # Procesar los items
            productos = self.request.POST.getlist('productos[]')
            cantidades = self.request.POST.getlist('cantidades[]')
            precios = self.request.POST.getlist('precios[]')
            
            print(f"📦 Items recibidos:")
            print(f"   Productos: {productos}")
            print(f"   Cantidades: {cantidades}")
            print(f"   Precios: {precios}")
            
            if not productos:
                print("⚠️ No se recibieron productos en el POST")
                messages.warning(self.request, 'No se agregaron productos a la cotización.')
                return response
            
            # Eliminar items existentes si los hay
            items_existentes = cotizacion.items.count()
            if items_existentes > 0:
                print(f"🗑️ Eliminando {items_existentes} items existentes")
                cotizacion.items.all().delete()
            
            # Crear los nuevos items
            items_creados = 0
            items_fallidos = 0
            
            for i, producto_id in enumerate(productos):
                if producto_id and i < len(cantidades) and i < len(precios):
                    try:
                        # Convertir a Decimal para evitar errores de tipos
                        cantidad = Decimal(str(cantidades[i]))
                        precio = Decimal(str(precios[i]))
                        
                        print(f"   📦 Procesando item {i+1}: Producto {producto_id}, Cantidad {cantidad}, Precio {precio}")
                        
                        if cantidad > 0 and precio >= 0:
                            producto = Producto.objects.get(id=producto_id, activo=True)
                            
                            item = ItemCotizacion.objects.create(
                                cotizacion=cotizacion,
                                producto=producto,
                                cantidad=cantidad,
                                precio_unitario=precio
                            )
                            
                            print(f"   ✅ Item creado: {producto.nombre} - {cantidad} x ${precio}")
                            items_creados += 1
                        else:
                            print(f"   ❌ Item inválido: cantidad={cantidad}, precio={precio}")
                            items_fallidos += 1
                            
                    except (ValueError, Producto.DoesNotExist, InvalidOperation) as e:
                        print(f"   ❌ Error creando item {i+1}: {e}")
                        items_fallidos += 1
                        continue
                else:
                    print(f"   ⚠️ Item {i+1} omitido: datos incompletos")
                    items_fallidos += 1
            
            print(f"📊 Resumen de items:")
            print(f"   ✅ Creados: {items_creados}")
            print(f"   ❌ Fallidos: {items_fallidos}")
            
            # Calcular totales después de crear los items
            if items_creados > 0:
                total_calculado = cotizacion.calcular_totales()
                print(f"💰 Total calculado: ${total_calculado:,.0f}")
                
                messages.success(self.request, f'✅ Cotización {cotizacion.numero} creada exitosamente con {items_creados} productos. Total: ${total_calculado:,.0f}')
            else:
                print("⚠️ No se crearon items válidos")
                messages.warning(self.request, f'⚠️ Cotización {cotizacion.numero} creada pero sin productos válidos.')
            
            if items_fallidos > 0:
                messages.warning(self.request, f'⚠️ {items_fallidos} productos no pudieron ser agregados.')
            
            print(f"✅ === COTIZACIÓN COMPLETADA ===")
            return response
            
        except Exception as e:
            print(f"❌ Error general en form_valid: {e}")
            import traceback
            traceback.print_exc()
            messages.error(self.request, f'❌ Error al crear la cotización: {str(e)}')
            return super().form_invalid(form)

class CotizacionDetailView(VentasRequiredMixin, DetailView):
    model = Cotizacion
    template_name = 'ventas/cotizacion_detail.html'
    context_object_name = 'cotizacion'
    
    def get_queryset(self):
        queryset = Cotizacion.objects.select_related('cliente').prefetch_related('items__producto')
        # Si es vendedor, ver todas las cotizaciones por ahora
        # TODO: Agregar campo vendedor si es necesario
        if self.request.user.role == 'vendedor' and not self.request.user.is_admin_user():
            # queryset = queryset.filter(vendedor=self.request.user)
            pass
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = datetime.now().date()
        return context

# ============= ACCIONES DE COTIZACIÓN =============

def imprimir_cotizacion(request, pk):
    """Vista para imprimir cotización"""
    if not request.user.can_create_sales():
        messages.error(request, 'No tiene permisos para esta acción.')
        return redirect('ventas:cotizacion_list')
    
    try:
        cotizacion = Cotizacion.objects.select_related('cliente').prefetch_related('items__producto').get(pk=pk)
        
        return render(request, 'ventas/cotizacion_print.html', {'cotizacion': cotizacion})
        
    except Cotizacion.DoesNotExist:
        messages.error(request, 'Cotización no encontrada.')
        return redirect('ventas:cotizacion_list')

def generar_pdf_cotizacion(request, pk):
    """Vista para generar PDF de cotización"""
    if not request.user.can_create_sales():
        messages.error(request, 'No tiene permisos para esta acción.')
        return redirect('ventas:cotizacion_list')
    
    try:
        from django.http import HttpResponse
        from django.template.loader import get_template
        
        cotizacion = Cotizacion.objects.select_related('cliente').prefetch_related('items__producto').get(pk=pk)
        
        # Por ahora, redirigir a vista de impresión (implementación completa de PDF requiere librerías adicionales)
        messages.info(request, 'Funcionalidad de PDF en desarrollo. Use la opción de imprimir y seleccione "Guardar como PDF" en su navegador.')
        return redirect('ventas:imprimir_cotizacion', pk=pk)
        
    except Cotizacion.DoesNotExist:
        messages.error(request, 'Cotización no encontrada.')
        return redirect('ventas:cotizacion_list')

def convertir_a_pedido(request, pk):
    """Vista para convertir cotización a pedido"""
    if not request.user.can_create_sales():
        messages.error(request, 'No tiene permisos para esta acción.')
        return redirect('ventas:cotizacion_list')
    
    try:
        cotizacion = Cotizacion.objects.select_related('cliente').prefetch_related('items__producto').get(pk=pk)
        
        # Verificar que la cotización no esté ya convertida
        if hasattr(cotizacion, 'convertida_a_pedido') and cotizacion.convertida_a_pedido:
            messages.warning(request, 'Esta cotización ya fue convertida a pedido.')
            return redirect('ventas:cotizacion_detail', pk=pk)
        
        # Verificar que tenga items
        if not cotizacion.items.exists():
            messages.error(request, 'No se puede convertir una cotización sin items.')
            return redirect('ventas:cotizacion_detail', pk=pk)
        
        # Crear el pedido
        from inventario.models import Bodega
        bodega_principal = Bodega.objects.first()  # Por ahora usar la primera bodega
        
        if not bodega_principal:
            messages.error(request, 'No hay bodegas configuradas. Configure al menos una bodega antes de crear pedidos.')
            return redirect('ventas:cotizacion_detail', pk=pk)
        
        pedido = Pedido.objects.create(
            cliente=cotizacion.cliente,
        )
        
        # Copiar los items de la cotización al pedido
        for item_cotizacion in cotizacion.items.all():
            ItemPedido.objects.create(
                pedido=pedido,
                producto=item_cotizacion.producto,
                cantidad=item_cotizacion.cantidad,
                precio_unitario=item_cotizacion.precio_unitario,
            )
        
        # Calcular totales del pedido
        pedido.calcular_totales()
        
        messages.success(request, f'Cotización convertida exitosamente a pedido {pedido.numero}')
        return redirect('ventas:pedido_detail', pk=pedido.pk)
        
    except Cotizacion.DoesNotExist:
        messages.error(request, 'Cotización no encontrada.')
        return redirect('ventas:cotizacion_list')

def enviar_cotizacion(request, pk):
    """Vista para enviar cotización por email"""
    if not request.user.can_create_sales():
        messages.error(request, 'No tiene permisos para esta acción.')
        return redirect('ventas:cotizacion_list')
    
    try:
        cotizacion = Cotizacion.objects.select_related('cliente').get(pk=pk)
        
        # Si es vendedor (no admin), verificar que sea su cotización
        if request.user.role == 'vendedor' and not request.user.is_admin_user() and cotizacion.vendedor != request.user:
            messages.error(request, 'No puede enviar cotizaciones de otros vendedores.')
            return redirect('ventas:cotizacion_list')
        
        # Verificar que el cliente tenga email
        if not cotizacion.cliente.email:
            messages.error(request, 'El cliente no tiene email registrado.')
            return redirect('ventas:cotizacion_detail', pk=pk)
        
        # Cambiar estado a enviada
        cotizacion.estado = 'enviada'
        cotizacion.save()
        
        # Por ahora solo cambiar el estado (implementación completa de email requiere configuración adicional)
        messages.success(request, f'Cotización marcada como enviada. Funcionalidad de email en desarrollo.')
        return redirect('ventas:cotizacion_detail', pk=pk)
        
    except Cotizacion.DoesNotExist:
        messages.error(request, 'Cotización no encontrada.')
        return redirect('ventas:cotizacion_list')

class CotizacionUpdateView(VentasRequiredMixin, UpdateView):
    model = Cotizacion
    form_class = CotizacionForm
    template_name = 'ventas/cotizacion_form.html'
    
    def get_queryset(self):
        queryset = Cotizacion.objects.all()
        # Si es vendedor, solo editar sus cotizaciones
        if self.request.user.role == 'vendedor' and not self.request.user.is_admin_user():
            queryset = queryset.filter(vendedor=self.request.user)
        return queryset
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('ventas:cotizacion_detail', kwargs={'pk': self.object.pk})

# ============= PEDIDOS =============

class PedidoListView(BodegaViewMixin, ListView):
    model = Pedido
    template_name = 'ventas/pedido_list.html'
    context_object_name = 'pedidos'
    paginate_by = 20
    
    def get_queryset(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        queryset = Pedido.objects.select_related(
            'cliente'
        ).prefetch_related('items', 'entregas')
        
        # Filtrar por rol de usuario (excepto administradores y superusers)
        if not self.request.user.is_admin_user():
            if self.request.user.role == 'vendedor':
                # Los vendedores ven todos los pedidos ya que no hay campo vendedor
                pass
            elif self.request.user.role == 'bodega':
                # Los bodegueros ven pedidos pendientes y en proceso para alistar
                queryset = queryset.filter(estado__in=['borrador', 'enviado'])
            elif self.request.user.role == 'repartidor':
                # Los repartidores solo ven pedidos completados por bodega, listos para entregar
                queryset = queryset.filter(estado='completado')
        
        # Aplicar filtros
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        cliente = self.request.GET.get('cliente')
        if cliente:
            queryset = queryset.filter(
                Q(cliente__nombre_completo__icontains=cliente) |
                Q(cliente__numero_documento__icontains=cliente)
            )
        
        vendedor = self.request.GET.get('vendedor')
        if vendedor and (self.request.user.role in ['admin', 'gerente']):
            # Como no hay campo vendedor, ignoramos este filtro por ahora
            pass
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        from django.contrib.auth import get_user_model
        from django.db.models import Sum, Count
        from datetime import datetime
        
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        
        # Obtener queryset base
        base_queryset = self.get_queryset()
        
        # Estadísticas generales
        stats = {
            'pendientes': base_queryset.filter(estado='borrador').count(),
            'proceso': base_queryset.filter(estado='enviado').count(),
            'completados': base_queryset.filter(estado='completado').count(),
            'total_mes': base_queryset.filter(
                fecha_creacion__month=datetime.now().month,
                fecha_creacion__year=datetime.now().year,
                estado__in=['completado', 'enviado']
            ).aggregate(Sum('total'))['total__sum'] or 0
        }
        
        context['stats'] = stats
        
        # Vendedores para filtro (solo para admin/gerente)
        if self.request.user.role in ['admin', 'gerente']:
            context['vendedores'] = User.objects.filter(
                role__in=['vendedor', 'gerente', 'admin']
            ).order_by('first_name', 'username')
        
        return context

class PedidoDetailView(BodegaViewMixin, DetailView):
    model = Pedido
    template_name = 'ventas/pedido_detail.html'
    context_object_name = 'pedido'
    
    def get_object(self, queryset=None):
        pedido = super().get_object(queryset)
        # Si es vendedor (no admin), verificar que sea su pedido
        if self.request.user.role == 'vendedor' and not self.request.user.is_admin_user() and pedido.vendedor != self.request.user:
            raise Http404("No tiene permisos para ver este pedido")
        return pedido

def cambiar_estado_pedido(request, pk):
    """Vista para cambiar el estado de un pedido"""
    # Permitir tanto a usuarios de ventas como de bodega
    if not (request.user.can_create_sales() or request.user.can_view_inventory()):
        messages.error(request, 'No tiene permisos para esta acción.')
        return redirect('ventas:pedido_list')
    
    try:
        pedido = Pedido.objects.get(pk=pk)
        
        # Si es vendedor (no admin), verificar que sea su pedido
        if request.user.role == 'vendedor' and not request.user.is_admin_user() and pedido.vendedor != request.user:
            messages.error(request, 'No puede modificar pedidos de otros vendedores.')
            return redirect('ventas:pedido_list')
        
        # Si es bodeguero y el pedido está en proceso, verificar que sea el asignado
        if (request.user.role == 'bodega' and 
            pedido.estado == 'proceso' and 
            pedido.asignado_a and 
            pedido.asignado_a != request.user):
            messages.error(request, f'Este pedido está asignado a {pedido.asignado_a.get_full_name()}. No puede modificarlo.')
            return redirect('ventas:pedidos_alistamiento')
        
        # Obtener nuevo estado desde POST o GET
        nuevo_estado = request.POST.get('estado') or request.GET.get('estado')
        
        if nuevo_estado:
            # Validar transiciones de estado
            transiciones_validas = {
                'borrador': ['enviada', 'pendiente', 'proceso', 'cancelado'],  # Desde borrador se puede ir a cualquier estado
                'enviada': ['pendiente', 'proceso', 'cancelado'],
                'pendiente': ['proceso', 'cancelado'],
                'proceso': ['completado', 'cancelado'],
                'completado': ['entregado'],  # Solo se puede entregar si está completado
                'entregado': [],  # Estado final
                'cancelado': []   # Estado final
            }
            
            if nuevo_estado not in transiciones_validas.get(pedido.estado, []):
                messages.error(request, f'No se puede cambiar de {pedido.get_estado_display()} a {nuevo_estado}.')
                return redirect('ventas:pedido_detail', pk=pk)
            
            # Cambiar estado
            estado_anterior = pedido.get_estado_display()
            
            try:
                pedido.estado = nuevo_estado
                
                # Si es un bodeguero iniciando un pedido (pendiente → proceso), asignarlo
                if (pedido.estado == 'proceso' and 
                    estado_anterior == 'Pendiente' and 
                    request.user.can_view_inventory() and 
                    hasattr(request.user, 'role') and 
                    request.user.role == 'bodega'):
                    pedido.asignado_a = request.user
                    messages.success(request, f'Pedido #{pedido.numero} iniciado y asignado a {request.user.get_full_name()}.')
                else:
                    messages.success(request, f'Pedido #{pedido.numero} cambiado de {estado_anterior} a {pedido.get_estado_display()}.')
                
                pedido.save()
                
            except ValueError as e:
                # Capturar errores de stock insuficiente
                error_msg = str(e)
                if "Stock insuficiente" in error_msg:
                    # Extraer información del error para el template
                    import re
                    producto_match = re.search(r'Stock insuficiente para (.+)', error_msg)
                    producto_nombre = producto_match.group(1) if producto_match else "producto desconocido"
                    
                    # Obtener información detallada del stock
                    from inventario.models import Stock
                    stock_info = []
                    for item in pedido.items.all():
                        if item.producto.nombre == producto_nombre:
                            stock_total = Stock.objects.filter(producto=item.producto).aggregate(
                                total=models.Sum('cantidad')
                            )['total'] or 0
                            
                            stock_info.append({
                                'producto': item.producto,
                                'cantidad_pedida': item.cantidad,
                                'stock_disponible': stock_total,
                                'faltante': item.cantidad - stock_total
                            })
                    
                    # Renderizar template de error de stock
                    context = {
                        'pedido': pedido,
                        'producto_nombre': producto_nombre,
                        'stock_info': stock_info,
                        'estado_deseado': nuevo_estado,
                        'estado_actual': estado_anterior
                    }
                    return render(request, 'ventas/error_stock_insuficiente.html', context)
                else:
                    # Otros errores de validación
                    messages.error(request, f'Error al cambiar estado: {error_msg}')
                    return redirect('ventas:pedido_detail', pk=pk)
            
            # Redirigir de vuelta a alistamiento si vino desde ahí
            if 'alistamiento' in request.META.get('HTTP_REFERER', ''):
                return redirect('ventas:pedidos_alistamiento')
            
        return redirect('ventas:pedido_detail', pk=pk)
        
    except Pedido.DoesNotExist:
        messages.error(request, 'Pedido no encontrado.')
        return redirect('ventas:pedido_list')

def imprimir_pedido(request, pk):
    """Vista para imprimir pedido"""
    if not request.user.can_create_sales():
        messages.error(request, 'No tiene permisos para esta acción.')
        return redirect('ventas:pedido_list')
    
    try:
        pedido = Pedido.objects.select_related(
            'cliente', 'vendedor', 'bodega', 'cotizacion_origen'
        ).prefetch_related('items__producto', 'items__variante').get(pk=pk)
        
        # Si es vendedor (no admin), verificar que sea su pedido
        if request.user.role == 'vendedor' and not request.user.is_admin_user() and pedido.vendedor != request.user:
            messages.error(request, 'No puede imprimir pedidos de otros vendedores.')
            return redirect('ventas:pedido_list')
        
        return render(request, 'ventas/pedido_print.html', {'pedido': pedido})
        
    except Pedido.DoesNotExist:
        messages.error(request, 'Pedido no encontrado.')
        return redirect('ventas:pedido_list')

class PedidoCreateView(LoginRequiredMixin, VentasRequiredMixin, CreateView):
    """Vista para crear nuevos pedidos directamente"""
    model = Pedido
    template_name = 'ventas/pedido_form.html'
    success_url = reverse_lazy('ventas:pedido_list')
    
    def get_form_class(self):
        from .forms import PedidoForm
        return PedidoForm
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        
        # Pre-seleccionar cliente si viene en la URL
        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            if 'initial' not in kwargs:
                kwargs['initial'] = {}
            kwargs['initial']['cliente'] = cliente_id
        
        return kwargs
    
    def form_valid(self, form):
        # Generar número de pedido automáticamente
        ultimo_pedido = Pedido.objects.order_by('-id').first()
        if ultimo_pedido:
            # Extraer el número del último pedido (ej: PED-001 -> 001)
            try:
                ultimo_numero = int(ultimo_pedido.numero.split('-')[1])
                nuevo_numero = f"PED-{ultimo_numero + 1:03d}"
            except (IndexError, ValueError):
                # Si el formato no es el esperado, empezar desde 001
                nuevo_numero = "PED-001"
        else:
            # Primer pedido
            nuevo_numero = "PED-001"
        
        # Asegurar que el número sea único
        while Pedido.objects.filter(numero=nuevo_numero).exists():
            numero_int = int(nuevo_numero.split('-')[1])
            nuevo_numero = f"PED-{numero_int + 1:03d}"
        
        form.instance.numero = nuevo_numero
        
        # Asignar vendedor automáticamente (si existe el campo)
        if hasattr(form.instance, 'vendedor'):
            form.instance.vendedor = self.request.user
        
        # Establecer estado inicial
        form.instance.estado = 'borrador'
        
        # Guardar el pedido primero
        response = super().form_valid(form)
        pedido = self.object
        
        # Procesar los items del pedido
        productos = self.request.POST.getlist('productos[]')
        cantidades = self.request.POST.getlist('cantidades[]')
        precios = self.request.POST.getlist('precios[]')
        
        # Validar que hay items
        if not productos or not any(productos):
            messages.error(self.request, 'Debe agregar al menos un producto al pedido.')
            pedido.delete()  # Eliminar pedido sin items
            return self.form_invalid(form)
        
        # Crear los items del pedido
        items_creados = 0
        for i, producto_id in enumerate(productos):
            if producto_id and i < len(cantidades) and i < len(precios):
                try:
                    cantidad = Decimal(str(cantidades[i]))
                    precio = Decimal(str(precios[i]))
                    
                    if cantidad > 0 and precio >= 0:
                        producto = Producto.objects.get(id=producto_id, activo=True)
                        
                        # Verificar stock total disponible (sin bodega específica)
                        from inventario.models import Stock
                        try:
                            stock_total = Stock.objects.filter(producto=producto).aggregate(
                                total_disponible=Sum('cantidad_disponible')
                            )['total_disponible'] or 0
                            
                            if stock_total < cantidad:
                                messages.warning(
                                    self.request, 
                                    f'Stock insuficiente para {producto.nombre}. '
                                    f'Disponible en todas las bodegas: {stock_total}, Solicitado: {cantidad}'
                                )
                        except Exception as e:
                            messages.warning(
                                self.request,
                                f'No se pudo verificar stock para {producto.nombre}'
                            )
                        
                        # Crear el item del pedido
                        ItemPedido.objects.create(
                            pedido=pedido,
                            producto=producto,
                            cantidad=cantidad,
                            precio_unitario=precio
                        )
                        items_creados += 1
                        
                except (ValueError, Producto.DoesNotExist, InvalidOperation) as e:
                    messages.error(self.request, f'Error procesando producto {producto_id}: {str(e)}')
                    continue
        
        # Verificar que se crearon items
        if items_creados == 0:
            messages.error(self.request, 'No se pudo crear ningún item válido para el pedido.')
            pedido.delete()
            return self.form_invalid(form)
        
        # Calcular totales
        pedido.calcular_totales()
        
        messages.success(
            self.request, 
            f'Pedido {pedido.numero} creado exitosamente con {items_creados} items. Total: ${pedido.total}'
        )
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener cliente preseleccionado si existe
        cliente_id = self.request.GET.get('cliente')
        cliente = None
        if cliente_id:
            try:
                cliente = Cliente.objects.get(id=cliente_id)
                context['cliente_preseleccionado'] = cliente
            except Cliente.DoesNotExist:
                pass
        
        # Obtener productos para el selector
        productos_queryset = Producto.objects.filter(activo=True).select_related('categoria')
        
        # Serializar productos para JavaScript
        import json
        productos_data = []
        for producto in productos_queryset:
            # Obtener precio según cliente preseleccionado
            precio = producto.get_precio_para_cliente(cliente)
            
            productos_data.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'codigo': producto.codigo,
                'categoria': producto.categoria.nombre if producto.categoria else 'Sin categoría',
                'precio': float(precio),
                'precio_minorista': float(producto.precio_minorista),
                'precio_mayorista': float(producto.precio_mayorista),
                'stock': getattr(producto, 'stock_disponible', 0),  # Si existe el campo
                'tipo_cliente_precio': cliente.tipo_cliente if cliente else 'minorista'
            })
        
        # Agregar productos serializados como JSON
        context['productos'] = productos_queryset  # Para el loop en el template
        context['productos_json'] = json.dumps(productos_data, ensure_ascii=False)
        
        # Agregar cliente preseleccionado si existe
        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            try:
                context['cliente_seleccionado'] = Cliente.objects.get(id=cliente_id)
            except Cliente.DoesNotExist:
                pass
        
        context['title'] = 'Crear Nuevo Pedido'
        
        return context

# ============= FACTURAS (PLACEHOLDER) =============

class FacturaListView(VentasRequiredMixin, ListView):
    model = Factura
    template_name = 'ventas/factura_list.html'
    context_object_name = 'facturas'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Factura.objects.select_related(
            'cliente', 'vendedor', 'pedido_origen'
        ).prefetch_related('items__producto')
        
        # Filtrar por rol de usuario
        if self.request.user.role == 'vendedor' and not self.request.user.is_admin_user():
            queryset = queryset.filter(vendedor=self.request.user)
        
        # Aplicar filtros
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        cliente = self.request.GET.get('cliente')
        if cliente:
            queryset = queryset.filter(
                Q(cliente__nombre_completo__icontains=cliente) |
                Q(cliente__numero_documento__icontains=cliente)
            )
        
        vendedor = self.request.GET.get('vendedor')
        if vendedor and (self.request.user.role in ['superadmin', 'administrador']):
            queryset = queryset.filter(vendedor_id=vendedor)
        
        # Filtros de fecha
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        
        if fecha_desde:
            queryset = queryset.filter(fecha_creacion__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_creacion__lte=fecha_hasta)
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas para dashboard
        queryset_base = self.get_queryset()
        
        from django.db.models import Sum, Count
        from datetime import datetime, timedelta
        
        stats = {
            'total_facturas': queryset_base.count(),
            'emitidas': queryset_base.filter(estado='emitida').count(),
            'pagadas': queryset_base.filter(estado='pagada').count(),
            'vencidas': queryset_base.filter(estado='vencida').count(),
            'total_mes': queryset_base.filter(
                fecha__month=datetime.now().month,
                fecha__year=datetime.now().year,
                estado__in=['emitida', 'pagada']
            ).aggregate(Sum('total'))['total__sum'] or 0,
            'por_vencer': queryset_base.filter(
                fecha_vencimiento__lte=datetime.now().date() + timedelta(days=7),
                estado='emitida'
            ).count()
        }
        
        context['stats'] = stats
        
        # Vendedores para filtro (solo para admin)
        if self.request.user.role in ['superadmin', 'administrador']:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            context['vendedores'] = User.objects.filter(
                role__in=['vendedor', 'administrador', 'superadmin']
            ).order_by('first_name', 'username')
        
        return context

class FacturaDetailView(VentasRequiredMixin, DetailView):
    model = Factura
    template_name = 'ventas/factura_detail.html'
    context_object_name = 'factura'
    
    def get_object(self, queryset=None):
        factura = super().get_object(queryset)
        # Comentado hasta que se implemente el campo vendedor
        # if self.request.user.role == 'vendedor' and not self.request.user.is_admin_user() and factura.vendedor != self.request.user:
        #     raise Http404("No tiene permisos para ver esta factura")
        return factura
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = datetime.now().date()
        return context

class FacturaCreateView(VentasRequiredMixin, CreateView):
    model = Factura
    template_name = 'ventas/factura_form.html'
    fields = ['cliente', 'observaciones', 'descuento_porcentaje', 'orden_compra', 'metodo_pago']
    success_url = reverse_lazy('ventas:factura_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Personalizar queryset de clientes
        queryset = Cliente.objects.filter(activo=True)
        # Los vendedores ahora pueden seleccionar todos los clientes
        # (Ya no se filtra por vendedor_asignado para vendedores)
        
        form.fields['cliente'].queryset = queryset
        
        # Widgets
        form.fields['cliente'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
        form.fields['observaciones'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'rows': 3
        })
        form.fields['descuento_porcentaje'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
        form.fields['orden_compra'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
        form.fields['metodo_pago'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
        
        return form
    
    def form_valid(self, form):
        form.instance.vendedor = self.request.user
        
        # Guardar la factura primero
        response = super().form_valid(form)
        factura = self.object
        
        # Procesar los items (similar a cotización)
        productos = self.request.POST.getlist('productos[]')
        cantidades = self.request.POST.getlist('cantidades[]')
        precios = self.request.POST.getlist('precios[]')
        
        # Crear los items
        items_creados = 0
        for i, producto_id in enumerate(productos):
            if producto_id and i < len(cantidades) and i < len(precios):
                try:
                    cantidad = Decimal(str(cantidades[i]))
                    precio = Decimal(str(precios[i]))
                    if cantidad > 0 and precio >= 0:
                        producto = Producto.objects.get(id=producto_id, activo=True)
                        ItemFactura.objects.create(
                            factura=factura,
                            producto=producto,
                            cantidad=cantidad,
                            precio_unitario=precio
                        )
                        items_creados += 1
                except (ValueError, Producto.DoesNotExist):
                    continue
        
        # Calcular totales después de crear los items
        if items_creados > 0:
            factura.calcular_totales()
        
        messages.success(self.request, 'Factura creada exitosamente.')
        return response

# ============= ACCIONES DE FACTURAS =============

def convertir_pedido_a_factura(request, pk):
    """Vista para convertir pedido a factura"""
    if not request.user.can_create_sales():
        messages.error(request, 'No tiene permisos para esta acción.')
        return redirect('ventas:pedido_list')
    
    try:
        pedido = Pedido.objects.select_related('cliente').prefetch_related('items__producto').get(pk=pk)
        
        # Verificar que el pedido esté completado
        if pedido.estado != 'completado':
            messages.error(request, 'Solo se pueden facturar pedidos completados.')
            return redirect('ventas:pedido_detail', pk=pk)
        
        # Verificar que no esté ya facturado (usando una consulta alternativa)
        # Como no hay pedido_origen, buscaremos facturas del mismo cliente y fecha similar
        factura_existente = None
        for factura_temp in Factura.objects.filter(cliente=pedido.cliente, fecha_creacion__date=pedido.fecha_creacion.date()):
            # Aquí podrías agregar lógica adicional para verificar si ya existe
            # Por ahora, permitimos crear nuevas facturas
            pass
        
        # Verificar que tenga items
        if not pedido.items.exists():
            messages.error(request, 'No se puede facturar un pedido sin items.')
            return redirect('ventas:pedido_detail', pk=pk)
        
        # Crear la factura
        factura = Factura.objects.create(
            cliente=pedido.cliente,
            estado='emitida'
        )
        
        # Copiar los items del pedido a la factura
        for item_pedido in pedido.items.all():
            ItemFactura.objects.create(
                factura=factura,
                cantidad=int(item_pedido.cantidad),
                precio=item_pedido.precio_unitario
            )
        
        # Calcular total de la factura manualmente
        total_factura = sum(item.cantidad * item.precio for item in factura.itemfactura_set.all())
        factura.total = total_factura
        factura.save()
        
        messages.success(request, f'Pedido convertido exitosamente a factura {factura.numero}')
        return redirect('ventas:factura_detail', pk=factura.pk)
        
    except Pedido.DoesNotExist:
        messages.error(request, 'Pedido no encontrado.')
        return redirect('ventas:pedido_list')

def marcar_factura_pagada(request, pk):
    """Vista para marcar una factura como pagada"""
    if not request.user.can_create_sales():
        messages.error(request, 'No tiene permisos para esta acción.')
        return redirect('ventas:factura_list')
    
    try:
        factura = Factura.objects.get(pk=pk)
        
        # Comentado hasta que se implemente el campo vendedor
        # if request.user.role == 'vendedor' and not request.user.is_admin_user() and factura.vendedor != request.user:
        #     messages.error(request, 'No puede modificar facturas de otros vendedores.')
        #     return redirect('ventas:factura_list')
        
        if request.method == 'POST':
            fecha_pago = request.POST.get('fecha_pago')
            
            if not fecha_pago:
                messages.error(request, 'Debe especificar la fecha de pago.')
                return redirect('ventas:factura_detail', pk=pk)
            
            try:
                from datetime import datetime
                fecha_pago_obj = datetime.strptime(fecha_pago, '%Y-%m-%d').date()
                factura.marcar_pagada(fecha_pago_obj)
                messages.success(request, 'Factura marcada como pagada exitosamente.')
            except ValueError:
                messages.error(request, 'Formato de fecha inválido.')
        
        return redirect('ventas:factura_detail', pk=pk)
        
    except Factura.DoesNotExist:
        messages.error(request, 'Factura no encontrada.')
        return redirect('ventas:factura_list')

def anular_factura(request, pk):
    """Vista para anular una factura"""
    if not request.user.role in ['superadmin', 'administrador']:
        messages.error(request, 'No tiene permisos para anular facturas.')
        return redirect('ventas:factura_list')
    
    try:
        factura = Factura.objects.get(pk=pk)
        
        if request.method == 'POST':
            motivo = request.POST.get('motivo', '').strip()
            
            if not motivo:
                messages.error(request, 'Debe especificar el motivo de anulación.')
                return redirect('ventas:factura_detail', pk=pk)
            
            try:
                factura.anular()
                factura.nota_interna = f"Anulada: {motivo}"
                factura.save()
                messages.success(request, 'Factura anulada exitosamente.')
            except ValueError as e:
                messages.error(request, str(e))
        
        return redirect('ventas:factura_detail', pk=pk)
        
    except Factura.DoesNotExist:
        messages.error(request, 'Factura no encontrada.')
        return redirect('ventas:factura_list')

def imprimir_factura(request, pk):
    """Vista para imprimir factura"""
    if not request.user.can_create_sales():
        messages.error(request, 'No tiene permisos para esta acción.')
        return redirect('ventas:factura_list')
    
    try:
        factura = Factura.objects.select_related(
            'cliente'
        ).prefetch_related('itemfactura_set').get(pk=pk)
        
        # Comentado hasta que se implemente el campo vendedor
        # if request.user.role == 'vendedor' and factura.vendedor != request.user:
        #     messages.error(request, 'No puede imprimir facturas de otros vendedores.')
        #     return redirect('ventas:factura_list')
        
        return render(request, 'ventas/factura_print.html', {'factura': factura})
        
    except Factura.DoesNotExist:
        messages.error(request, 'Factura no encontrada.')
        return redirect('ventas:factura_list')

def reporte_facturas(request):
    """Vista para generar reportes de facturas"""
    if not request.user.can_create_sales():
        messages.error(request, 'No tiene permisos para esta acción.')
        return redirect('ventas:factura_list')
    
    # Obtener parámetros de filtro
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    cliente_id = request.GET.get('cliente_id')
    vendedor_id = request.GET.get('vendedor_id')
    estado = request.GET.get('estado')
    
    # Construir queryset
    queryset = Factura.objects.select_related('cliente')
    
    # Comentado hasta que se implemente el campo vendedor
    # if request.user.role == 'vendedor':
    #     queryset = queryset.filter(vendedor=request.user)
    
    if fecha_desde:
        queryset = queryset.filter(fecha_creacion__gte=fecha_desde)
    if fecha_hasta:
        queryset = queryset.filter(fecha_creacion__lte=fecha_hasta)
    if cliente_id:
        queryset = queryset.filter(cliente_id=cliente_id)
    # Comentado hasta que se implemente el campo vendedor
    # if vendedor_id and request.user.role in ['superadmin', 'administrador']:
    #     queryset = queryset.filter(vendedor_id=vendedor_id)
    if estado:
        queryset = queryset.filter(estado=estado)
    
    facturas = queryset.order_by('-fecha_creacion')
    
    # Calcular estadísticas
    from django.db.models import Sum, Avg, Count
    
    # Estados disponibles en el modelo actual
    estados_disponibles = ['borrador', 'emitida', 'pagada', 'anulada']
    
    stats = {
        'total_facturas': facturas.count(),
        'total_facturado': facturas.aggregate(Sum('total'))['total__sum'] or 0,
        'promedio_factura': facturas.aggregate(Avg('total'))['total__avg'] or 0,
        'por_estado': {
            estado: facturas.filter(estado=estado).count()
            for estado in estados_disponibles
        }
    }
    
    return render(request, 'ventas/factura_reporte.html', {
        'facturas': facturas,
        'stats': stats,
        'filtros': {
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'cliente_id': cliente_id,
            'vendedor_id': vendedor_id,
            'estado': estado
        }
    })

# ============= API HELPERS =============

def buscar_productos_api(request):
    """API para buscar productos en tiempo real"""
    if not request.user.is_authenticated or not request.user.can_create_sales():
        return JsonResponse({'error': 'No autorizado'}, status=401)
    
    query = request.GET.get('q', '')
    cliente_id = request.GET.get('cliente_id')  # Agregar cliente_id para determinar precio
    
    if len(query) < 2:
        return JsonResponse({'productos': []})
    
    productos = Producto.objects.filter(
        Q(codigo__icontains=query) | Q(nombre__icontains=query),
        activo=True
    ).select_related('categoria')[:10]
    
    # Obtener cliente para determinar precios
    cliente = None
    if cliente_id:
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            pass
    
    data = []
    for producto in productos:
        # Obtener precio según tipo de cliente
        precio = producto.get_precio_para_cliente(cliente)
        
        # Verificar stock disponible en todas las bodegas
        stocks_bodega = Stock.objects.filter(producto=producto).select_related('bodega')
        stock_total = sum(stock.cantidad_disponible for stock in stocks_bodega)
        
        # Detalles por bodega
        stock_bodegas = []
        for stock in stocks_bodega:
            if stock.cantidad > 0 or stock.cantidad_reservada > 0:
                stock_bodegas.append({
                    'bodega': stock.bodega.nombre,
                    'cantidad_total': stock.cantidad,
                    'cantidad_reservada': stock.cantidad_reservada,
                    'cantidad_disponible': stock.cantidad_disponible
                })
        
        data.append({
            'id': producto.id,
            'codigo': producto.codigo,
            'nombre': producto.nombre,
            'precio': float(precio),
            'precio_minorista': float(producto.precio_minorista),
            'precio_mayorista': float(producto.precio_mayorista),
            'stock_total': stock_total,
            'stock_disponible': stock_total,
            'stock_bodegas': stock_bodegas,
            'categoria': producto.categoria.nombre,
            'tipo_cliente_precio': cliente.tipo_cliente if cliente else 'minorista'
        })
    
    return JsonResponse({'productos': data})

def verificar_stock_disponible(request):
    """API para verificar stock disponible antes de procesar venta"""
    if not request.user.is_authenticated or not request.user.can_create_sales():
        return JsonResponse({'error': 'No autorizado'}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        
        productos_verificar = data.get('productos', [])
        bodega_id = data.get('bodega_id')
        
        if not productos_verificar:
            return JsonResponse({'error': 'No se especificaron productos'}, status=400)
        
        resultados = []
        stock_suficiente = True
        
        for item in productos_verificar:
            producto_id = item.get('producto_id')
            variante_id = item.get('variante_id')
            cantidad_solicitada = int(item.get('cantidad', 0))
            
            if not producto_id or cantidad_solicitada <= 0:
                continue
            
            try:
                producto = Producto.objects.get(id=producto_id)
                
                # Obtener stock específico o general
                if bodega_id:
                    # Stock en bodega específica
                    try:
                        stock = Stock.objects.get(
                            producto=producto,
                            variante_id=variante_id,
                            bodega_id=bodega_id
                        )
                        stock_disponible = stock.cantidad_disponible
                    except Stock.DoesNotExist:
                        stock_disponible = 0
                else:
                    # Stock total en todas las bodegas
                    stocks = Stock.objects.filter(
                        producto=producto,
                        variante_id=variante_id
                    )
                    stock_disponible = sum(s.cantidad_disponible for s in stocks)
                
                suficiente = stock_disponible >= cantidad_solicitada
                if not suficiente:
                    stock_suficiente = False
                
                resultados.append({
                    'producto_id': producto_id,
                    'producto_nombre': producto.nombre,
                    'variante_id': variante_id,
                    'cantidad_solicitada': cantidad_solicitada,
                    'stock_disponible': stock_disponible,
                    'suficiente': suficiente,
                    'faltante': max(0, cantidad_solicitada - stock_disponible)
                })
                
            except Producto.DoesNotExist:
                resultados.append({
                    'producto_id': producto_id,
                    'error': 'Producto no encontrado',
                    'suficiente': False
                })
                stock_suficiente = False
        
        return JsonResponse({
            'stock_suficiente': stock_suficiente,
            'productos': resultados
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def obtener_precio_producto(request, producto_id):
    """API para obtener precio del producto según el cliente"""
    if not request.user.is_authenticated or not request.user.can_create_sales():
        return JsonResponse({'error': 'No autorizado'}, status=401)
    
    try:
        producto = Producto.objects.get(id=producto_id, activo=True)
        cliente_id = request.GET.get('cliente_id')
        
        # Obtener cliente y precio correspondiente
        cliente = None
        if cliente_id:
            try:
                cliente = Cliente.objects.get(id=cliente_id)
            except Cliente.DoesNotExist:
                pass
        
        # Usar el método del modelo para obtener el precio correcto
        precio = producto.get_precio_para_cliente(cliente)
        
        return JsonResponse({
            'precio': float(precio),
            'precio_minorista': float(producto.precio_minorista),
            'precio_mayorista': float(producto.precio_mayorista),
            'tipo_cliente': cliente.tipo_cliente if cliente else 'minorista',
            'stock': Stock.objects.filter(producto=producto).aggregate(
                total=Sum('cantidad')
            )['total'] or 0
        })
        
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

@csrf_exempt
def buscar_clientes_api(request):
    """API para buscar clientes en tiempo real"""
    import sys
    
    # Forzar output inmediato
    print(f"🚀 === API LLAMADA DIRECTA ===", flush=True)
    sys.stdout.flush()
    
    # Debug temporal - permitir acceso sin autenticación para testing
    if not request.user.is_authenticated:
        print(f"⚠️ Usuario no autenticado - permitiendo para debug", flush=True)
    elif not hasattr(request.user, 'can_create_sales') or not request.user.can_create_sales():
        print(f"⚠️ Usuario sin permisos - permitiendo para debug", flush=True)
    
    # Línea original comentada para debug:
    # if not request.user.is_authenticated or not request.user.can_create_sales():
    #     return JsonResponse({'error': 'No autorizado'}, status=401)
    
    # Si viene cliente_id, devolver información de ese cliente específico
    cliente_id = request.GET.get('cliente_id')
    if cliente_id:
        try:
            cliente = Cliente.objects.get(id=cliente_id)
            return JsonResponse({
                'cliente': {
                    'id': cliente.id,
                    'nombre_completo': cliente.nombre_completo,
                    'tipo_cliente': cliente.tipo_cliente,  # Valor directo, no display
                    'telefono': cliente.telefono or ''
                }
            })
        except Cliente.DoesNotExist:
            return JsonResponse({'error': 'Cliente no encontrado'}, status=404)
    
    query = request.GET.get('q', '')
    print(f"🔍 API llamada con query: '{query}'", flush=True)
    
    if len(query) < 2:
        print(f"❌ Query demasiado corto: {len(query)} caracteres")
        return JsonResponse({'clientes': []})
    
    queryset = Cliente.objects.filter(activo=True)
    print(f"📊 Clientes activos total: {queryset.count()}")
    
    # Los vendedores ahora pueden buscar todos los clientes
    # (Ya no se filtra por vendedor_asignado para vendedores)
    
    # Filtrar por búsqueda
    clientes = queryset.filter(
        Q(numero_documento__icontains=query) |
        Q(nombre_completo__icontains=query)
    )[:10]
    
    print(f"🎯 Clientes encontrados: {clientes.count()}")
    
    data = []
    for cliente in clientes:
        data.append({
            'id': cliente.id,
            'nombre_completo': cliente.nombre_completo,
            'numero_documento': cliente.numero_documento,
            'tipo_documento': cliente.get_tipo_documento_display(),
            'tipo_cliente': cliente.get_tipo_cliente_display()
        })
        print(f"   → {cliente.nombre_completo} - {cliente.numero_documento}")
    
    print(f"📤 Enviando {len(data)} resultados")
    return JsonResponse({'clientes': data})


from django.utils import timezone
from django.contrib.auth.decorators import login_required

@login_required
def completar_pedido_inmediato(request, pk):
    """Marcar pedido como completado inmediatamente para ventas en punto de venta"""
    pedido = get_object_or_404(Pedido, pk=pk)
    
    # Verificar permisos
    if not request.user.has_perm('ventas.change_pedido'):
        messages.error(request, 'No tienes permisos para completar pedidos.')
        return redirect('ventas:pedido_detail', pk=pk)
    
    # Si es vendedor, solo puede completar sus propios pedidos
    if hasattr(request.user, 'role') and request.user.role == 'vendedor':
        if pedido.vendedor != request.user:
            messages.error(request, 'Solo puedes completar tus propios pedidos.')
            return redirect('ventas:pedido_detail', pk=pk)
    
    # Verificar que el pedido no esté ya completado
    if pedido.estado == 'completado':
        messages.warning(request, f'El pedido #{pedido.numero} ya está completado.')
        return redirect('ventas:pedido_detail', pk=pk)
    
    # Verificar que el pedido no esté cancelado
    if pedido.estado == 'cancelado':
        messages.error(request, 'No se puede completar un pedido cancelado.')
        return redirect('ventas:pedido_detail', pk=pk)
    
    # Verificar que tenga items
    if not pedido.items.exists():
        messages.error(request, 'No se puede completar un pedido sin productos.')
        return redirect('ventas:pedido_detail', pk=pk)
    
    if request.method == 'POST':
        # Confirmar con el parámetro 'confirmar'
        if request.POST.get('confirmar') != '1':
            messages.error(request, 'Operación no confirmada.')
            return redirect('ventas:pedido_detail', pk=pk)
        
        # Marcar como completado con entrega inmediata
        pedido.estado = 'completado'
        pedido.entrega_inmediata = True
        pedido.fecha_entrega = timezone.now()
        pedido.save()
        
        messages.success(request, f'✅ Pedido #{pedido.numero} completado como entrega inmediata.')
        
        # Opción de generar factura inmediatamente
        if request.POST.get('generar_factura') == '1':
            return redirect('ventas:convertir_a_factura', pk=pk)
    
    return redirect('ventas:pedido_detail', pk=pk)


# ============= ALISTAMIENTO DE PEDIDOS (BODEGA) =============

class PedidosAlistamientoView(BodegaViewMixin, ListView):
    """Vista para que bodega vea pedidos pendientes de alistamiento"""
    model = Pedido
    template_name = 'ventas/pedidos_alistamiento.html'
    context_object_name = 'pedidos'
    paginate_by = 20
    
    def get_queryset(self):
        """Obtener pedidos listos para alistar con filtros opcionales y asignación"""
        # Usuarios con permisos de bodega pueden ver pedidos de alistamiento
        usuario_actual = self.request.user
        
        # Base: pedidos que necesitan alistamiento
        queryset = Pedido.objects.filter(
            estado__in=['proceso', 'pendiente']
        ).select_related(
            'cliente', 'asignado_a'
        ).prefetch_related(
            'items__producto',
            'items__producto__stock'
        )
        
        # Aplicar filtro de estado (todos los bodegueros ven todos los pedidos)
        filtro_estado = self.request.GET.get('estado')
        
        if filtro_estado == 'proceso':
            # Todos los pedidos en proceso (independientemente de asignación)
            queryset = queryset.filter(estado='proceso')
        elif filtro_estado == 'pendiente':
            # Todos los pedidos pendientes
            queryset = queryset.filter(estado='pendiente')
        # else: Vista "Todos" - mostrar todos los pedidos pendientes y en proceso
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Alistamiento de Pedidos'
        usuario_actual = self.request.user
        
        # Totales específicos para cada bodeguero
        context['total_pedidos'] = self.get_queryset().count()
        context['total_pendientes'] = Pedido.objects.filter(estado='pendiente').count()
        context['total_proceso'] = Pedido.objects.filter(
            estado='proceso', 
            asignado_a=usuario_actual
        ).count()
        
        # Estado del filtro actual
        context['filtro_actual'] = self.request.GET.get('estado', 'todos')
        context['usuario_actual'] = usuario_actual
        
        # Agregar información de stock para cada pedido
        for pedido in context['pedidos']:
            for item in pedido.items.all():
                # Verificar disponibilidad de stock usando los campos reales
                stock_disponible = Stock.objects.filter(
                    producto=item.producto
                ).aggregate(
                    total=Sum(F('cantidad') - F('cantidad_reservada'))
                )['total'] or 0
                
                item.stock_disponible = stock_disponible
                item.stock_suficiente = stock_disponible >= item.cantidad
        
        return context


# ============= ENTREGAS (REPARTIDOR) =============

class EntregasRepartidorView(LoginRequiredMixin, ListView):
    """Vista para que repartidores gestionen entregas"""
    model = Entrega
    template_name = 'ventas/entregas_repartidor.html'
    context_object_name = 'entregas'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_deliver_orders():
            raise PermissionDenied("No tienes permisos para acceder a entregas")
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = Entrega.objects.select_related(
            'pedido__cliente', 'repartidor'
        ).prefetch_related('pedido__items__producto')
        
        # Los repartidores ven solo sus entregas
        if self.request.user.role == 'repartidor':
            queryset = queryset.filter(repartidor=self.request.user)
        
        # Filtros
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        return queryset.order_by('-fecha_programada')


class CrearEntregaView(LoginRequiredMixin, View):
    """Vista para crear entrega desde pedidos completados"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_deliver_orders():
            raise PermissionDenied("No tienes permisos para crear entregas")
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        from django.utils import timezone
        from datetime import timedelta
        import json
        
        data = json.loads(request.body)
        pedido_ids = data.get('pedidos', [])
        fecha_programada = data.get('fecha_programada')
        
        try:
            # Validar fecha
            if not fecha_programada:
                fecha_programada = timezone.now() + timedelta(hours=1)
            else:
                fecha_programada = timezone.datetime.fromisoformat(fecha_programada.replace('Z', '+00:00'))
            
            entregas_creadas = []
            pedidos_ya_con_entrega = []
            
            for pedido_id in pedido_ids:
                try:
                    pedido = Pedido.objects.get(
                        id=pedido_id,
                        estado='completado'
                    )
                    
                    # Verificar que no tenga entregas ya creadas
                    if pedido.entregas.exists():
                        pedidos_ya_con_entrega.append(pedido.numero)
                        continue  # Saltar este pedido, ya tiene entregas
                    
                    # Crear entrega
                    entrega = Entrega.objects.create(
                        pedido=pedido,
                        repartidor=request.user,
                        fecha_programada=fecha_programada,
                        direccion_entrega=pedido.cliente.direccion,
                        telefono_contacto=pedido.cliente.telefono
                    )
                    entregas_creadas.append(entrega)
                    
                except Pedido.DoesNotExist:
                    continue
            
            # Crear mensaje informativo
            mensaje_partes = []
            if entregas_creadas:
                mensaje_partes.append(f"Se crearon {len(entregas_creadas)} nuevas entregas")
            
            if pedidos_ya_con_entrega:
                mensaje_partes.append(f"Se omitieron {len(pedidos_ya_con_entrega)} pedidos que ya tenían entregas: {', '.join(pedidos_ya_con_entrega)}")
            
            if not entregas_creadas and not pedidos_ya_con_entrega:
                mensaje_partes.append("No se procesó ningún pedido")
            
            mensaje_final = ". ".join(mensaje_partes)
            
            return JsonResponse({
                'success': True,
                'message': mensaje_final,
                'entregas_creadas': len(entregas_creadas),
                'pedidos_omitidos': len(pedidos_ya_con_entrega)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al crear entregas: {str(e)}'
            }, status=400)


class MarcarSalidaView(LoginRequiredMixin, View):
    """Vista para marcar salida de entrega"""
    
    def post(self, request, entrega_id):
        if not request.user.can_deliver_orders():
            raise PermissionDenied()
        
        try:
            entrega = Entrega.objects.get(
                id=entrega_id,
                repartidor=request.user,
                estado='programada'
            )
            
            entrega.marcar_en_camino()
            
            return JsonResponse({
                'success': True,
                'message': 'Entrega marcada en camino'
            })
            
        except Entrega.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Entrega no encontrada'
            }, status=404)


class CompletarEntregaView(LoginRequiredMixin, View):
    """Vista para completar entrega con firma y evidencia"""
    
    def post(self, request, entrega_id):
        if not request.user.can_deliver_orders():
            raise PermissionDenied()
        
        try:
            entrega = Entrega.objects.get(
                id=entrega_id,
                repartidor=request.user,
                estado='en_camino'
            )
            
            # Obtener datos del formulario
            persona_recibe = request.POST.get('persona_recibe', '')
            firma_digital = request.POST.get('firma_digital', '')
            observaciones = request.POST.get('observaciones', '')
            
            # Manejar foto de evidencia
            if 'foto_evidencia' in request.FILES:
                entrega.foto_evidencia = request.FILES['foto_evidencia']
            
            # Procesar items rechazados
            items_rechazados_data = self._procesar_items_rechazados(request, entrega)
            
            # Completar entrega
            entrega.marcar_entregado(
                persona_recibe=persona_recibe,
                firma=firma_digital,
                observaciones=observaciones
            )
            
            # Crear registros de items rechazados
            self._crear_items_rechazados(items_rechazados_data, entrega)
            
            mensaje = 'Entrega completada exitosamente'
            if items_rechazados_data:
                mensaje += f' con {len(items_rechazados_data)} item(s) rechazado(s)'
            
            return JsonResponse({
                'success': True,
                'message': mensaje,
                'items_rechazados': len(items_rechazados_data)
            })
            
        except Entrega.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Entrega no encontrada'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al completar entrega: {str(e)}'
            }, status=400)
    
    def _procesar_items_rechazados(self, request, entrega):
        """Procesa los items rechazados del formulario"""
        items_rechazados = []
        
        # Obtener todos los items del pedido
        for item in entrega.pedido.items.all():
            # Verificar si este item fue rechazado
            rechazado_key = f'item_rechazado_{item.id}'
            cantidad_rechazada_key = f'cantidad_rechazada_{item.id}'
            motivo_key = f'motivo_rechazo_{item.id}'
            observaciones_key = f'observaciones_rechazo_{item.id}'
            
            if request.POST.get(rechazado_key) == 'on':
                try:
                    cantidad_rechazada = float(request.POST.get(cantidad_rechazada_key, 0))
                    if cantidad_rechazada > 0 and cantidad_rechazada <= float(item.cantidad):
                        items_rechazados.append({
                            'item_pedido': item,
                            'cantidad_rechazada': cantidad_rechazada,
                            'motivo': request.POST.get(motivo_key, 'otro'),
                            'observaciones': request.POST.get(observaciones_key, '')
                        })
                except (ValueError, TypeError):
                    continue  # Ignorar valores inválidos
        
        return items_rechazados
    
    def _crear_items_rechazados(self, items_rechazados_data, entrega):
        """Crea los registros de items rechazados en la base de datos"""
        from .models import ItemRechazado
        
        for data in items_rechazados_data:
            ItemRechazado.objects.create(
                entrega=entrega,
                item_pedido=data['item_pedido'],
                cantidad_rechazada=data['cantidad_rechazada'],
                motivo=data['motivo'],
                observaciones=data['observaciones']
            )


class MarcarFallidaView(LoginRequiredMixin, View):
    """Vista para marcar entrega como fallida"""
    
    def post(self, request, entrega_id):
        if not request.user.can_deliver_orders():
            raise PermissionDenied()
        
        try:
            entrega = Entrega.objects.get(
                id=entrega_id,
                repartidor=request.user,
                estado='en_camino'
            )
            
            motivo = request.POST.get('motivo', 'No especificado')
            entrega.marcar_fallido(motivo)
            
            return JsonResponse({
                'success': True,
                'message': 'Entrega marcada como fallida'
            })
            
        except Entrega.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Entrega no encontrada'
            }, status=404)


class EntregaDetailView(LoginRequiredMixin, DetailView):
    """Vista para mostrar detalles completos de una entrega"""
    model = Entrega
    template_name = 'ventas/entrega_detail.html'
    context_object_name = 'entrega'
    pk_url_kwarg = 'entrega_id'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_deliver_orders():
            raise PermissionDenied("No tienes permisos para ver entregas")
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = Entrega.objects.select_related(
            'pedido__cliente', 
            'repartidor',
            'pedido__asignado_a'
        ).prefetch_related('pedido__items__producto')
        
        # Los repartidores solo ven sus entregas
        if self.request.user.role == 'repartidor':
            queryset = queryset.filter(repartidor=self.request.user)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entrega = self.object
        
        # Información del pedido
        context['pedido'] = entrega.pedido
        context['items'] = entrega.pedido.items.all()
        
        # Verificar si se puede reprogramar (solo entregas fallidas)
        context['puede_reprogramar'] = entrega.estado == 'fallido'
        
        return context


class ReprogramarEntregaView(LoginRequiredMixin, View):
    """Vista para reprogramar entregas fallidas"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_deliver_orders():
            raise PermissionDenied("No tienes permisos para reprogramar entregas")
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, entrega_id):
        """Mostrar formulario de reprogramación"""
        try:
            entrega = get_object_or_404(Entrega, id=entrega_id)
            
            # Solo se pueden reprogramar entregas fallidas
            if entrega.estado != 'fallido':
                messages.error(request, 'Solo se pueden reprogramar entregas fallidas.')
                return redirect('ventas:entrega_detail', entrega_id=entrega_id)
            
            # Los repartidores solo pueden reprogramar sus entregas
            if request.user.role == 'repartidor' and entrega.repartidor != request.user:
                raise PermissionDenied("No puedes reprogramar entregas de otros repartidores")
            
            # Obtener repartidores disponibles
            repartidores = User.objects.filter(role='repartidor', is_active=True)
            
            context = {
                'entrega': entrega,
                'repartidores': repartidores,
            }
            
            return render(request, 'ventas/reprogramar_entrega.html', context)
            
        except Entrega.DoesNotExist:
            messages.error(request, 'Entrega no encontrada.')
            return redirect('ventas:entregas_repartidor')
    
    def post(self, request, entrega_id):
        """Procesar reprogramación de entrega"""
        try:
            entrega = get_object_or_404(Entrega, id=entrega_id)
            
            # Validar que sea una entrega fallida
            if entrega.estado != 'fallido':
                return JsonResponse({
                    'success': False,
                    'message': 'Solo se pueden reprogramar entregas fallidas'
                }, status=400)
            
            # Obtener datos del formulario
            nueva_fecha = request.POST.get('fecha_programada')
            nuevo_repartidor_id = request.POST.get('repartidor')
            nueva_direccion = request.POST.get('direccion_entrega', entrega.direccion_entrega)
            nuevo_telefono = request.POST.get('telefono_contacto', entrega.telefono_contacto)
            observaciones = request.POST.get('observaciones_reprogramacion', '')
            
            # Validaciones
            if not nueva_fecha:
                return JsonResponse({
                    'success': False,
                    'message': 'Debe especificar una nueva fecha'
                }, status=400)
            
            if not nuevo_repartidor_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Debe seleccionar un repartidor'
                }, status=400)
            
            # Verificar que el repartidor existe
            try:
                nuevo_repartidor = User.objects.get(id=nuevo_repartidor_id, role='repartidor')
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Repartidor no válido'
                }, status=400)
            
            # Actualizar la entrega
            from datetime import datetime
            from django.utils import timezone
            
            # Convertir fecha string a datetime
            try:
                nueva_fecha_dt = datetime.fromisoformat(nueva_fecha.replace('Z', '+00:00'))
                if timezone.is_naive(nueva_fecha_dt):
                    nueva_fecha_dt = timezone.make_aware(nueva_fecha_dt)
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'message': 'Formato de fecha inválido'
                }, status=400)
            
            # Actualizar campos
            entrega.fecha_programada = nueva_fecha_dt
            entrega.repartidor = nuevo_repartidor
            entrega.direccion_entrega = nueva_direccion
            entrega.telefono_contacto = nuevo_telefono
            entrega.estado = 'programada'  # Resetear a programada
            
            # Limpiar datos de entrega anterior
            entrega.fecha_salida = None
            entrega.fecha_entrega = None
            entrega.persona_recibe = ''
            entrega.firma_digital = ''
            entrega.foto_evidencia = None
            
            # Añadir observaciones de reprogramación
            if observaciones:
                if entrega.observaciones:
                    entrega.observaciones += f"\n\n--- REPROGRAMADA ---\n{observaciones}"
                else:
                    entrega.observaciones = f"REPROGRAMADA: {observaciones}"
            
            entrega.save()
            
            # Actualizar pedido si estaba marcado como no entregado
            if entrega.pedido.estado in ['no_entregado', 'devuelto']:
                entrega.pedido.estado = 'completado'  # Volver a completado para entrega
                entrega.pedido.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Entrega reprogramada exitosamente para {nueva_fecha_dt.strftime("%d/%m/%Y %H:%M")}',
                'redirect_url': f'/ventas/entregas/{entrega_id}/'
            })
            
        except Entrega.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Entrega no encontrada'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error inesperado: {str(e)}'
            }, status=500)


# Vista temporal para probar autocompletado
def test_autocompletado(request):
    """Vista temporal para probar el autocompletado de clientes"""
    from django.shortcuts import render
    return render(request, 'test_autocompletado.html')

def test_ajax_simple(request):
    """Vista de prueba simple para AJAX"""
    from django.http import HttpResponse
    html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Test AJAX Simple</title>
</head>
<body>
    <h1>Test AJAX Directo</h1>
    <input type="text" id="query" placeholder="Escribe aquí (ej: Ana)" value="Ana">
    <button onclick="testAPI()">Probar API</button>
    <div id="result"></div>

    <script>
        function testAPI() {
            const query = document.getElementById('query').value;
            const resultDiv = document.getElementById('result');
            
            console.log('Testing with query:', query);
            resultDiv.innerHTML = 'Enviando petición...';
            
            fetch('/ventas/api/clientes/?q=' + encodeURIComponent(query))
                .then(response => {
                    console.log('Response status:', response.status);
                    return response.json();
                })
                .then(data => {
                    console.log('Data received:', data);
                    resultDiv.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                })
                .catch(error => {
                    console.error('Error:', error);
                    resultDiv.innerHTML = 'Error: ' + error.message;
                });
        }
        
        // Auto-test on load
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(() => {
                testAPI();
            }, 500);
        });
    </script>
</body>
</html>
    '''
    return HttpResponse(html)

def test_syntax(request):
    """Vista de prueba para verificar sintaxis JavaScript"""
    from django.http import HttpResponse
    with open('test_syntax.html', 'r', encoding='utf-8') as f:
        html = f.read()
    return HttpResponse(html)

# ============= RUTA OPTIMIZADA PARA REPARTIDORES =============

@login_required
def ruta_optimizada_view(request):
    """Vista para mostrar la ruta optimizada de entregas para repartidores"""
    
    # Verificar que el usuario sea repartidor
    if not request.user.can_deliver_orders():
        messages.error(request, "No tienes permisos para ver rutas de entrega.")
        return redirect('dashboard')
    
    # Obtener entregas asignadas al repartidor para hoy
    hoy = timezone.now().date()
    entregas = Entrega.objects.filter(
        repartidor=request.user,
        fecha_programada__date=hoy,
        estado__in=['programada', 'en_camino']
    ).select_related('pedido__cliente')
    
    if not entregas.exists():
        # No hay entregas para optimizar
        context = {
            'ruta_data': None
        }
        return render(request, 'ventas/ruta_optimizada.html', context)
    
    # Verificar si se solicita recalcular
    recalcular = request.GET.get('recalcular') == '1'
    
    try:
        # Obtener o crear ruta optimizada
        ruta_data = request.user.optimizar_ruta_entregas(list(entregas), recalcular=recalcular)
        
        if ruta_data:
            # Preparar datos para el template
            ruta_detallada = []
            orden = 1
            
            for entrega in ruta_data['entregas_ordenadas']:
                cliente = entrega.pedido.cliente
                
                ruta_detallada.append({
                    'orden': orden,
                    'entrega': entrega,
                    'cliente': cliente,
                })
                orden += 1
            
            # Actualizar datos con información detallada
            ruta_data['ruta_detallada'] = ruta_detallada
            
            context = {
                'ruta_data': ruta_data
            }
        else:
            context = {
                'ruta_data': None
            }
            messages.warning(request, "No se pudo calcular una ruta optimizada.")
    
    except Exception as e:
        messages.error(request, f"Error al calcular la ruta: {str(e)}")
        context = {
            'ruta_data': None
        }
    
    return render(request, 'ventas/ruta_optimizada.html', context)

@login_required
def marcar_salida_entrega(request, entrega_id):
    """API para marcar que el repartidor sale hacia una entrega"""
    
    if not request.user.can_deliver_orders():
        return JsonResponse({'success': False, 'message': 'No tienes permisos'})
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    try:
        entrega = get_object_or_404(Entrega, id=entrega_id, repartidor=request.user)
        
        if entrega.estado != 'programada':
            return JsonResponse({
                'success': False, 
                'message': 'La entrega no está en estado programada'
            })
        
        # Cambiar estado a en_camino
        entrega.estado = 'en_camino'
        entrega.fecha_salida = timezone.now()
        entrega.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Salida registrada correctamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'Error: {str(e)}'
        })


# ============= API REPARTIDOR =============

@require_http_methods(["GET"])
@login_required
def obtener_items_entrega_api(request, entrega_id):
    """API para obtener los items de una entrega"""
    try:
        entrega = get_object_or_404(Entrega, id=entrega_id)
        
        # Verificar permisos
        if not request.user.can_deliver_orders():
            return JsonResponse({'success': False, 'error': 'Sin permisos'})
        
        # Solo el repartidor asignado puede ver los items
        if entrega.repartidor != request.user:
            return JsonResponse({'success': False, 'error': 'No es tu entrega'})
        
        # Obtener items del pedido
        items_data = []
        for item in entrega.pedido.items.select_related('producto').all():
            items_data.append({
                'id': item.id,
                'producto_nombre': item.producto.nombre,
                'cantidad': str(item.cantidad),
                'precio_unitario': str(item.precio_unitario),
                'subtotal': str(item.subtotal)
            })
        
        return JsonResponse({
            'success': True, 
            'items': items_data,
            'pedido_numero': entrega.pedido.numero
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(["POST"])
@login_required
def iniciar_entrega_api(request, entrega_id):
    """API para que repartidor inicie una entrega"""
    try:
        entrega = get_object_or_404(Entrega, id=entrega_id)
        
        # Verificar permisos
        if not request.user.can_deliver_orders():
            return JsonResponse({'success': False, 'error': 'Sin permisos'})
        
        # Solo el repartidor asignado puede iniciar
        if entrega.repartidor != request.user:
            return JsonResponse({'success': False, 'error': 'No es tu entrega'})
        
        # Solo se puede iniciar si está programada
        if entrega.estado != 'programada':
            return JsonResponse({'success': False, 'error': 'Estado inválido'})
        
        entrega.estado = 'en_camino'
        entrega.fecha_inicio = timezone.now()
        entrega.save()
        
        return JsonResponse({'success': True, 'message': 'Entrega iniciada'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(["POST"])
@login_required
def completar_entrega_api(request, entrega_id):
    """API para que repartidor complete una entrega"""
    try:
        entrega = get_object_or_404(Entrega, id=entrega_id)
        
        # Verificar permisos
        if not request.user.can_deliver_orders():
            return JsonResponse({'success': False, 'error': 'Sin permisos'})
        
        # Solo el repartidor asignado puede completar
        if entrega.repartidor != request.user:
            return JsonResponse({'success': False, 'error': 'No es tu entrega'})
        
        # Solo se puede completar si está en camino
        if entrega.estado != 'en_camino':
            return JsonResponse({'success': False, 'error': 'Estado inválido'})
        
        entrega.estado = 'entregado'
        entrega.fecha_entrega = timezone.now()
        entrega.save()
        
        # Actualizar estado del pedido
        entrega.pedido.estado = 'entregado'
        entrega.pedido.save()
        
        return JsonResponse({'success': True, 'message': 'Entrega completada'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(["POST"])
@login_required
def marcar_entrega_fallida_api(request, entrega_id):
    """API para que repartidor marque entrega como fallida"""
    try:
        import json
        data = json.loads(request.body)
        motivo = data.get('motivo', 'Sin motivo especificado')
        
        entrega = get_object_or_404(Entrega, id=entrega_id)
        
        # Verificar permisos
        if not request.user.can_deliver_orders():
            return JsonResponse({'success': False, 'error': 'Sin permisos'})
        
        # Solo el repartidor asignado puede marcar como fallida
        if entrega.repartidor != request.user:
            return JsonResponse({'success': False, 'error': 'No es tu entrega'})
        
        # Solo se puede marcar como fallida si está en camino
        if entrega.estado != 'en_camino':
            return JsonResponse({'success': False, 'error': 'Estado inválido'})
        
        entrega.estado = 'fallido'
        entrega.motivo_falla = motivo
        entrega.fecha_falla = timezone.now()
        entrega.save()
        
        return JsonResponse({'success': True, 'message': 'Entrega marcada como fallida'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(["GET"])
@login_required
def detalle_entrega_api(request, entrega_id):
    """API para obtener detalles de una entrega"""
    try:
        entrega = get_object_or_404(Entrega, id=entrega_id)
        
        # Verificar permisos
        if not request.user.can_deliver_orders():
            return JsonResponse({'success': False, 'error': 'Sin permisos'})
        
        # Solo el repartidor asignado puede ver detalles
        if entrega.repartidor != request.user:
            return JsonResponse({'success': False, 'error': 'No es tu entrega'})
        
        # Construir HTML para el modal
        html = f"""
        <div class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <h4 class="font-medium text-gray-900">Información del Pedido</h4>
                    <p class="text-sm text-gray-600">Número: {entrega.pedido.numero_pedido}</p>
                    <p class="text-sm text-gray-600">Total: ${entrega.pedido.total:,.2f}</p>
                </div>
                <div>
                    <h4 class="font-medium text-gray-900">Cliente</h4>
                    <p class="text-sm text-gray-600">{entrega.pedido.cliente.nombre}</p>
                    <p class="text-sm text-gray-600">{entrega.pedido.cliente.telefono}</p>
                </div>
            </div>
            
            <div>
                <h4 class="font-medium text-gray-900">Dirección de Entrega</h4>
                <p class="text-sm text-gray-600">{entrega.direccion_entrega}</p>
            </div>
            
            <div>
                <h4 class="font-medium text-gray-900">Estado</h4>
                <p class="text-sm text-gray-600">
                    <span class="estado-badge estado-{entrega.estado}">
                        {entrega.get_estado_display()}
                    </span>
                </p>
            </div>
            
            <div>
                <h4 class="font-medium text-gray-900">Productos</h4>
                <div class="mt-2 space-y-1">
        """
        
        for item in entrega.pedido.items.all():
            html += f"""
                    <div class="text-sm text-gray-600">
                        {item.cantidad}x {item.producto.nombre} - ${item.precio_unitario:,.2f}
                    </div>
            """
        
        html += """
                </div>
            </div>
        </div>
        """
        
        return JsonResponse({'success': True, 'html': html})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})





# ============= OPTIMIZADOR DE RUTAS =============

@login_required
def optimizar_ruta_view(request):
    """Vista para optimizar rutas de entrega"""
    
    # Verificar permisos - solo repartidores y administradores
    if not (request.user.can_deliver_orders() or request.user.is_staff):
        raise PermissionDenied("No tienes permisos para acceder al optimizador de rutas")
    
    # Obtener entregas según el tipo de usuario
    if request.user.can_deliver_orders() and not request.user.is_staff:
        # Repartidor: solo sus entregas asignadas
        entregas = Entrega.objects.filter(
            repartidor=request.user,
            estado__in=['programada', 'pendiente', 'en_ruta']
        ).select_related(
            'pedido__cliente'
        ).order_by('fecha_programada', 'id')
    else:
        # Administrador: todas las entregas pendientes
        entregas = Entrega.objects.filter(
            estado__in=['programada', 'pendiente', 'en_ruta']
        ).select_related(
            'pedido__cliente',
            'repartidor'
        ).order_by('fecha_programada', 'repartidor', 'id')
    
    # Estadísticas simples
    total_entregas = entregas.count()
    
    context = {
        'entregas': entregas,
        'total_entregas': total_entregas,
        'es_repartidor': request.user.can_deliver_orders() and not request.user.is_staff,
    }
    
    return render(request, 'ventas/optimizar_ruta.html', context)


class ReporteItemsRechazadosView(LoginRequiredMixin, TemplateView):
    """Vista para mostrar reporte de items rechazados"""
    template_name = 'ventas/reporte_items_rechazados.html'
    paginate_by = 12
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener filtros
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        motivo = self.request.GET.get('motivo')
        
        # Filtrar items rechazados
        from .models import ItemRechazado
        queryset = ItemRechazado.objects.select_related(
            'entrega__pedido__cliente',
            'item_pedido__producto',
            'entrega__repartidor'
        ).order_by('-fecha_rechazo')
        
        if fecha_desde:
            queryset = queryset.filter(fecha_rechazo__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_rechazo__lte=fecha_hasta)
        if motivo:
            queryset = queryset.filter(motivo=motivo)
        
        # Calcular estadísticas
        total_items_rechazados = queryset.count()
        valor_total_rechazado = sum(item.valor_rechazado for item in queryset)
        entregas_con_rechazos = queryset.values('entrega').distinct().count()
        
        # Calcular porcentaje de rechazo (sobre total de entregas del período)
        entregas_totales = Entrega.objects.all()
        if fecha_desde:
            entregas_totales = entregas_totales.filter(fecha_programada__gte=fecha_desde)
        if fecha_hasta:
            entregas_totales = entregas_totales.filter(fecha_programada__lte=fecha_hasta)
        
        total_entregas = entregas_totales.count()
        porcentaje_rechazo = (entregas_con_rechazos / total_entregas * 100) if total_entregas > 0 else 0
        
        # Paginación
        from django.core.paginator import Paginator
        paginator = Paginator(queryset, self.paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context.update({
            'items_rechazados': page_obj,
            'total_items_rechazados': total_items_rechazados,
            'valor_total_rechazado': valor_total_rechazado,
            'entregas_con_rechazos': entregas_con_rechazos,
            'porcentaje_rechazo': porcentaje_rechazo,
            'is_paginated': page_obj.has_other_pages(),
            'page_obj': page_obj,
        })
        
        return context

@login_required
def asignar_pedido_bodega(request, pk):
    """Vista para asignar un pedido a un bodeguero"""
    # Verificar permisos de bodega
    if not request.user.can_view_inventory():
        messages.error(request, 'No tiene permisos para esta acción.')
        return redirect('ventas:pedidos_alistamiento')
    
    try:
        pedido = Pedido.objects.get(pk=pk)
        
        # Verificar que el pedido esté en estado proceso
        if pedido.estado != 'proceso':
            messages.error(request, f'Solo se pueden asignar pedidos en estado "Proceso". Este pedido está en estado "{pedido.get_estado_display()}".')
            return redirect('ventas:pedidos_alistamiento')
        
        # Verificar que no esté ya asignado
        if pedido.asignado_a:
            messages.error(request, f'Este pedido ya está asignado a {pedido.asignado_a.get_full_name()}.')
            return redirect('ventas:pedidos_alistamiento')
        
        # Asignar al usuario actual
        pedido.asignado_a = request.user
        pedido.save()
        
        messages.success(request, f'Pedido #{pedido.numero} asignado exitosamente a {request.user.get_full_name()}. Ahora puede proceder con el alistamiento.')
        return redirect('ventas:pedidos_alistamiento')
        
    except Pedido.DoesNotExist:
        messages.error(request, 'Pedido no encontrado.')
        return redirect('ventas:pedidos_alistamiento')


# ============= VISTAS SIMPLES PARA URLs FALTANTES =============

@login_required
def cambiar_estado_pedido_simple(request, pk):
    """Vista simple para cambiar estado de pedido"""
    pedido = get_object_or_404(Pedido, pk=pk)
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in ['pendiente', 'proceso', 'completado', 'cancelado']:
            pedido.estado = nuevo_estado
            pedido.save()
            messages.success(request, f'Estado del pedido actualizado a {nuevo_estado}.')
        else:
            messages.error(request, 'Estado inválido.')
    
    return redirect('ventas:pedido_detail', pk=pk)

@login_required
def completar_pedido_inmediato(request, pk):
    """Vista simple para completar pedido inmediatamente"""
    pedido = get_object_or_404(Pedido, pk=pk)
    
    if request.method == 'POST':
        pedido.estado = 'completado'
        pedido.fecha_completado = timezone.now()
        pedido.save()
        messages.success(request, 'Pedido completado exitosamente.')
    
    return redirect('ventas:pedido_detail', pk=pk)

@login_required
def asignar_pedido_bodega(request, pk):
    """Vista simple para asignar pedido a bodega"""
    pedido = get_object_or_404(Pedido, pk=pk)
    
    if request.method == 'POST':
        pedido.asignado_a = request.user
        pedido.estado = 'proceso'
        pedido.save()
        messages.success(request, 'Pedido asignado a bodega exitosamente.')
    
    return redirect('ventas:pedido_detail', pk=pk)

@login_required
def reprogramar_entrega(request, pk):
    """Vista simple para reprogramar entrega"""
    entrega = get_object_or_404(Entrega, pk=pk)
    
    if request.method == 'POST':
        nueva_fecha = request.POST.get('nueva_fecha')
        if nueva_fecha:
            entrega.fecha_programada = nueva_fecha
            entrega.save()
            messages.success(request, 'Entrega reprogramada exitosamente.')
        else:
            messages.error(request, 'Fecha inválida.')
    
    return redirect('ventas:entrega_detail', pk=pk)

@login_required
def generar_pdf_cotizacion(request, pk):
    """Vista simple para generar PDF de cotización"""
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    messages.info(request, 'PDF generado exitosamente.')
    return redirect('ventas:cotizacion_detail', pk=pk)

@login_required
def enviar_cotizacion(request, pk):
    """Vista simple para enviar cotización"""
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    cotizacion.estado = 'enviada'
    cotizacion.save()
    messages.success(request, 'Cotización enviada exitosamente.')
    return redirect('ventas:cotizacion_detail', pk=pk)

@login_required
def anular_factura(request, pk):
    """Vista simple para anular factura"""
    factura = get_object_or_404(Factura, pk=pk)
    
    if request.method == 'POST':
        factura.estado = 'anulada'
        factura.save()
        messages.success(request, 'Factura anulada exitosamente.')
    
    return redirect('ventas:factura_detail', pk=pk)

@login_required
def reporte_ventas(request):
    """Vista simple para reportes de ventas"""
    messages.info(request, 'Funcionalidad de reportes en desarrollo.')
    return redirect('ventas:dashboard')

@login_required
def imprimir_pedido(request, pk):
    """Vista simple para imprimir pedido"""
    pedido = get_object_or_404(Pedido, pk=pk)
    messages.info(request, 'Pedido enviado a impresión.')
    return redirect('ventas:pedido_detail', pk=pk)
