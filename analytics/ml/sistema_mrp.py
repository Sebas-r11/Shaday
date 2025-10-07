"""
Sistema MRP (Material Requirements Planning) con IA
Planificación avanzada de requerimientos de materiales
"""

from datetime import datetime, timedelta
from django.db.models import Q, Sum, Avg, Count, F
from django.utils import timezone
from decimal import Decimal
from collections import defaultdict
import json


class SistemaMRP:
    """
    Sistema inteligente de planificación de requerimientos de materiales
    """
    
    def __init__(self):
        self.horizontes_planificacion = {
            'corto_plazo': 30,    # 1 mes
            'mediano_plazo': 90,  # 3 meses
            'largo_plazo': 365    # 1 año
        }
        
    def calcular_requerimientos_netos(self, producto_id):
        """
        Calcula los requerimientos netos del producto usando lógica MRP
        """
        from inventario.models import Producto
        from analytics.ml.predictor_demanda import PredictorDemanda
        
        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            return None
        
        # Obtener predicción de demanda
        predictor = PredictorDemanda()
        predicciones = predictor.predecir_demanda(producto_id)
        
        if not predicciones:
            predicciones = self._prediccion_fallback(producto)
        
        # Stock actual y en tránsito
        stock_actual = producto.stock_total
        stock_en_transito = self._calcular_stock_en_transito(producto)
        stock_comprometido = self._calcular_stock_comprometido(producto)
        
        # Cálculo de requerimientos netos por período
        requerimientos = {}
        
        for periodo in ['7dias', '30dias', '60dias', '90dias']:
            demanda_bruta = predicciones.get(f'demanda_{periodo}', 0)
            
            # Disponible = Stock actual + En tránsito - Comprometido
            disponible = stock_actual + stock_en_transito - stock_comprometido
            
            # Requerimiento neto = Demanda bruta - Disponible + Stock seguridad
            stock_seguridad = max(producto.stock_minimo, int(demanda_bruta * 0.2))  # 20% de la demanda
            requerimiento_neto = max(0, demanda_bruta - disponible + stock_seguridad)
            
            # Lote económico de compra
            lote_economico = self._calcular_lote_economico(producto, requerimiento_neto)
            
            requerimientos[periodo] = {
                'demanda_bruta': demanda_bruta,
                'stock_disponible': disponible,
                'stock_seguridad': stock_seguridad,
                'requerimiento_neto': requerimiento_neto,
                'lote_sugerido': lote_economico,
                'costo_estimado': lote_economico * (producto.proveedor_preferido.precio_compra if producto.proveedor_preferido else 0)
            }
        
        return requerimientos
    
    def _calcular_stock_en_transito(self, producto):
        """
        Calcula el stock que está en tránsito (órdenes de compra pendientes)
        """
        from inventario.models import ItemOrdenCompraStock
        
        stock_en_transito = ItemOrdenCompraStock.objects.filter(
            producto=producto,
            orden_compra__estado__in=['borrador', 'enviada', 'confirmada']
        ).aggregate(
            total=Sum('cantidad_solicitada')
        )['total'] or 0
        
        return stock_en_transito
    
    def _calcular_stock_comprometido(self, producto):
        """
        Calcula el stock comprometido (pedidos de venta pendientes)
        """
        from ventas.models import ItemPedido
        
        stock_comprometido = ItemPedido.objects.filter(
            producto=producto,
            pedido__estado__in=['borrador', 'enviado', 'proceso']
        ).aggregate(
            total=Sum('cantidad')
        )['total'] or 0
        
        return stock_comprometido
    
    def _calcular_lote_economico(self, producto, demanda_anual):
        """
        Calcula el lote económico de compra (EOQ)
        """
        if demanda_anual <= 0:
            return producto.stock_minimo
        
        # Parámetros para EOQ
        costo_pedido = 50000  # Costo fijo por pedido
        costo_almacenamiento = 0.25  # 25% anual del valor del inventario
        
        if producto.proveedor_preferido:
            precio_unitario = float(producto.proveedor_preferido.precio_compra)
        else:
            precio_unitario = 10000  # Valor por defecto
        
        # Fórmula EOQ: sqrt((2 * D * S) / (H * C))
        # D = demanda anual, S = costo pedido, H = tasa almacenamiento, C = costo unitario
        try:
            eoq = ((2 * demanda_anual * costo_pedido) / (costo_almacenamiento * precio_unitario)) ** 0.5
            return max(int(eoq), producto.stock_minimo)
        except:
            return producto.stock_minimo
    
    def _prediccion_fallback(self, producto):
        """
        Predicción básica cuando no hay datos suficientes para ML
        """
        # Usar promedio de ventas históricas si está disponible
        from analytics.models import EventoInventario
        
        fecha_inicio = timezone.now() - timedelta(days=90)
        ventas_recientes = EventoInventario.objects.filter(
            producto=producto,
            tipo_evento='venta',
            fecha_evento__gte=fecha_inicio
        ).aggregate(
            total=Sum('cantidad')
        )['total'] or 0
        
        # Extrapolar a diferentes períodos
        ventas_diarias = ventas_recientes / 90 if ventas_recientes > 0 else 1
        
        return {
            'demanda_7dias': int(ventas_diarias * 7),
            'demanda_30dias': int(ventas_diarias * 30),
            'demanda_60dias': int(ventas_diarias * 60),
            'demanda_90dias': int(ventas_diarias * 90)
        }
    
    def generar_plan_maestro_produccion(self, productos_ids=None):
        """
        Genera un plan maestro de producción/compras
        """
        from inventario.models import Producto
        
        if productos_ids:
            productos = Producto.objects.filter(id__in=productos_ids)
        else:
            # Productos con stock crítico o bajo
            productos = Producto.productos_con_alerta_stock()
        
        plan_maestro = {
            'fecha_generacion': timezone.now(),
            'productos': [],
            'resumen_costos': {
                'total_inversion_30d': Decimal('0'),
                'total_inversion_60d': Decimal('0'),
                'total_inversion_90d': Decimal('0'),
            },
            'alertas': []
        }
        
        for producto in productos:
            requerimientos = self.calcular_requerimientos_netos(producto.id)
            
            if requerimientos:
                producto_plan = {
                    'producto_id': producto.id,
                    'producto_nombre': producto.nombre,
                    'stock_actual': producto.stock_total,
                    'stock_minimo': producto.stock_minimo,
                    'requerimientos': requerimientos,
                    'prioridad': self._calcular_prioridad_producto(producto, requerimientos),
                    'recomendaciones': self._generar_recomendaciones_producto(producto, requerimientos)
                }
                
                plan_maestro['productos'].append(producto_plan)
                
                # Acumular costos
                plan_maestro['resumen_costos']['total_inversion_30d'] += requerimientos['30dias']['costo_estimado']
                plan_maestro['resumen_costos']['total_inversion_60d'] += requerimientos['60dias']['costo_estimado']
                plan_maestro['resumen_costos']['total_inversion_90d'] += requerimientos['90dias']['costo_estimado']
                
                # Generar alertas si es necesario
                if producto_plan['prioridad'] == 'critica':
                    plan_maestro['alertas'].append({
                        'tipo': 'stock_critico',
                        'producto': producto.nombre,
                        'mensaje': f'Stock crítico: {producto.stock_total} unidades (mínimo: {producto.stock_minimo})'
                    })
        
        # Ordenar por prioridad
        plan_maestro['productos'].sort(key=lambda x: {'critica': 3, 'alta': 2, 'media': 1, 'baja': 0}[x['prioridad']], reverse=True)
        
        return plan_maestro
    
    def _calcular_prioridad_producto(self, producto, requerimientos):
        """
        Calcula la prioridad del producto basado en múltiples factores
        """
        # Factor de stock crítico
        ratio_stock = producto.stock_total / max(producto.stock_minimo, 1)
        
        # Factor de demanda
        demanda_30d = requerimientos['30dias']['demanda_bruta']
        
        # Factor de valor económico
        valor_producto = float(producto.proveedor_preferido.precio_compra) if producto.proveedor_preferido else 0
        
        if ratio_stock < 0.5:  # Stock muy bajo
            return 'critica'
        elif ratio_stock < 1.0 or demanda_30d > producto.stock_total:  # Stock bajo o alta demanda
            return 'alta'
        elif demanda_30d > 0 or valor_producto > 100000:  # Hay demanda o producto costoso
            return 'media'
        else:
            return 'baja'
    
    def _generar_recomendaciones_producto(self, producto, requerimientos):
        """
        Genera recomendaciones específicas para el producto
        """
        recomendaciones = []
        
        req_30d = requerimientos['30dias']
        
        # Recomendación de compra urgente
        if req_30d['requerimiento_neto'] > 0:
            recomendaciones.append({
                'tipo': 'compra_urgente',
                'mensaje': f'Comprar {req_30d["lote_sugerido"]} unidades en los próximos 7 días',
                'cantidad': req_30d['lote_sugerido'],
                'costo': req_30d['costo_estimado']
            })
        
        # Recomendación de stock de seguridad
        if producto.stock_total < req_30d['stock_seguridad']:
            deficit_seguridad = req_30d['stock_seguridad'] - producto.stock_total
            recomendaciones.append({
                'tipo': 'stock_seguridad',
                'mensaje': f'Incrementar stock de seguridad en {deficit_seguridad} unidades',
                'cantidad': deficit_seguridad
            })
        
        # Recomendación de proveedor alternativo si hay riesgo
        if not producto.proveedor_preferido:
            recomendaciones.append({
                'tipo': 'proveedor_faltante',
                'mensaje': 'Asignar proveedor preferido para optimizar compras'
            })
        
        return recomendaciones
    
    def optimizar_calendario_compras(self, plan_maestro):
        """
        Optimiza el calendario de compras para minimizar costos
        """
        from collections import defaultdict
        
        calendario = defaultdict(list)
        
        for producto_plan in plan_maestro['productos']:
            producto_id = producto_plan['producto_id']
            reqs = producto_plan['requerimientos']
            
            # Programar compras basado en lead time y urgencia
            if producto_plan['prioridad'] in ['critica', 'alta']:
                # Compra inmediata
                calendario['semana_1'].append({
                    'producto_id': producto_id,
                    'producto': producto_plan['producto_nombre'],
                    'cantidad': reqs['30dias']['lote_sugerido'],
                    'costo': reqs['30dias']['costo_estimado'],
                    'urgencia': producto_plan['prioridad']
                })
            elif reqs['30dias']['requerimiento_neto'] > 0:
                # Compra en 2 semanas
                calendario['semana_2'].append({
                    'producto_id': producto_id,
                    'producto': producto_plan['producto_nombre'],
                    'cantidad': reqs['30dias']['lote_sugerido'],
                    'costo': reqs['30dias']['costo_estimado'],
                    'urgencia': producto_plan['prioridad']
                })
        
        # Agrupar por proveedor para optimizar órdenes
        calendario_optimizado = {}
        for semana, compras in calendario.items():
            proveedores = defaultdict(list)
            
            for compra in compras:
                # Buscar proveedor del producto
                from inventario.models import Producto
                try:
                    producto = Producto.objects.get(id=compra['producto_id'])
                    proveedor_nombre = producto.proveedor_preferido.proveedor.nombre if producto.proveedor_preferido else 'Sin proveedor'
                    proveedores[proveedor_nombre].append(compra)
                except:
                    proveedores['Sin proveedor'].append(compra)
            
            calendario_optimizado[semana] = dict(proveedores)
        
        return calendario_optimizado
    
    def analizar_abc_xyz(self):
        """
        Análisis ABC-XYZ para clasificar productos por valor e irregularidad
        """
        from inventario.models import Producto
        from analytics.models import EventoInventario
        
        productos_con_datos = []
        fecha_inicio = timezone.now() - timedelta(days=365)
        
        for producto in Producto.objects.all():
            # Calcular valor anual (A,B,C)
            ventas = EventoInventario.objects.filter(
                producto=producto,
                tipo_evento='venta',
                fecha_evento__gte=fecha_inicio
            )
            
            if ventas.exists():
                valor_anual = sum(float(v.cantidad * v.precio_unitario) for v in ventas)
                cantidad_total = sum(v.cantidad for v in ventas)
                
                # Calcular variabilidad (X,Y,Z)
                ventas_mensuales = []
                for mes in range(12):
                    inicio_mes = fecha_inicio + timedelta(days=mes*30)
                    fin_mes = inicio_mes + timedelta(days=30)
                    
                    ventas_mes = EventoInventario.objects.filter(
                        producto=producto,
                        tipo_evento='venta',
                        fecha_evento__gte=inicio_mes,
                        fecha_evento__lt=fin_mes
                    ).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
                    
                    ventas_mensuales.append(ventas_mes)
                
                # Coeficiente de variación
                if len(ventas_mensuales) > 1 and sum(ventas_mensuales) > 0:
                    import statistics
                    cv = statistics.stdev(ventas_mensuales) / (statistics.mean(ventas_mensuales) + 0.01)
                else:
                    cv = 0
                
                productos_con_datos.append({
                    'producto': producto,
                    'valor_anual': valor_anual,
                    'cantidad_anual': cantidad_total,
                    'coef_variacion': cv
                })
        
        if not productos_con_datos:
            return {}
        
        # Clasificar por valor (ABC)
        productos_con_datos.sort(key=lambda x: x['valor_anual'], reverse=True)
        total_productos = len(productos_con_datos)
        
        # Clasificar por variabilidad (XYZ)  
        for i, item in enumerate(productos_con_datos):
            # Clasificación ABC (por valor)
            if i < total_productos * 0.2:  # Top 20%
                item['clase_abc'] = 'A'
            elif i < total_productos * 0.5:  # Next 30%
                item['clase_abc'] = 'B'
            else:  # Bottom 50%
                item['clase_abc'] = 'C'
            
            # Clasificación XYZ (por variabilidad)
            cv = item['coef_variacion']
            if cv < 0.5:  # Baja variabilidad
                item['clase_xyz'] = 'X'
            elif cv < 1.0:  # Media variabilidad
                item['clase_xyz'] = 'Y'
            else:  # Alta variabilidad
                item['clase_xyz'] = 'Z'
            
            item['clasificacion'] = f"{item['clase_abc']}{item['clase_xyz']}"
        
        # Agrupar por clasificación
        clasificacion_abc_xyz = defaultdict(list)
        for item in productos_con_datos:
            clasificacion_abc_xyz[item['clasificacion']].append({
                'producto_id': item['producto'].id,
                'producto_nombre': item['producto'].nombre,
                'valor_anual': item['valor_anual'],
                'cantidad_anual': item['cantidad_anual'],
                'variabilidad': item['coef_variacion']
            })
        
        return dict(clasificacion_abc_xyz)