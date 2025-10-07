# inventario/reportes_views.py
# Vistas para reportes, estadísticas y dashboards del módulo de inventario

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse, Http404
from django.db import transaction
from django.db.models import Q, F, Sum, Count, Avg, Max, Min
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
import json

# Importaciones locales
from .models import (
    Producto, Categoria, Subcategoria, PresentacionProducto, MovimientoInventario,
    Stock, Bodega, ProductoProveedor, PresentacionProveedorProducto,
    RecomendacionReposicion
)
from .general_views import AdminInventarioMixin, BodegaMixin

# ========================================
# DASHBOARDS Y REPORTES PRINCIPALES
# ========================================

class DashboardRecomendacionesView(AdminInventarioMixin, TemplateView):
    """Dashboard de recomendaciones con estadísticas y gráficos"""
    template_name = 'inventario/dashboard_recomendaciones.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Recomendaciones activas
        recomendaciones_activas = RecomendacionReposicion.objects.filter(activa=True)
        
        # Estadísticas generales
        context['estadisticas'] = {
            'total_activas': recomendaciones_activas.count(),
            'criticas': recomendaciones_activas.filter(prioridad='critica').count(),
            'urgentes': recomendaciones_activas.filter(prioridad__in=['critica', 'alta']).count(),
            'procesando': recomendaciones_activas.filter(estado='procesando').count(),
            'pendientes': recomendaciones_activas.filter(estado='pendiente').count(),
        }
        
        # Top 10 productos más urgentes
        context['productos_urgentes'] = recomendaciones_activas.filter(
            prioridad__in=['critica', 'alta']
        ).select_related('producto').order_by(
            'prioridad', 'dias_cobertura_actual'
        )[:10]
        
        # Inversión requerida por prioridad
        context['inversion_por_prioridad'] = {}
        for prioridad, _ in RecomendacionReposicion.PRIORIDAD_CHOICES:
            total = recomendaciones_activas.filter(
                prioridad=prioridad,
                valor_total_sugerido__isnull=False
            ).aggregate(total=Sum('valor_total_sugerido'))['total'] or 0
            
            context['inversion_por_prioridad'][prioridad] = {
                'total': total,
                'count': recomendaciones_activas.filter(prioridad=prioridad).count()
            }
        
        # Productos sin stock (críticos)
        context['productos_sin_stock'] = recomendaciones_activas.filter(
            stock_actual=0
        ).select_related('producto').count()
        
        # Tendencias (productos con crecimiento fuerte)
        context['productos_crecimiento'] = recomendaciones_activas.filter(
            tendencia_porcentaje__gte=20
        ).count()
        
        return context


class DashboardInventarioView(AdminInventarioMixin, TemplateView):
    """Dashboard principal de inventario con estadísticas generales"""
    template_name = 'inventario/dashboard_inventario.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas generales de productos
        productos_activos = Producto.objects.filter(activo=True)
        context['estadisticas_productos'] = {
            'total': productos_activos.count(),
            'con_stock': productos_activos.filter(stock_actual__gt=0).count(),
            'sin_stock': productos_activos.filter(stock_actual=0).count(),
            'stock_minimo': productos_activos.filter(
                stock_actual__lte=F('stock_minimo')
            ).count(),
        }
        
        # Estadísticas de movimientos (últimos 30 días)
        fecha_limite = timezone.now() - timedelta(days=30)
        movimientos_recientes = MovimientoInventario.objects.filter(
            fecha_movimiento__gte=fecha_limite
        )
        
        context['estadisticas_movimientos'] = {
            'total_movimientos': movimientos_recientes.count(),
            'entradas': movimientos_recientes.filter(tipo='entrada').count(),
            'salidas': movimientos_recientes.filter(tipo='salida').count(),
            'transferencias': movimientos_recientes.filter(tipo='transferencia').count(),
            'ajustes': movimientos_recientes.filter(tipo='ajuste').count(),
        }
        
        # Valor total del inventario
        valor_total = productos_activos.aggregate(
            total=Sum(F('stock_actual') * F('precio_costo'))
        )['total'] or 0
        context['valor_inventario'] = valor_total
        
        # Top 10 productos con más movimientos
        context['productos_mas_movimiento'] = productos_activos.annotate(
            total_movimientos=Count('movimientoinventario')
        ).order_by('-total_movimientos')[:10]
        
        # Alertas críticas
        context['alertas'] = {
            'productos_sin_stock': productos_activos.filter(stock_actual=0).count(),
            'productos_stock_minimo': productos_activos.filter(
                stock_actual__lte=F('stock_minimo'),
                stock_actual__gt=0
            ).count(),
            'recomendaciones_criticas': RecomendacionReposicion.objects.filter(
                activa=True, prioridad='critica'
            ).count(),
        }
        
        return context


class ReporteInventarioView(AdminInventarioMixin, TemplateView):
    """Vista para generar reportes detallados de inventario"""
    template_name = 'inventario/reporte_inventario.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Parámetros de filtro
        categoria_id = self.request.GET.get('categoria')
        bodega_id = self.request.GET.get('bodega')
        estado_stock = self.request.GET.get('estado_stock')
        
        # Query base
        productos = Producto.objects.filter(activo=True).select_related(
            'categoria', 'subcategoria'
        ).prefetch_related('stockbodega_set__bodega')
        
        # Aplicar filtros
        if categoria_id:
            productos = productos.filter(categoria_id=categoria_id)
        
        if bodega_id:
            productos = productos.filter(stockbodega__bodega_id=bodega_id)
        
        if estado_stock == 'sin_stock':
            productos = productos.filter(stock_actual=0)
        elif estado_stock == 'stock_minimo':
            productos = productos.filter(stock_actual__lte=F('stock_minimo'))
        elif estado_stock == 'con_stock':
            productos = productos.filter(stock_actual__gt=0)
        
        context['productos'] = productos.distinct()
        context['categorias'] = Categoria.objects.filter(activa=True)
        context['bodegas'] = Bodega.objects.filter(activa=True)
        
        # Totales del reporte
        context['totales'] = productos.aggregate(
            total_productos=Count('id'),
            total_stock=Sum('stock_actual'),
            valor_total=Sum(F('stock_actual') * F('precio_costo'))
        )
        
        return context


class ReporteMovimientosView(AdminInventarioMixin, TemplateView):
    """Vista para reportes de movimientos de inventario"""
    template_name = 'inventario/reporte_movimientos.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Parámetros de filtro
        fecha_inicio = self.request.GET.get('fecha_inicio')
        fecha_fin = self.request.GET.get('fecha_fin')
        tipo_movimiento = self.request.GET.get('tipo')
        producto_id = self.request.GET.get('producto')
        bodega_id = self.request.GET.get('bodega')
        
        # Query base
        movimientos = MovimientoInventario.objects.select_related(
            'producto', 'bodega_origen', 'bodega_destino', 'usuario'
        ).order_by('-fecha_movimiento')
        
        # Aplicar filtros
        if fecha_inicio:
            movimientos = movimientos.filter(
                fecha_movimiento__date__gte=fecha_inicio
            )
        
        if fecha_fin:
            movimientos = movimientos.filter(
                fecha_movimiento__date__lte=fecha_fin
            )
        
        if tipo_movimiento:
            movimientos = movimientos.filter(tipo=tipo_movimiento)
        
        if producto_id:
            movimientos = movimientos.filter(producto_id=producto_id)
        
        if bodega_id:
            movimientos = movimientos.filter(
                Q(bodega_origen_id=bodega_id) | Q(bodega_destino_id=bodega_id)
            )
        
        context['movimientos'] = movimientos[:1000]  # Limitar resultados
        context['productos'] = Producto.objects.filter(activo=True)
        context['bodegas'] = Bodega.objects.filter(activa=True)
        
        # Estadísticas del período
        context['estadisticas'] = movimientos.aggregate(
            total_movimientos=Count('id'),
            total_entradas=Count('id', filter=Q(tipo='entrada')),
            total_salidas=Count('id', filter=Q(tipo='salida')),
            total_transferencias=Count('id', filter=Q(tipo='transferencia')),
            total_ajustes=Count('id', filter=Q(tipo='ajuste'))
        )
        
        return context


# ========================================
# FUNCIONES AJAX PARA RECOMENDACIONES
# ========================================

@csrf_exempt 
def generar_recomendaciones_ajax(request):
    """Vista AJAX para generar recomendaciones en tiempo real"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    if not (request.user.is_superuser or 
            request.user.role in ['superadmin', 'administrador']):
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        modo = request.POST.get('modo', 'todos')  # 'todos', 'criticos', 'especifico'
        producto_id = request.POST.get('producto_id')
        forzar = request.POST.get('forzar') == 'true'
        
        recomendaciones_generadas = 0
        productos_analizados = 0
        
        if modo == 'especifico' and producto_id:
            # Analizar producto específico
            try:
                producto = Producto.objects.get(id=producto_id, activo=True)
                productos_analizados = 1
                
                recomendacion = producto.generar_recomendacion_inteligente(forzar=forzar)
                if recomendacion:
                    recomendaciones_generadas = 1
                    
            except Producto.DoesNotExist:
                return JsonResponse({'error': 'Producto no encontrado'}, status=404)
                
        elif modo == 'criticos':
            # Analizar solo productos críticos (sin stock o stock mínimo)
            productos_criticos = Producto.objects.filter(
                activo=True,
                stock_actual__lte=F('stock_minimo')
            )
            
            for producto in productos_criticos:
                productos_analizados += 1
                recomendacion = producto.generar_recomendacion_inteligente(forzar=forzar)
                if recomendacion:
                    recomendaciones_generadas += 1
                    
        else:  # modo == 'todos'
            # Analizar todos los productos activos
            productos = Producto.objects.filter(activo=True)
            
            for producto in productos:
                productos_analizados += 1
                recomendacion = producto.generar_recomendacion_inteligente(forzar=forzar)
                if recomendacion:
                    recomendaciones_generadas += 1
        
        return JsonResponse({
            'success': True,
            'productos_analizados': productos_analizados,
            'recomendaciones_generadas': recomendaciones_generadas,
            'mensaje': f'Se analizaron {productos_analizados} productos y se generaron {recomendaciones_generadas} recomendaciones.'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno: {str(e)}'
        }, status=500)


def estadisticas_movimientos_api(request):
    """API para obtener estadísticas de movimientos para gráficos"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'No autorizado'}, status=401)
    
    try:
        # Parámetros
        dias = int(request.GET.get('dias', 30))
        fecha_limite = timezone.now() - timedelta(days=dias)
        
        # Movimientos por día
        movimientos_por_dia = {}
        for i in range(dias):
            fecha = (timezone.now() - timedelta(days=i)).date()
            count = MovimientoInventario.objects.filter(
                fecha_movimiento__date=fecha
            ).count()
            movimientos_por_dia[fecha.strftime('%Y-%m-%d')] = count
        
        # Movimientos por tipo
        movimientos_por_tipo = MovimientoInventario.objects.filter(
            fecha_movimiento__gte=fecha_limite
        ).values('tipo').annotate(
            count=Count('id')
        ).order_by('tipo')
        
        # Top productos con más movimientos
        top_productos = Producto.objects.filter(
            movimientoinventario__fecha_movimiento__gte=fecha_limite
        ).annotate(
            total_movimientos=Count('movimientoinventario')
        ).order_by('-total_movimientos')[:10]
        
        top_productos_data = [
            {
                'codigo': p.codigo,
                'nombre': p.nombre_mostrar,
                'movimientos': p.total_movimientos
            }
            for p in top_productos
        ]
        
        return JsonResponse({
            'movimientos_por_dia': movimientos_por_dia,
            'movimientos_por_tipo': list(movimientos_por_tipo),
            'top_productos': top_productos_data,
            'periodo_dias': dias
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def estadisticas_inventario_api(request):
    """API para obtener estadísticas generales de inventario"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'No autorizado'}, status=401)
    
    try:
        # Estadísticas por categoría
        stats_categoria = Categoria.objects.filter(activa=True).annotate(
            total_productos=Count('producto', filter=Q(producto__activo=True)),
            total_stock=Sum('producto__stock_actual', filter=Q(producto__activo=True)),
            valor_total=Sum(
                F('producto__stock_actual') * F('producto__precio_costo'),
                filter=Q(producto__activo=True)
            )
        ).order_by('-total_productos')
        
        categorias_data = [
            {
                'nombre': cat.nombre,
                'productos': cat.total_productos or 0,
                'stock': cat.total_stock or 0,
                'valor': float(cat.valor_total or 0)
            }
            for cat in stats_categoria
        ]
        
        # Estadísticas por bodega
        stats_bodega = Bodega.objects.filter(activa=True).annotate(
            total_productos=Count('stockbodega__producto', distinct=True),
            total_stock=Sum('stockbodega__cantidad')
        ).order_by('-total_stock')
        
        bodegas_data = [
            {
                'nombre': bod.nombre,
                'productos': bod.total_productos or 0,
                'stock': bod.total_stock or 0
            }
            for bod in stats_bodega
        ]
        
        # Estado general del inventario
        productos_activos = Producto.objects.filter(activo=True)
        estado_inventario = {
            'total_productos': productos_activos.count(),
            'con_stock': productos_activos.filter(stock_actual__gt=0).count(),
            'sin_stock': productos_activos.filter(stock_actual=0).count(),
            'stock_critico': productos_activos.filter(
                stock_actual__lte=F('stock_minimo'),
                stock_actual__gt=0
            ).count(),
            'valor_total': float(productos_activos.aggregate(
                total=Sum(F('stock_actual') * F('precio_costo'))
            )['total'] or 0)
        }
        
        return JsonResponse({
            'categorias': categorias_data,
            'bodegas': bodegas_data,
            'estado_inventario': estado_inventario
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def recomendaciones_resumen_api(request):
    """API para obtener resumen de recomendaciones activas"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'No autorizado'}, status=401)
    
    try:
        recomendaciones = RecomendacionReposicion.objects.filter(activa=True)
        
        # Resumen por prioridad
        por_prioridad = recomendaciones.values('prioridad').annotate(
            count=Count('id'),
            valor_total=Sum('valor_total_sugerido')
        ).order_by('prioridad')
        
        # Resumen por estado
        por_estado = recomendaciones.values('estado').annotate(
            count=Count('id')
        ).order_by('estado')
        
        # Top 10 productos más urgentes
        urgentes = recomendaciones.filter(
            prioridad__in=['critica', 'alta']
        ).select_related('producto').order_by(
            'prioridad', 'dias_cobertura_actual'
        )[:10]
        
        urgentes_data = [
            {
                'producto': rec.producto.codigo,
                'nombre': rec.producto.nombre_mostrar,
                'prioridad': rec.prioridad,
                'dias_cobertura': rec.dias_cobertura_actual,
                'cantidad_sugerida': rec.cantidad_sugerida,
                'valor_sugerido': float(rec.valor_total_sugerido or 0)
            }
            for rec in urgentes
        ]
        
        return JsonResponse({
            'por_prioridad': list(por_prioridad),
            'por_estado': list(por_estado),
            'productos_urgentes': urgentes_data,
            'total_activas': recomendaciones.count()
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)