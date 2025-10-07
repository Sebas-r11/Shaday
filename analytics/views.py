"""
Vistas del sistema de Analytics e IA
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, TemplateView
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Q, Sum, Avg, Count, F
from django.utils import timezone
from datetime import datetime, timedelta
import json
from decimal import Decimal

from .models import (
    AnalisisVentasCliente, PrediccionDemanda, AnalisisProveedores,
    ParametrosMRP, ReporteAnalisis, EventoInventario
)
from inventario.models import Producto, Proveedor
from ventas.models import Cliente, Pedido
from .ml.predictor_simple import PredictorDemandaSimple as PredictorDemanda
from .ml.analizador_simple import AnalizadorClientesSimple as AnalizadorClientes
from .ml.sistema_mrp import SistemaMRP


def es_admin_o_gerente(user):
    """Verifica si el usuario es admin o gerente"""
    return user.is_superuser or user.groups.filter(name__in=['Administradores', 'Gerentes']).exists()


@login_required
@user_passes_test(es_admin_o_gerente)
def dashboard_analytics(request):
    """Dashboard principal de analytics e IA"""
    
    # Estadísticas generales
    total_productos = Producto.objects.count()
    total_clientes = Cliente.objects.count()
    total_proveedores = Proveedor.objects.count()
    
    # Reportes recientes
    reportes_recientes = ReporteAnalisis.objects.all()[:5]
    
    # Productos con predicciones recientes
    productos_con_predicciones = PrediccionDemanda.objects.select_related('producto').order_by('-fecha_prediccion')[:10]
    
    # Alertas de riesgo
    alertas_riesgo = []
    
    # Productos con alta demanda predicha pero stock bajo
    for pred in productos_con_predicciones:
        if pred.demanda_30dias > pred.producto.stock_total:
            alertas_riesgo.append({
                'tipo': 'stock_insuficiente',
                'mensaje': f'{pred.producto.nombre}: Demanda predicha {pred.demanda_30dias}, stock actual {pred.producto.stock_total}',
                'producto': pred.producto,
                'severidad': 'alta'
            })
    
    context = {
        'total_productos': total_productos,
        'total_clientes': total_clientes,
        'total_proveedores': total_proveedores,
        'reportes_recientes': reportes_recientes,
        'productos_con_predicciones': productos_con_predicciones,
        'alertas_riesgo': alertas_riesgo[:5],  # Máximo 5 alertas
    }
    
    return render(request, 'analytics/dashboard.html', context)


@login_required
@user_passes_test(es_admin_o_gerente)
def prediccion_demanda(request):
    """Vista para predicciones de demanda"""
    
    predictor = PredictorDemanda()
    productos = Producto.objects.all()
    
    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        
        if producto_id:
            try:
                producto = Producto.objects.get(id=producto_id)
                
                # Generar predicción
                predicciones = predictor.predecir_demanda(producto_id)
                metricas_estacionalidad = predictor.calcular_metricas_estacionalidad(producto_id)
                
                if predicciones:
                    # Guardar predicción en base de datos
                    pred_obj, created = PrediccionDemanda.objects.get_or_create(
                        producto=producto,
                        defaults={
                            'demanda_7dias': predicciones.get('demanda_7dias', 0),
                            'demanda_15dias': predicciones.get('demanda_15dias', 0),
                            'demanda_30dias': predicciones.get('demanda_30dias', 0),
                            'demanda_60dias': predicciones.get('demanda_60dias', 0),
                            'demanda_90dias': predicciones.get('demanda_90dias', 0),
                            'precision_modelo': predictor.precision_modelo,
                            'estacionalidad_factor': metricas_estacionalidad.get('factor_estacionalidad', 1.0),
                        }
                    )
                    
                    if not created:
                        # Actualizar predicción existente
                        pred_obj.demanda_7dias = predicciones.get('demanda_7dias', 0)
                        pred_obj.demanda_15dias = predicciones.get('demanda_15dias', 0)
                        pred_obj.demanda_30dias = predicciones.get('demanda_30dias', 0)
                        pred_obj.demanda_60dias = predicciones.get('demanda_60dias', 0)
                        pred_obj.demanda_90dias = predicciones.get('demanda_90dias', 0)
                        pred_obj.precision_modelo = predictor.precision_modelo
                        pred_obj.estacionalidad_factor = metricas_estacionalidad.get('factor_estacionalidad', 1.0)
                        pred_obj.save()
                    
                    messages.success(request, f'Predicción generada para {producto.nombre}')
                    
                    # Retornar JSON si es AJAX
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'predicciones': predicciones,
                            'estacionalidad': metricas_estacionalidad,
                            'precision': predictor.precision_modelo
                        })
                else:
                    messages.error(request, 'No hay suficientes datos para generar predicción')
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': 'Datos insuficientes'})
                        
            except Producto.DoesNotExist:
                messages.error(request, 'Producto no encontrado')
            except Exception as e:
                messages.error(request, f'Error generando predicción: {str(e)}')
    
    # Obtener predicciones existentes
    predicciones_existentes = PrediccionDemanda.objects.select_related('producto').order_by('-fecha_prediccion')
    
    context = {
        'productos': productos,
        'predicciones_existentes': predicciones_existentes,
    }
    
    return render(request, 'analytics/prediccion_demanda.html', context)


@login_required
@user_passes_test(es_admin_o_gerente)
def analisis_clientes(request):
    """Vista para análisis avanzado de clientes"""
    
    analizador = AnalizadorClientes()
    clientes = Cliente.objects.all()
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'analizar_cliente':
            cliente_id = request.POST.get('cliente_id')
            
            if cliente_id:
                try:
                    # Extraer métricas del cliente
                    metricas = analizador.extraer_metricas_cliente(cliente_id)
                    predicciones = analizador.predecir_comportamiento_cliente(cliente_id)
                    productos_cliente = analizador.analizar_productos_por_cliente(cliente_id)
                    recomendaciones = analizador.generar_recomendaciones_cliente(cliente_id)
                    
                    # Guardar análisis en base de datos
                    cliente = Cliente.objects.get(id=cliente_id)
                    
                    # Crear o actualizar análisis para cada producto
                    for producto_id, datos_producto in productos_cliente.items():
                        from inventario.models import Producto
                        producto = Producto.objects.get(id=producto_id)
                        
                        analisis, created = AnalisisVentasCliente.objects.get_or_create(
                            cliente=cliente,
                            producto=producto,
                            defaults={
                                'total_pedidos': datos_producto['veces_comprado'],
                                'cantidad_total_comprada': datos_producto['total_comprado'],
                                'valor_total_comprado': Decimal(str(datos_producto['valor_total'])),
                                'precio_promedio_pagado': Decimal(str(datos_producto['precio_promedio'])),
                                'demanda_predicha_30dias': datos_producto['cantidad_predicha_30d'],
                            }
                        )
                        
                        if not created:
                            analisis.total_pedidos = datos_producto['veces_comprado']
                            analisis.cantidad_total_comprada = datos_producto['total_comprado']
                            analisis.valor_total_comprado = Decimal(str(datos_producto['valor_total']))
                            analisis.precio_promedio_pagado = Decimal(str(datos_producto['precio_promedio']))
                            analisis.demanda_predicha_30dias = datos_producto['cantidad_predicha_30d']
                            analisis.save()
                    
                    messages.success(request, f'Análisis completado para {cliente.nombre}')
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'metricas': metricas,
                            'predicciones': predicciones,
                            'productos': productos_cliente,
                            'recomendaciones': recomendaciones
                        })
                        
                except Exception as e:
                    messages.error(request, f'Error en análisis: {str(e)}')
        
        elif accion == 'segmentar_todos':
            try:
                # Analizar todos los clientes y segmentarlos
                todos_metricas = []
                for cliente in clientes:
                    metricas = analizador.extraer_metricas_cliente(cliente.id)
                    if metricas:
                        todos_metricas.append(metricas)
                
                if todos_metricas:
                    segmentos = analizador.segmentar_clientes(todos_metricas)
                    messages.success(request, f'Segmentación completada para {len(segmentos)} clientes')
                    
                    # Guardar segmentos (podrías crear un modelo para esto)
                    # Por ahora solo mostramos el mensaje
                else:
                    messages.warning(request, 'No hay suficientes datos para segmentación')
                    
            except Exception as e:
                messages.error(request, f'Error en segmentación: {str(e)}')
    
    # Obtener análisis existentes
    analisis_existentes = AnalisisVentasCliente.objects.select_related('cliente', 'producto').order_by('-fecha_analisis')[:20]
    
    context = {
        'clientes': clientes,
        'analisis_existentes': analisis_existentes,
    }
    
    return render(request, 'analytics/analisis_clientes.html', context)


@login_required
@user_passes_test(es_admin_o_gerente)
def sistema_mrp(request):
    """Vista del sistema MRP"""
    
    mrp = SistemaMRP()
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'generar_plan':
            try:
                # Generar plan maestro
                plan_maestro = mrp.generar_plan_maestro_produccion()
                calendario_optimizado = mrp.optimizar_calendario_compras(plan_maestro)
                
                # Guardar reporte
                reporte = ReporteAnalisis.objects.create(
                    tipo_reporte='mrp',
                    titulo=f'Plan MRP - {timezone.now().strftime("%Y-%m-%d %H:%M")}',
                    datos_reporte={
                        'plan_maestro': {
                            'fecha_generacion': plan_maestro['fecha_generacion'].isoformat(),
                            'productos_analizados': len(plan_maestro['productos']),
                            'resumen_costos': {
                                'total_30d': float(plan_maestro['resumen_costos']['total_inversion_30d']),
                                'total_60d': float(plan_maestro['resumen_costos']['total_inversion_60d']),
                                'total_90d': float(plan_maestro['resumen_costos']['total_inversion_90d']),
                            },
                            'alertas': plan_maestro['alertas']
                        },
                        'calendario': calendario_optimizado
                    },
                    recomendaciones=f'Plan generado con {len(plan_maestro["productos"])} productos. Inversión total 90d: ${plan_maestro["resumen_costos"]["total_inversion_90d"]:,.0f}',
                    usuario_generacion=request.user,
                    productos_analizados=len(plan_maestro['productos'])
                )
                
                messages.success(request, f'Plan MRP generado exitosamente. ID: {reporte.id}')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'plan_maestro': plan_maestro,
                        'calendario': calendario_optimizado,
                        'reporte_id': reporte.id
                    })
                    
            except Exception as e:
                messages.error(request, f'Error generando plan MRP: {str(e)}')
        
        elif accion == 'analisis_abc_xyz':
            try:
                clasificacion = mrp.analizar_abc_xyz()
                
                # Guardar reporte ABC-XYZ
                reporte = ReporteAnalisis.objects.create(
                    tipo_reporte='inventario',
                    titulo=f'Análisis ABC-XYZ - {timezone.now().strftime("%Y-%m-%d %H:%M")}',
                    datos_reporte={'clasificacion_abc_xyz': clasificacion},
                    recomendaciones=f'Clasificación ABC-XYZ completada con {sum(len(productos) for productos in clasificacion.values())} productos',
                    usuario_generacion=request.user,
                    productos_analizados=sum(len(productos) for productos in clasificacion.values())
                )
                
                messages.success(request, f'Análisis ABC-XYZ completado. ID: {reporte.id}')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'clasificacion': clasificacion,
                        'reporte_id': reporte.id
                    })
                    
            except Exception as e:
                messages.error(request, f'Error en análisis ABC-XYZ: {str(e)}')
    
    # Obtener reportes MRP recientes
    reportes_mrp = ReporteAnalisis.objects.filter(
        tipo_reporte__in=['mrp', 'inventario']
    ).order_by('-fecha_generacion')[:10]
    
    context = {
        'reportes_mrp': reportes_mrp,
    }
    
    return render(request, 'analytics/sistema_mrp.html', context)


@login_required
@user_passes_test(es_admin_o_gerente)
def reportes_analytics(request):
    """Vista para ver reportes generados"""
    
    reportes = ReporteAnalisis.objects.all().order_by('-fecha_generacion')
    
    # Filtros
    tipo_filtro = request.GET.get('tipo')
    if tipo_filtro:
        reportes = reportes.filter(tipo_reporte=tipo_filtro)
    
    context = {
        'reportes': reportes,
        'tipo_filtro': tipo_filtro,
        'tipos_reporte': ReporteAnalisis.TIPO_REPORTE_CHOICES,
    }
    
    return render(request, 'analytics/reportes.html', context)


@login_required
@user_passes_test(es_admin_o_gerente)
def detalle_reporte(request, reporte_id):
    """Vista detalle de un reporte específico"""
    
    reporte = get_object_or_404(ReporteAnalisis, id=reporte_id)
    
    context = {
        'reporte': reporte,
    }
    
    return render(request, 'analytics/detalle_reporte.html', context)


@login_required
@user_passes_test(es_admin_o_gerente)
def estadisticas_masivas(request):
    """Vista para estadísticas masivas del sistema"""
    
    # Estadísticas de ventas por cliente
    fecha_inicio = timezone.now() - timedelta(days=365)
    
    # Top clientes por valor
    top_clientes_valor = Cliente.objects.annotate(
        total_comprado=Sum('pedido__total', filter=Q(pedido__fecha_creacion__gte=fecha_inicio))
    ).exclude(total_comprado__isnull=True).order_by('-total_comprado')[:20]
    
    # Top clientes por frecuencia
    top_clientes_frecuencia = Cliente.objects.annotate(
        total_pedidos=Count('pedido', filter=Q(pedido__fecha_creacion__gte=fecha_inicio))
    ).exclude(total_pedidos=0).order_by('-total_pedidos')[:20]
    
    # Productos más vendidos
    productos_top_ventas = EventoInventario.objects.filter(
        tipo_evento='venta',
        fecha_evento__gte=fecha_inicio
    ).values('producto__nombre').annotate(
        total_vendido=Sum('cantidad'),
        valor_total=Sum(F('cantidad') * F('precio_unitario'))
    ).order_by('-total_vendido')[:20]
    
    # Estadísticas por mes
    estadisticas_mensuales = []
    for i in range(12):
        mes_inicio = fecha_inicio + timedelta(days=i*30)
        mes_fin = mes_inicio + timedelta(days=30)
        
        ventas_mes = EventoInventario.objects.filter(
            tipo_evento='venta',
            fecha_evento__gte=mes_inicio,
            fecha_evento__lt=mes_fin
        ).aggregate(
            total_ventas=Sum('cantidad'),
            valor_ventas=Sum(F('cantidad') * F('precio_unitario'))
        )
        
        estadisticas_mensuales.append({
            'mes': mes_inicio.strftime('%Y-%m'),
            'total_ventas': ventas_mes['total_ventas'] or 0,
            'valor_ventas': float(ventas_mes['valor_ventas'] or 0)
        })
    
    # Estadísticas generales para el dashboard
    from inventario.models import Categoria
    
    # Calcular métricas principales
    total_ventas = EventoInventario.objects.filter(
        tipo_evento='venta',
        fecha_evento__gte=fecha_inicio
    ).aggregate(
        total=Sum(F('cantidad') * F('precio_unitario'))
    )['total'] or 0
    
    total_pedidos = Pedido.objects.filter(fecha_creacion__gte=fecha_inicio).count()
    
    clientes_activos = Cliente.objects.filter(
        pedido__fecha_creacion__gte=fecha_inicio
    ).distinct().count()
    
    productos_vendidos = EventoInventario.objects.filter(
        tipo_evento='venta',
        fecha_evento__gte=fecha_inicio
    ).aggregate(
        total=Sum('cantidad')
    )['total'] or 0
    
    # Calcular métricas adicionales - Convertir a float para evitar errores Decimal
    ticket_promedio = float(total_ventas) / total_pedidos if total_pedidos > 0 else 0
    
    # Crecimiento (comparar con período anterior)
    fecha_periodo_anterior = fecha_inicio - timedelta(days=365)
    
    ventas_periodo_anterior = EventoInventario.objects.filter(
        tipo_evento='venta',
        fecha_evento__gte=fecha_periodo_anterior,
        fecha_evento__lt=fecha_inicio
    ).aggregate(
        total=Sum(F('cantidad') * F('precio_unitario'))
    )['total'] or 1
    
    # Convertir a float para cálculos
    ventas_periodo_anterior_float = float(ventas_periodo_anterior) if ventas_periodo_anterior else 1
    total_ventas_float = float(total_ventas) if total_ventas else 0
    
    crecimiento_ventas = ((total_ventas_float - ventas_periodo_anterior_float) / ventas_periodo_anterior_float) * 100 if ventas_periodo_anterior_float > 0 else 0
    
    pedidos_periodo_anterior = Pedido.objects.filter(
        fecha_creacion__gte=fecha_periodo_anterior,
        fecha_creacion__lt=fecha_inicio
    ).count()
    
    crecimiento_pedidos = ((total_pedidos - pedidos_periodo_anterior) / pedidos_periodo_anterior) * 100 if pedidos_periodo_anterior > 0 else 0
    
    clientes_periodo_anterior = Cliente.objects.filter(
        pedido__fecha_creacion__gte=fecha_periodo_anterior,
        pedido__fecha_creacion__lt=fecha_inicio
    ).distinct().count()
    
    crecimiento_clientes = ((clientes_activos - clientes_periodo_anterior) / clientes_periodo_anterior) * 100 if clientes_periodo_anterior > 0 else 0
    
    # Ticket promedio período anterior - Convertir a float
    ticket_periodo_anterior = ventas_periodo_anterior_float / pedidos_periodo_anterior if pedidos_periodo_anterior > 0 else 1
    crecimiento_ticket = ((ticket_promedio - ticket_periodo_anterior) / ticket_periodo_anterior) * 100 if ticket_periodo_anterior > 0 else 0
    
    # Frecuencia de compra promedio
    frecuencia_compra = 30  # Días promedio entre compras (estimado)
    mejora_frecuencia = 5   # Mejora en días (estimado)
    
    rotacion_promedio = 4.5  # Rotación promedio de inventario
    
    # Generar datos para heatmap (últimas 7 semanas)
    heatmap_data = []
    for i in range(49):  # 7x7 grid
        fecha_dia = timezone.now() - timedelta(days=i)
        ventas_dia = EventoInventario.objects.filter(
            tipo_evento='venta',
            fecha_evento__date=fecha_dia.date()
        ).count()
        
        # Determinar intensidad
        if ventas_dia == 0:
            intensity = 'low'
        elif ventas_dia < 5:
            intensity = 'medium'
        else:
            intensity = 'high'
            
        heatmap_data.append({
            'date': fecha_dia,
            'sales': ventas_dia,
            'intensity': intensity
        })
    
    # Top productos por rentabilidad
    top_productos = []
    for producto_data in productos_top_ventas[:10]:
        # Simular datos de rentabilidad
        ventas_totales = float(producto_data['valor_total'] or 0)
        margen = 25.5  # Porcentaje promedio
        roi = 2.3      # ROI promedio
        
        top_productos.append({
            'nombre': producto_data['producto__nombre'],
            'ventas_totales': ventas_totales,
            'margen': margen,
            'roi': roi
        })
    
    # Análisis por segmentos (simulado)
    # Usar las variables float ya definidas anteriormente
    ticket_promedio_float = float(ticket_promedio) if ticket_promedio else 0
    
    segmentos_analisis = [
        {
            'nombre': 'VIP',
            'cantidad_clientes': clientes_activos // 10,
            'ventas_totales': total_ventas_float * 0.4,
            'ticket_promedio': ticket_promedio_float * 1.5,
            'frecuencia_promedio': 15,
            'ltv': ticket_promedio_float * 8,
            'participacion': 40
        },
        {
            'nombre': 'Premium', 
            'cantidad_clientes': clientes_activos // 4,
            'ventas_totales': total_ventas_float * 0.35,
            'ticket_promedio': ticket_promedio_float * 1.2,
            'frecuencia_promedio': 25,
            'ltv': ticket_promedio_float * 5,
            'participacion': 35
        },
        {
            'nombre': 'Regular',
            'cantidad_clientes': clientes_activos // 2,
            'ventas_totales': total_ventas_float * 0.25,
            'ticket_promedio': ticket_promedio_float,
            'frecuencia_promedio': 45,
            'ltv': ticket_promedio_float * 3,
            'participacion': 25
        }
    ]
    
    context = {
        # Datos originales
        'top_clientes_valor': top_clientes_valor,
        'top_clientes_frecuencia': top_clientes_frecuencia,
        'productos_top_ventas': productos_top_ventas,
        'estadisticas_mensuales': estadisticas_mensuales,
        'fecha_inicio': fecha_inicio,
        
        # Métricas principales
        'total_ventas': total_ventas,
        'total_pedidos': total_pedidos,
        'clientes_activos': clientes_activos,
        'productos_vendidos': productos_vendidos,
        'ticket_promedio': ticket_promedio,
        'frecuencia_compra': frecuencia_compra,
        'mejora_frecuencia': mejora_frecuencia,
        'rotacion_promedio': rotacion_promedio,
        
        # Crecimientos
        'crecimiento_ventas': crecimiento_ventas,
        'crecimiento_pedidos': crecimiento_pedidos,
        'crecimiento_clientes': crecimiento_clientes,
        'crecimiento_ticket': crecimiento_ticket,
        
        # Datos para visualizaciones
        'heatmap_data': heatmap_data,
        'top_productos': top_productos,
        'segmentos_analisis': segmentos_analisis,
        
        # Categorías para filtros
        'categorias': Categoria.objects.all(),
        
        # Métricas adicionales
        'total_eventos_procesados': EventoInventario.objects.count(),
        'patrones_detectados': 147,  # Simulado
        'precision_promedio': 94.7,  # Simulado
    }
    
    return render(request, 'analytics/estadisticas_masivas.html', context)


@login_required
@user_passes_test(es_admin_o_gerente)
def api_prediccion_producto(request, producto_id):
    """API endpoint para obtener predicción de un producto específico"""
    
    if request.method == 'GET':
        try:
            prediccion = PrediccionDemanda.objects.filter(producto_id=producto_id).first()
            
            if prediccion:
                data = {
                    'producto_id': producto_id,
                    'producto_nombre': prediccion.producto.nombre,
                    'demanda_7dias': prediccion.demanda_7dias,
                    'demanda_30dias': prediccion.demanda_30dias,
                    'demanda_60dias': prediccion.demanda_60dias,
                    'demanda_90dias': prediccion.demanda_90dias,
                    'precision_modelo': prediccion.precision_modelo,
                    'fecha_prediccion': prediccion.fecha_prediccion.isoformat(),
                    'stock_actual': prediccion.producto.stock_total,
                    'stock_minimo': prediccion.producto.stock_minimo,
                    'riesgo_desabastecimiento': prediccion.riesgo_desabastecimiento,
                }
                
                return JsonResponse({'success': True, 'data': data})
            else:
                return JsonResponse({'success': False, 'error': 'No hay predicción para este producto'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})