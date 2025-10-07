# ventas/general_views.py
"""
Vistas generales del módulo de ventas
Dashboard, búsquedas generales y funcionalidades compartidas
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Cliente, Cotizacion, Pedido, Factura, Entrega
from inventario.models import Producto


class VentasRequiredMixin(UserPassesTestMixin):
    """Mixin para verificar permisos de ventas"""
    def test_func(self):
        return self.request.user.can_create_sales()


# ============= DASHBOARD =============

@login_required
def dashboard_view(request):
    """Dashboard principal de ventas"""
    if not request.user.can_create_sales():
        return redirect('dashboard')
    
    # Estadísticas del mes actual
    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)
    
    # Ventas del mes
    ventas_mes = Factura.objects.filter(
        fecha_creacion__date__gte=primer_dia_mes,
        estado='pagada'
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    # Pedidos pendientes
    pedidos_pendientes = Pedido.objects.filter(estado='pendiente').count()
    pedidos_alistamiento = Pedido.objects.filter(estado='alistamiento').count()
    
    # Facturas por cobrar
    facturas_pendientes = Factura.objects.filter(
        estado='pendiente'
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    # Entregas del día
    entregas_hoy = Entrega.objects.filter(fecha_programada__date=hoy).count()
    entregas_pendientes = Entrega.objects.filter(
        estado__in=['pendiente', 'asignada', 'en_ruta']
    ).count()
    
    # Cotizaciones pendientes
    cotizaciones_pendientes = Cotizacion.objects.filter(estado='pendiente').count()
    
    # Ventas últimos 7 días
    hace_7_dias = hoy - timedelta(days=7)
    ventas_semana = []
    
    for i in range(7):
        fecha = hace_7_dias + timedelta(days=i)
        ventas_dia = Factura.objects.filter(
            fecha_creacion__date=fecha,
            estado='pagada'
        ).aggregate(Sum('total'))['total__sum'] or 0
        
        ventas_semana.append({
            'fecha': fecha.strftime('%d/%m'),
            'ventas': float(ventas_dia)
        })
    
    # Top productos vendidos del mes
    from inventario.models import MovimientoInventario
    top_productos = MovimientoInventario.objects.filter(
        fecha_movimiento__date__gte=primer_dia_mes,
        tipo_movimiento='salida',
        motivo='venta'
    ).values(
        'producto__nombre'
    ).annotate(
        cantidad_vendida=Sum('cantidad')
    ).order_by('-cantidad_vendida')[:5]
    
    # Clientes con más compras del mes
    top_clientes = Factura.objects.filter(
        fecha_creacion__date__gte=primer_dia_mes,
        estado='pagada'
    ).values(
        'cliente__nombre_completo'
    ).annotate(
        total_compras=Sum('total'),
        num_facturas=Count('id')
    ).order_by('-total_compras')[:5]
    
    context = {
        'ventas_mes': ventas_mes,
        'pedidos_pendientes': pedidos_pendientes,
        'pedidos_alistamiento': pedidos_alistamiento,
        'facturas_pendientes': facturas_pendientes,
        'entregas_hoy': entregas_hoy,
        'entregas_pendientes': entregas_pendientes,
        'cotizaciones_pendientes': cotizaciones_pendientes,
        'ventas_semana': ventas_semana,
        'top_productos': top_productos,
        'top_clientes': top_clientes,
        'title': 'Dashboard de Ventas'
    }
    
    return render(request, 'ventas/dashboard.html', context)

@login_required
def dashboard_charts_view(request):
    """Dashboard avanzado con gráficos interactivos"""
    if not request.user.can_create_sales():
        return redirect('dashboard')
    context = {
        'ventas_mes': ventas_mes,
        'pedidos_pendientes': pedidos_pendientes,
        'pedidos_alistamiento': pedidos_alistamiento,
        'facturas_pendientes': facturas_pendientes,
        'entregas_hoy': entregas_hoy,
        'entregas_pendientes': entregas_pendientes,
        'cotizaciones_pendientes': cotizaciones_pendientes,
        'ventas_semana': ventas_semana,
        'top_productos': top_productos,
        'top_clientes': top_clientes,
        'title': 'Dashboard de Ventas'
    }
    
    return render(request, 'ventas/dashboard.html', context)

@login_required
def dashboard_charts_view(request):
    """Dashboard avanzado con gráficos interactivos"""
    if not request.user.can_create_sales():
        return redirect('dashboard')
    
    context = {
        'title': 'Dashboard Avanzado'
    }
    
    return render(request, 'ventas/dashboard_charts.html', context)


# ============= APIS GENERALES =============

@login_required
def buscar_productos_api(request):
    """API para buscar productos (usado en autocompletado)"""
    if not request.user.can_create_sales():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    term = request.GET.get('term', '')
    if len(term) < 2:
        return JsonResponse([], safe=False)
    
    productos = Producto.objects.filter(
        Q(nombre__icontains=term) |
        Q(codigo__icontains=term) |
        Q(codigo_barras__icontains=term),
        activo=True
    )[:10]
    
    results = []
    for producto in productos:
        results.append({
            'id': producto.id,
            'label': f"{producto.nombre} - {producto.codigo}",
            'value': producto.nombre,
            'codigo': producto.codigo,
            'precio': float(producto.precio),
            'stock': producto.stock,
            'categoria': producto.categoria.nombre if producto.categoria else '',
            'imagen': producto.imagen.url if producto.imagen else None
        })
    
    return JsonResponse(results, safe=False)


@login_required
def obtener_precio_producto(request, producto_id):
    """API para obtener precio actual de un producto"""
    if not request.user.can_create_sales():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    try:
        producto = Producto.objects.get(id=producto_id, activo=True)
        return JsonResponse({
            'precio': float(producto.precio),
            'stock': producto.stock,
            'disponible': producto.stock > 0
        })
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)


@login_required
def verificar_stock_disponible(request):
    """API para verificar stock de múltiples productos"""
    if not request.user.can_create_sales():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    import json
    
    if request.method == 'POST':
        data = json.loads(request.body)
        productos_verificar = data.get('productos', [])
        
        results = []
        for item in productos_verificar:
            producto_id = item.get('producto_id')
            cantidad_solicitada = item.get('cantidad', 0)
            
            try:
                producto = Producto.objects.get(id=producto_id, activo=True)
                disponible = producto.stock >= cantidad_solicitada
                
                results.append({
                    'producto_id': producto_id,
                    'nombre': producto.nombre,
                    'stock_actual': producto.stock,
                    'cantidad_solicitada': cantidad_solicitada,
                    'disponible': disponible,
                    'faltante': max(0, cantidad_solicitada - producto.stock)
                })
            except Producto.DoesNotExist:
                results.append({
                    'producto_id': producto_id,
                    'error': 'Producto no encontrado'
                })
        
        return JsonResponse({
            'productos': results,
            'todos_disponibles': all(r.get('disponible', False) for r in results if 'error' not in r)
        })
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


# ============= FUNCIONES DE UTILIDAD =============

def calcular_estadisticas_periodo(fecha_inicio, fecha_fin):
    """Función para calcular estadísticas de un período específico"""
    stats = {}
    
    # Ventas del período
    facturas_periodo = Factura.objects.filter(
        fecha_creacion__date__gte=fecha_inicio,
        fecha_creacion__date__lte=fecha_fin,
        estado='pagada'
    )
    
    stats['total_ventas'] = facturas_periodo.aggregate(Sum('total'))['total__sum'] or 0
    stats['numero_facturas'] = facturas_periodo.count()
    stats['promedio_venta'] = stats['total_ventas'] / stats['numero_facturas'] if stats['numero_facturas'] > 0 else 0
    
    # Pedidos del período
    pedidos_periodo = Pedido.objects.filter(
        fecha_creacion__date__gte=fecha_inicio,
        fecha_creacion__date__lte=fecha_fin
    )
    
    stats['total_pedidos'] = pedidos_periodo.count()
    stats['pedidos_completados'] = pedidos_periodo.filter(estado='completado').count()
    stats['tasa_conversion'] = (stats['pedidos_completados'] / stats['total_pedidos'] * 100) if stats['total_pedidos'] > 0 else 0
    
    # Entregas del período
    entregas_periodo = Entrega.objects.filter(
        fecha_creacion__date__gte=fecha_inicio,
        fecha_creacion__date__lte=fecha_fin
    )
    
    stats['total_entregas'] = entregas_periodo.count()
    stats['entregas_exitosas'] = entregas_periodo.filter(estado='entregada').count()
    stats['tasa_entrega'] = (stats['entregas_exitosas'] / stats['total_entregas'] * 100) if stats['total_entregas'] > 0 else 0
    
    return stats


# ============= APIS PARA GRÁFICOS DEL DASHBOARD =============

@login_required
def api_ventas_por_mes(request):
    """API para gráfico de ventas por mes de los últimos 12 meses"""
    from django.db.models import Sum
    from datetime import datetime, timedelta
    import calendar
    
    hoy = timezone.now().date()
    hace_12_meses = hoy - timedelta(days=365)
    
    # Obtener ventas por mes
    ventas_por_mes = []
    for i in range(12):
        # Calcular el mes
        mes_actual = hoy.replace(day=1) - timedelta(days=30*i)
        mes_siguiente = mes_actual.replace(day=28) + timedelta(days=4)
        mes_siguiente = mes_siguiente.replace(day=1)
        
        ventas_mes = Factura.objects.filter(
            fecha_creacion__date__gte=mes_actual,
            fecha_creacion__date__lt=mes_siguiente,
            estado='pagada'
        ).aggregate(Sum('total'))['total__sum'] or 0
        
        ventas_por_mes.append({
            'mes': calendar.month_name[mes_actual.month][:3] + f' {mes_actual.year}',
            'ventas': float(ventas_mes),
            'fecha': mes_actual.isoformat()
        })
    
    ventas_por_mes.reverse()  # Ordenar cronológicamente
    
    return JsonResponse({
        'success': True,
        'data': ventas_por_mes
    })

@login_required  
def api_productos_mas_vendidos(request):
    """API para gráfico de productos más vendidos"""
    from inventario.models import MovimientoInventario
    from django.db.models import Sum
    
    hoy = timezone.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    
    productos_vendidos = MovimientoInventario.objects.filter(
        fecha_movimiento__date__gte=hace_30_dias,
        tipo_movimiento='salida',
        motivo='venta'
    ).values(
        'producto__nombre'
    ).annotate(
        cantidad_vendida=Sum('cantidad')
    ).order_by('-cantidad_vendida')[:10]
    
    data = []
    for item in productos_vendidos:
        data.append({
            'producto': item['producto__nombre'],
            'cantidad': float(item['cantidad_vendida'])
        })
    
    return JsonResponse({
        'success': True,
        'data': data
    })

@login_required
def api_estados_pedidos(request):
    """API para gráfico de distribución de estados de pedidos"""
    estados_count = {}
    
    for estado_code, estado_name in Pedido.ESTADO_CHOICES:
        count = Pedido.objects.filter(estado=estado_code).count()
        if count > 0:
            estados_count[estado_name] = count
    
    data = []
    for estado, count in estados_count.items():
        data.append({
            'estado': estado,
            'cantidad': count
        })
    
    return JsonResponse({
        'success': True,
        'data': data
    })

@login_required
def api_ventas_por_vendedor(request):
    """API para gráfico de ventas por vendedor del mes"""
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)
    
    # Obtener vendedores con ventas
    vendedores_ventas = Factura.objects.filter(
        fecha_creacion__date__gte=primer_dia_mes,
        estado='pagada',
        cliente__vendedor_asignado__isnull=False
    ).values(
        'cliente__vendedor_asignado__first_name',
        'cliente__vendedor_asignado__last_name'
    ).annotate(
        total_ventas=Sum('total'),
        num_ventas=Count('id')
    ).order_by('-total_ventas')[:8]
    
    data = []
    for item in vendedores_ventas:
        nombre = f"{item['cliente__vendedor_asignado__first_name']} {item['cliente__vendedor_asignado__last_name']}"
        if not nombre.strip():
            nombre = "Vendedor Sin Nombre"
            
        data.append({
            'vendedor': nombre,
            'ventas': float(item['total_ventas']),
            'num_ventas': item['num_ventas']
        })
    
    return JsonResponse({
        'success': True,
        'data': data
    })

@login_required
def api_estadisticas_dashboard(request):
    """API para estadísticas generales del dashboard"""
    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)
    mes_anterior = (primer_dia_mes - timedelta(days=1)).replace(day=1)
    
    # Estadísticas del mes actual
    pedidos_mes = Pedido.objects.filter(fecha_creacion__date__gte=primer_dia_mes).count()
    ventas_mes = Factura.objects.filter(
        fecha_creacion__date__gte=primer_dia_mes,
        estado='pagada'
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    # Estadísticas del mes anterior para comparación
    pedidos_mes_anterior = Pedido.objects.filter(
        fecha_creacion__date__gte=mes_anterior,
        fecha_creacion__date__lt=primer_dia_mes
    ).count()
    
    ventas_mes_anterior = Factura.objects.filter(
        fecha_creacion__date__gte=mes_anterior,
        fecha_creacion__date__lt=primer_dia_mes,
        estado='pagada'
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    # Calcular crecimientos
    crecimiento_pedidos = 0
    if pedidos_mes_anterior > 0:
        crecimiento_pedidos = ((pedidos_mes - pedidos_mes_anterior) / pedidos_mes_anterior) * 100
    
    crecimiento_ventas = 0
    if ventas_mes_anterior > 0:
        crecimiento_ventas = ((ventas_mes - ventas_mes_anterior) / ventas_mes_anterior) * 100
    
    # Pedidos pendientes
    pedidos_pendientes = Pedido.objects.filter(estado='pendiente').count()
    pedidos_proceso = Pedido.objects.filter(estado='proceso').count()
    
    # Alertas de stock
    try:
        from inventario.models import AlertaStock
        alertas_stock = AlertaStock.objects.filter(vista=False).count()
    except:
        alertas_stock = 0
    
    return JsonResponse({
        'success': True,
        'data': {
            'pedidos_mes': pedidos_mes,
            'ventas_mes': float(ventas_mes),
            'crecimiento_pedidos': round(crecimiento_pedidos, 1),
            'crecimiento_ventas': round(crecimiento_ventas, 1),
            'pedidos_pendientes': pedidos_pendientes,
            'pedidos_proceso': pedidos_proceso,
            'alertas_stock': alertas_stock,
            'mes_actual': primer_dia_mes.strftime('%B %Y')
        }
    })

# ============= VISTAS DE PRUEBA/DESARROLLO =============

@login_required
def test_autocompletado(request):
    """Vista de prueba para autocompletado"""
    return render(request, 'ventas/test_autocompletado.html')


@login_required
def test_ajax_simple(request):
    """Vista de prueba para AJAX"""
    if request.method == 'POST':
        return JsonResponse({'success': True, 'message': 'AJAX funcionando correctamente'})
    return render(request, 'ventas/test_ajax.html')


@login_required
def test_syntax(request):
    """Vista de prueba para verificar sintaxis"""
    return JsonResponse({'status': 'ok', 'message': 'Sintaxis correcta'})