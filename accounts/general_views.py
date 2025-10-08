"""
Vistas generales del módulo accounts - Dashboard principal y funciones de apoyo
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
def optimizar_ruta(request):
    """Vista placeholder para optimizar ruta. No modifica modelos."""
    return HttpResponse("Optimización de ruta (placeholder)")
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta

from inventario.models import Producto, Stock, MovimientoInventario
from ventas.models import Pedido, Cotizacion, Cliente, Entrega
from .models import User

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/dashboard.html'
    
    def get_template_names(self):
        """Seleccionar template específico según el rol del usuario"""
        if self.request.user.role == 'repartidor':
            return ['accounts/dashboard_repartidor.html']
        return [self.template_name]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Configuración base de permisos
        context['user_role'] = user.role
        context['user_permissions'] = {
            'can_manage_users': user.can_manage_users(),
            'can_see_costs': user.can_see_costs(),
            'can_adjust_inventory': user.can_adjust_inventory(),
            'can_access_crm': user.can_access_crm(),
            'can_create_sales': user.can_create_sales(),
            'can_prepare_orders': user.can_prepare_orders(),
            'can_deliver_orders': user.can_deliver_orders(),
        }
        
        # Dashboard personalizado por rol
        if user.role == 'vendedor':
            # Dashboard para vendedores - solo sus ventas
            context.update(self.get_vendedor_dashboard_data(user))
        elif user.role == 'bodega':
            # Dashboard para bodegueros - inventario y pedidos asignados
            context.update(self.get_bodeguero_dashboard_data(user))
        elif user.role == 'repartidor':
            # Dashboard para repartidores - entregas y rutas
            context.update(self.get_repartidor_dashboard_data(user))
        else:
            # Dashboard para administradores - vista completa
            context.update(self.get_admin_dashboard_data(user))
        
        return context
    
    def get_vendedor_dashboard_data(self, user):
        """Dashboard personalizado para vendedores"""
        hoy = timezone.now().date()
        mes_actual = hoy.replace(day=1)
        
        # Como los modelos no tienen campo vendedor, mostramos todos los pedidos/cotizaciones
        # En el futuro se puede filtrar por cliente asignado al vendedor
        todos_pedidos = Pedido.objects.all()
        todas_cotizaciones = Cotizacion.objects.all()
        
        # Estadísticas de ventas del mes actual
        pedidos_mes = todos_pedidos.filter(fecha_creacion__gte=mes_actual)
        cotizaciones_mes = todas_cotizaciones.filter(fecha_creacion__gte=mes_actual)
        
        # Ventas del día
        pedidos_hoy = todos_pedidos.filter(fecha_creacion__date=hoy)
        ventas_hoy = sum(pedido.total for pedido in pedidos_hoy if pedido.total)
        
        # Ventas del mes
        ventas_mes = sum(pedido.total for pedido in pedidos_mes if pedido.total)
        
        # Pedidos por estado
        pedidos_por_estado = {
            'borrador': todos_pedidos.filter(estado='borrador').count(),
            'enviado': todos_pedidos.filter(estado='enviado').count(),
            'en_proceso': todos_pedidos.filter(estado='en_proceso').count(),
            'completado': todos_pedidos.filter(estado='completado').count(),
            'entregado': todos_pedidos.filter(estado='entregado').count(),
        }
        
        return {
            'total_productos': Producto.objects.filter(activo=True).count(),
            'mis_pedidos_total': todos_pedidos.count(),
            'mis_cotizaciones_total': todas_cotizaciones.count(),
            'ventas_hoy': ventas_hoy,
            'ventas_mes': ventas_mes,
            'pedidos_hoy': pedidos_hoy.count(),
            'pedidos_mes': pedidos_mes.count(),
            'cotizaciones_mes': cotizaciones_mes.count(),
            'pedidos_por_estado': pedidos_por_estado,
            'pedidos_recientes': todos_pedidos.order_by('-fecha_creacion')[:5],
            'cotizaciones_recientes': todas_cotizaciones.order_by('-fecha_creacion')[:5],
            # No mostrar productos bajo stock para vendedores
            'productos_bajo_stock': [],
            'is_vendedor_dashboard': True,
        }
    
    def get_bodeguero_dashboard_data(self, user):
        """Dashboard personalizado para bodegueros"""
        # Todos los pedidos que necesitan alistamiento
        pedidos_pendientes_alistamiento = Pedido.objects.filter(
            estado__in=['borrador', 'enviado']
        )
        
        # Todos los pedidos (sin asignación específica ya que el modelo no tiene este campo)
        todos_pedidos = Pedido.objects.all()
        
        return {
            'total_productos': Producto.objects.filter(activo=True).count(),
            'productos_bajo_stock': [],  # Los bodegueros no ven alertas de stock
            'pedidos_asignados': todos_pedidos.count(),
            'pedidos_pendientes_alistamiento': pedidos_pendientes_alistamiento.count(),
            'pedidos_recientes': pedidos_pendientes_alistamiento.order_by('-fecha_creacion')[:10],
            'movimientos_recientes': MovimientoInventario.objects.filter(
                usuario=user
            ).select_related('producto', 'bodega').order_by('-fecha_movimiento')[:10] if hasattr(MovimientoInventario, 'usuario') else [],
            'is_bodeguero_dashboard': True,
        }
    
    def get_repartidor_dashboard_data(self, user):
        """Dashboard especializado para repartidores - solo entregas y rutas"""
        hoy = timezone.now().date()
        
        # Entregas asignadas al repartidor
        entregas_asignadas = Entrega.objects.filter(repartidor=user)
        entregas_hoy = entregas_asignadas.filter(fecha_programada=hoy)
        entregas_pendientes = entregas_asignadas.filter(estado='programada')
        entregas_en_camino = entregas_asignadas.filter(estado='en_camino')
        
        # Entregas para generar ruta optimizada
        entregas_para_ruta = entregas_asignadas.filter(
            estado__in=['programada', 'en_camino'],
            fecha_programada=hoy
        ).select_related('pedido', 'pedido__cliente')
        
        # Estadísticas del repartidor
        total_entregas_realizadas = entregas_asignadas.filter(estado='entregado').count()
        entregas_fallidas = entregas_asignadas.filter(estado='fallido').count()
        
        return {
            'entregas_hoy': entregas_hoy.count(),
            'entregas_pendientes': entregas_pendientes.count(),
            'entregas_en_camino': entregas_en_camino.count(),
            'total_entregas_realizadas': total_entregas_realizadas,
            'entregas_fallidas': entregas_fallidas,
            'entregas_para_ruta': entregas_para_ruta,
            'entregas_recientes': entregas_asignadas.order_by('-fecha_programada')[:10],
            'is_repartidor_dashboard': True,
        }
    
    def get_admin_dashboard_data(self, user):
        """Dashboard completo para administradores"""
        hoy = timezone.now().date()
        
        # Ventas del día (todos los pedidos)
        pedidos_hoy = Pedido.objects.filter(fecha_creacion__date=hoy)
        ventas_hoy = sum(pedido.total for pedido in pedidos_hoy if pedido.total)
        
        return {
            'total_productos': Producto.objects.filter(activo=True).count(),
            'productos_bajo_stock': self.get_productos_bajo_stock(),
            'ventas_hoy': ventas_hoy,
            'pedidos_hoy': pedidos_hoy.count(),
            'total_clientes': Cliente.objects.filter(activo=True).count(),
            'movimientos_recientes': MovimientoInventario.objects.select_related(
                'producto', 'bodega', 'usuario'
            ).order_by('-fecha_movimiento')[:10] if user.can_see_costs() and hasattr(MovimientoInventario, 'usuario') else [],
            'pedidos_recientes': Pedido.objects.order_by('-fecha_creacion')[:10],
            'is_admin_dashboard': True,
        }
    
    def get_productos_bajo_stock(self):
        """Obtiene productos que están bajo el stock mínimo"""
        productos_bajo_stock = []
        
        for producto in Producto.objects.filter(activo=True):
            stock_total = Stock.objects.filter(producto=producto).aggregate(
                total=Sum('cantidad')
            )['total'] or 0
            
            if stock_total <= producto.stock_minimo:
                productos_bajo_stock.append({
                    'producto': producto,
                    'stock_actual': stock_total,
                    'stock_minimo': producto.stock_minimo
                })
        
        return productos_bajo_stock[:10]  # Máximo 10 para el dashboard