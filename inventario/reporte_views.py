from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from inventario.models import Producto, Stock, MovimientoInventario, Bodega
from ventas.models import Pedido, ItemPedido
import json

@login_required
def reporte_integracion_ventas_inventario(request):
    """Vista para reporte integrado de ventas e inventario"""
    
    # Obtener filtros de la URL
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    producto_id = request.GET.get('producto_id')
    
    # Fechas por defecto (último mes)
    if not fecha_desde:
        fecha_desde = (timezone.now() - timedelta(days=30)).date()
    else:
        fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
    
    if not fecha_hasta:
        fecha_hasta = timezone.now().date()
    else:
        fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    
    # ========== ESTADÍSTICAS PRINCIPALES ==========
    
    # Pedidos completados en el período
    pedidos_completados = Pedido.objects.filter(
        estado='completado',
        fecha__date__range=[fecha_desde, fecha_hasta]
    )
    
    # Pedidos del mes anterior para comparación
    fecha_desde_anterior = fecha_desde - timedelta(days=30)
    fecha_hasta_anterior = fecha_desde - timedelta(days=1)
    pedidos_mes_anterior = Pedido.objects.filter(
        estado='completado',
        fecha__date__range=[fecha_desde_anterior, fecha_hasta_anterior]
    ).count()
    
    # Calcular crecimiento
    ventas_actual = pedidos_completados.count()
    crecimiento_ventas = 0
    if pedidos_mes_anterior > 0:
        crecimiento_ventas = ((ventas_actual - pedidos_mes_anterior) / pedidos_mes_anterior) * 100
    
    # Valor total vendido
    valor_total = pedidos_completados.aggregate(
        total=Sum('total')
    )['total'] or 0
    
    # Productos únicos vendidos
    productos_vendidos = ItemPedido.objects.filter(
        pedido__in=pedidos_completados
    ).values('producto').distinct().count()
    
    # Movimientos de inventario relacionados con ventas
    movimientos_inventario = MovimientoInventario.objects.filter(
        motivo__in=['venta', 'reserva', 'liberacion_reserva', 'devolucion_cliente'],
        fecha_movimiento__date__range=[fecha_desde, fecha_hasta]
    ).count()
    
    stats = {
        'ventas_completadas': ventas_actual,
        'crecimiento_ventas': round(crecimiento_ventas, 1),
        'valor_total': valor_total,
        'productos_vendidos': productos_vendidos,
        'movimientos_inventario': movimientos_inventario
    }
    
    # ========== PRODUCTOS MÁS IMPACTADOS ==========
    
    # Filtro por producto específico si se selecciona
    queryset_productos = Producto.objects.filter(activo=True)
    if producto_id:
        queryset_productos = queryset_productos.filter(id=producto_id)
    
    productos_impactados = []
    
    for producto in queryset_productos:
        # Cantidad vendida en el período
        cantidad_vendida = ItemPedido.objects.filter(
            pedido__in=pedidos_completados,
            producto=producto
        ).aggregate(total=Sum('cantidad'))['total'] or 0
        
        if cantidad_vendida > 0:
            # Stock actual en todas las bodegas
            stock_actual = Stock.objects.filter(
                producto=producto
            ).aggregate(total=Sum('cantidad'))['total'] or 0
            
            # Stock inicial aproximado (stock actual + cantidad vendida)
            stock_inicial = stock_actual + int(cantidad_vendida)
            
            # Calcular impacto porcentual
            impacto_porcentaje = 0
            if stock_inicial > 0:
                impacto_porcentaje = (int(cantidad_vendida) / stock_inicial) * 100
            
            # Valor vendido
            valor_vendido = ItemPedido.objects.filter(
                pedido__in=pedidos_completados,
                producto=producto
            ).aggregate(total=Sum('total'))['total'] or 0
            
            productos_impactados.append({
                'codigo': producto.codigo,
                'nombre': producto.nombre,
                'stock_inicial': stock_inicial,
                'cantidad_vendida': int(cantidad_vendida),
                'stock_actual': stock_actual,
                'impacto_porcentaje': impacto_porcentaje,
                'valor_vendido': valor_vendido
            })
    
    # Ordenar por impacto porcentual descendente
    productos_impactados.sort(key=lambda x: x['impacto_porcentaje'], reverse=True)
    productos_impactados = productos_impactados[:10]  # Top 10
    
    # ========== MOVIMIENTOS RECIENTES ==========
    
    movimientos_recientes = MovimientoInventario.objects.filter(
        motivo__in=['venta', 'reserva', 'liberacion_reserva', 'devolucion_cliente'],
        fecha_movimiento__date__range=[fecha_desde, fecha_hasta]
    ).select_related(
        'producto', 'usuario'
    ).order_by('-fecha_movimiento')[:20]
    
    # ========== DATOS PARA GRÁFICOS ==========
    
    # Gráfico de Stock: Top 5 productos más impactados
    top_5_productos = productos_impactados[:5]
    
    chart_data = {
        'productos_labels': json.dumps([p['codigo'] for p in top_5_productos]),
        'stock_inicial': json.dumps([p['stock_inicial'] for p in top_5_productos]),
        'stock_actual': json.dumps([p['stock_actual'] for p in top_5_productos]),
    }
    
    # Gráfico de movimientos por tipo
    movimientos_por_tipo = MovimientoInventario.objects.filter(
        motivo__in=['venta', 'reserva', 'liberacion_reserva', 'devolucion_cliente'],
        fecha_movimiento__date__range=[fecha_desde, fecha_hasta]
    ).values('motivo').annotate(
        cantidad=Count('id')
    ).order_by('-cantidad')
    
    tipos_labels = []
    tipos_datos = []
    for movimiento in movimientos_por_tipo:
        tipos_labels.append(dict(MovimientoInventario.MOTIVO_CHOICES)[movimiento['motivo']])
        tipos_datos.append(movimiento['cantidad'])
    
    chart_data.update({
        'tipos_movimiento_labels': json.dumps(tipos_labels),
        'tipos_movimiento_datos': json.dumps(tipos_datos)
    })
    
    # ========== CONTEXTO PARA EL TEMPLATE ==========
    
    context = {
        'title': 'Reporte Integrado Ventas-Inventario',
        'stats': stats,
        'productos_impactados': productos_impactados,
        'movimientos_recientes': movimientos_recientes,
        'chart_data': chart_data,
        'filtros': {
            'fecha_desde': fecha_desde.strftime('%Y-%m-%d') if fecha_desde else '',
            'fecha_hasta': fecha_hasta.strftime('%Y-%m-%d') if fecha_hasta else '',
            'producto_id': producto_id or ''
        },
        'productos': Producto.objects.filter(activo=True).order_by('codigo')  # Para el filtro
    }
    
    return render(request, 'inventario/reporte_integracion.html', context)