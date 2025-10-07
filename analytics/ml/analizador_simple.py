"""
Analizador de clientes simplificado
"""

import statistics
from datetime import datetime, timedelta
from django.db.models import Q, Avg, Sum, Count, Max, Min, F
from django.utils import timezone
from decimal import Decimal


class AnalizadorClientesSimple:
    """
    Sistema de análisis de comportamiento de clientes usando estadísticas simples
    """
    
    def __init__(self):
        pass
        
    def extraer_metricas_cliente(self, cliente_id, dias_historicos=365):
        """
        Extrae métricas completas de comportamiento del cliente
        """
        from ventas.models import Cliente, Pedido, ItemPedido
        
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return None
        
        fecha_inicio = timezone.now() - timedelta(days=dias_historicos)
        
        # Pedidos del cliente
        pedidos = Pedido.objects.filter(
            cliente=cliente,
            fecha__gte=fecha_inicio
        )
        
        if not pedidos.exists():
            return self._metricas_cliente_nuevo(cliente)
        
        # Métricas básicas
        total_pedidos = pedidos.count()
        valor_total = pedidos.aggregate(Sum('total'))['total__sum'] or Decimal('0')
        
        # Métricas temporales
        primer_pedido = pedidos.aggregate(Min('fecha'))['fecha__min']
        ultimo_pedido = pedidos.aggregate(Max('fecha'))['fecha__max']
        
        if primer_pedido and ultimo_pedido and total_pedidos > 1:
            dias_cliente = (ultimo_pedido - primer_pedido).days or 1
            frecuencia_compra = dias_cliente / (total_pedidos - 1)
        else:
            frecuencia_compra = 365
            dias_cliente = (timezone.now().date() - primer_pedido.date()).days if primer_pedido else 0
        
        # Análisis de productos
        items_pedidos = ItemPedido.objects.filter(pedido__in=pedidos)
        productos_unicos = items_pedidos.values('producto').distinct().count()
        cantidad_total_items = items_pedidos.aggregate(Sum('cantidad'))['cantidad__sum'] or 0
        
        # Métricas de precio
        ticket_promedio = valor_total / total_pedidos if total_pedidos > 0 else Decimal('0')
        
        precios_productos = items_pedidos.aggregate(
            precio_min=Min('precio_unitario'),
            precio_max=Max('precio_unitario'),
            precio_promedio=Avg('precio_unitario')
        )
        
        # Análisis temporal
        pedidos_por_dia_semana = {}
        pedidos_por_mes = {}
        
        for pedido in pedidos:
            dia_semana = pedido.fecha.weekday()
            mes = pedido.fecha.month
            
            pedidos_por_dia_semana[dia_semana] = pedidos_por_dia_semana.get(dia_semana, 0) + 1
            pedidos_por_mes[mes] = pedidos_por_mes.get(mes, 0) + 1
        
        dia_preferido = max(pedidos_por_dia_semana, key=pedidos_por_dia_semana.get) if pedidos_por_dia_semana else 1
        mes_mayor_actividad = max(pedidos_por_mes, key=pedidos_por_mes.get) if pedidos_por_mes else 1
        
        # Recencia
        dias_desde_ultimo_pedido = (timezone.now().date() - ultimo_pedido.date()).days if ultimo_pedido else 999
        
        # Variabilidad de compras
        valores_pedidos = [float(p.total) for p in pedidos]
        variabilidad_ticket = statistics.stdev(valores_pedidos) if len(valores_pedidos) > 1 else 0
        
        # Crecimiento del cliente
        crecimiento_valor = 0
        if total_pedidos >= 2:
            pedidos_ordenados = pedidos.order_by('fecha')
            primeros_pedidos = list(pedidos_ordenados[:total_pedidos//2])
            ultimos_pedidos = list(pedidos_ordenados[total_pedidos//2:])
            
            valor_periodo_inicial = sum(float(p.total) for p in primeros_pedidos)
            valor_periodo_final = sum(float(p.total) for p in ultimos_pedidos)
            
            if valor_periodo_inicial > 0:
                crecimiento_valor = ((valor_periodo_final - valor_periodo_inicial) / valor_periodo_inicial) * 100
        
        return {
            'cliente_id': cliente_id,
            'total_pedidos': total_pedidos,
            'valor_total': float(valor_total),
            'ticket_promedio': float(ticket_promedio),
            'frecuencia_compra': frecuencia_compra,
            'productos_unicos': productos_unicos,
            'cantidad_total_items': cantidad_total_items,
            'dias_cliente': dias_cliente,
            'dias_desde_ultimo_pedido': dias_desde_ultimo_pedido,
            'precio_promedio': float(precios_productos['precio_promedio'] or 0),
            'precio_min': float(precios_productos['precio_min'] or 0),
            'precio_max': float(precios_productos['precio_max'] or 0),
            'variabilidad_ticket': variabilidad_ticket,
            'dia_preferido': dia_preferido,
            'mes_mayor_actividad': mes_mayor_actividad,
            'crecimiento_valor': crecimiento_valor,
            'pedidos_por_dia_semana': pedidos_por_dia_semana,
            'pedidos_por_mes': pedidos_por_mes,
        }
    
    def _metricas_cliente_nuevo(self, cliente):
        """Métricas por defecto para clientes nuevos"""
        return {
            'cliente_id': cliente.id,
            'total_pedidos': 0,
            'valor_total': 0.0,
            'ticket_promedio': 0.0,
            'frecuencia_compra': 999,
            'productos_unicos': 0,
            'cantidad_total_items': 0,
            'dias_cliente': 0,
            'dias_desde_ultimo_pedido': 999,
            'precio_promedio': 0.0,
            'precio_min': 0.0,
            'precio_max': 0.0,
            'variabilidad_ticket': 0.0,
            'dia_preferido': 1,
            'mes_mayor_actividad': 1,
            'crecimiento_valor': 0.0,
            'pedidos_por_dia_semana': {},
            'pedidos_por_mes': {},
        }
    
    def clasificar_cliente(self, metricas):
        """Clasifica al cliente según sus métricas"""
        if metricas['total_pedidos'] == 0:
            return 'nuevo'
        elif metricas['dias_desde_ultimo_pedido'] > 180:
            return 'inactivo'
        elif metricas['valor_total'] > 5000000 and metricas['total_pedidos'] >= 5:
            return 'premium'
        elif metricas['frecuencia_compra'] <= 30 and metricas['total_pedidos'] >= 3:
            return 'frecuente'
        else:
            return 'ocasional'
    
    def predecir_comportamiento_cliente(self, cliente_id):
        """Predice el comportamiento futuro del cliente"""
        metricas = self.extraer_metricas_cliente(cliente_id)
        
        if not metricas or metricas['total_pedidos'] < 2:
            return {
                'demanda_30dias': 0,
                'demanda_60dias': 0,
                'demanda_90dias': 0,
                'probabilidad_recompra': 0.1,
                'valor_esperado_30dias': 0
            }
        
        # Predicción simple basada en patrones
        frecuencia = metricas['frecuencia_compra']
        ticket_promedio = metricas['ticket_promedio']
        
        # Probabilidad de recompra
        if metricas['dias_desde_ultimo_pedido'] < frecuencia:
            probabilidad_recompra = 0.8
        elif metricas['dias_desde_ultimo_pedido'] < frecuencia * 2:
            probabilidad_recompra = 0.5
        else:
            probabilidad_recompra = 0.2
        
        # Factor de crecimiento
        factor_crecimiento = 1 + (metricas['crecimiento_valor'] / 100)
        factor_crecimiento = max(0.5, min(2.0, factor_crecimiento))
        
        # Predicciones
        pedidos_esperados_30 = (30 / frecuencia) * probabilidad_recompra if frecuencia > 0 else 0
        pedidos_esperados_60 = (60 / frecuencia) * probabilidad_recompra if frecuencia > 0 else 0
        pedidos_esperados_90 = (90 / frecuencia) * probabilidad_recompra if frecuencia > 0 else 0
        
        valor_esperado_30 = pedidos_esperados_30 * ticket_promedio * factor_crecimiento
        
        return {
            'demanda_30dias': max(0, int(pedidos_esperados_30)),
            'demanda_60dias': max(0, int(pedidos_esperados_60)),
            'demanda_90dias': max(0, int(pedidos_esperados_90)),
            'probabilidad_recompra': probabilidad_recompra,
            'valor_esperado_30dias': float(valor_esperado_30),
            'frecuencia_estimada': frecuencia,
            'factor_crecimiento': factor_crecimiento
        }
    
    def analizar_productos_por_cliente(self, cliente_id):
        """Analiza qué productos compra cada cliente"""
        from ventas.models import ItemPedido, Pedido
        
        items = ItemPedido.objects.filter(
            pedido__cliente_id=cliente_id,
            pedido__fecha__gte=timezone.now() - timedelta(days=365)
        ).select_related('producto', 'pedido')
        
        if not items.exists():
            return {}
        
        # Agrupar por producto
        productos_cliente = {}
        for item in items:
            producto_id = item.producto.id
            if producto_id not in productos_cliente:
                productos_cliente[producto_id] = {
                    'producto_nombre': item.producto.nombre,
                    'total_comprado': 0,
                    'veces_comprado': 0,
                    'valor_total': 0,
                    'precio_promedio': 0,
                    'ultima_compra': None,
                    'fechas_compra': []
                }
            
            productos_cliente[producto_id]['total_comprado'] += item.cantidad
            productos_cliente[producto_id]['veces_comprado'] += 1
            productos_cliente[producto_id]['valor_total'] += float(item.cantidad * item.precio_unitario)
            productos_cliente[producto_id]['fechas_compra'].append(item.pedido.fecha)
            
            if (productos_cliente[producto_id]['ultima_compra'] is None or 
                item.pedido.fecha > productos_cliente[producto_id]['ultima_compra']):
                productos_cliente[producto_id]['ultima_compra'] = item.pedido.fecha
        
        # Calcular métricas por producto
        for producto_id, datos in productos_cliente.items():
            datos['precio_promedio'] = datos['valor_total'] / datos['total_comprado']
            
            # Frecuencia de compra del producto
            fechas = sorted(datos['fechas_compra'])
            if len(fechas) > 1:
                intervalos = [(fechas[i+1] - fechas[i]).days for i in range(len(fechas)-1)]
                frecuencia_producto = sum(intervalos) / len(intervalos)
            else:
                frecuencia_producto = 365
            
            datos['frecuencia_compra_dias'] = frecuencia_producto
            
            # Predicción de próxima compra
            if datos['ultima_compra']:
                dias_desde_ultima = (timezone.now() - datos['ultima_compra']).days
                if frecuencia_producto > 0:
                    probabilidad_compra_prox_30d = max(0, min(1, (30 - dias_desde_ultima) / frecuencia_producto))
                else:
                    probabilidad_compra_prox_30d = 0
            else:
                probabilidad_compra_prox_30d = 0
            
            datos['probabilidad_compra_30d'] = probabilidad_compra_prox_30d
            datos['cantidad_predicha_30d'] = int(probabilidad_compra_prox_30d * 
                                                (datos['total_comprado'] / datos['veces_comprado']))
        
        return productos_cliente
    
    def generar_recomendaciones_cliente(self, cliente_id):
        """Genera recomendaciones para el cliente"""
        metricas = self.extraer_metricas_cliente(cliente_id)
        
        if not metricas:
            return []
        
        recomendaciones = []
        
        if metricas['total_pedidos'] == 0:
            recomendaciones.append({
                'tipo': 'cliente_nuevo',
                'mensaje': 'Cliente nuevo - considerar descuento de bienvenida',
                'prioridad': 'alta'
            })
        
        if metricas['dias_desde_ultimo_pedido'] > 60:
            recomendaciones.append({
                'tipo': 'reactivacion',
                'mensaje': f'Cliente inactivo por {metricas["dias_desde_ultimo_pedido"]} días',
                'prioridad': 'alta'
            })
        
        if metricas['valor_total'] > 1000000:
            recomendaciones.append({
                'tipo': 'cliente_vip',
                'mensaje': 'Cliente de alto valor - atención personalizada',
                'prioridad': 'alta'
            })
        
        return recomendaciones