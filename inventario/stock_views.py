# inventario/stock_views.py
"""
Vistas especializadas para gestión de stock e inventarios
Extraído de inventario/views.py para mejorar organización
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count, F
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import Stock, Bodega, Producto, MovimientoInventario, Categoria


class InventarioRequiredMixin(UserPassesTestMixin):
    """Mixin para verificar permisos de inventario"""
    def test_func(self):
        return self.request.user.can_adjust_inventory()


class InventarioViewMixin(UserPassesTestMixin):
    """Mixin para permitir ver inventario (incluye bodega)"""
    def test_func(self):
        return (self.request.user.can_adjust_inventory() or 
                self.request.user.can_view_inventory())


class AdminInventarioMixin(UserPassesTestMixin):
    """Mixin para funciones estratégicas de inventario (solo administradores)"""
    def test_func(self):
        return (self.request.user.is_superuser or 
                self.request.user.role in ['superadmin', 'administrador'])


# ============= VISTAS DE STOCK =============

class StockListView(InventarioViewMixin, ListView):
    """Lista de stock por productos y bodegas"""
    model = Stock
    template_name = 'inventario/stock_list.html'
    context_object_name = 'stocks'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Stock.objects.select_related('producto', 'bodega', 'variante').annotate(
            stock_total=F('cantidad') + F('cantidad_reservada')
        )
        
        # Filtros
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(producto__nombre__icontains=search) |
                Q(producto__codigo__icontains=search) |
                Q(bodega__nombre__icontains=search)
            )
        
        bodega_id = self.request.GET.get('bodega')
        if bodega_id:
            try:
                queryset = queryset.filter(bodega_id=bodega_id)
            except ValueError:
                pass
        
        # Filtro por estado de stock
        stock_status = self.request.GET.get('stock_status')
        if stock_status == 'sin_stock':
            queryset = queryset.filter(cantidad=0)
        elif stock_status == 'bajo_minimo':
            # Solo productos bajo el mínimo
            productos_bajo_minimo = []
            for stock in queryset:
                if stock.cantidad <= stock.producto.stock_minimo:
                    productos_bajo_minimo.append(stock.id)
            queryset = queryset.filter(id__in=productos_bajo_minimo)
        elif stock_status == 'disponible':
            queryset = queryset.filter(cantidad__gt=0)
        
        # Filtro por categoría
        categoria_id = self.request.GET.get('categoria')
        if categoria_id:
            try:
                queryset = queryset.filter(producto__categoria_id=categoria_id)
            except ValueError:
                pass
        
        return queryset.order_by('bodega__nombre', 'producto__nombre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bodegas'] = Bodega.objects.filter(activa=True).order_by('nombre')
        context['categorias'] = Categoria.objects.filter(activa=True).order_by('nombre')
        
        # Estadísticas generales
        context['total_productos_stock'] = Stock.objects.filter(cantidad__gt=0).count()
        context['productos_sin_stock'] = Stock.objects.filter(cantidad=0).count()
        context['valor_total_inventario'] = self._calcular_valor_total_inventario()
        
        # Filtros aplicados
        context['filtros'] = {
            'search': self.request.GET.get('search', ''),
            'bodega': self.request.GET.get('bodega', ''),
            'stock_status': self.request.GET.get('stock_status', ''),
            'categoria': self.request.GET.get('categoria', ''),
        }
        
        return context
    
    def _calcular_valor_total_inventario(self):
        """Calcular valor total del inventario"""
        valor_total = 0
        stocks = Stock.objects.select_related('producto').filter(cantidad__gt=0)
        for stock in stocks:
            valor_total += stock.cantidad * stock.producto.costo_promedio
        return valor_total


class StockDetailView(InventarioViewMixin, DetailView):
    """Detalle de stock con histórico de movimientos"""
    model = Stock
    template_name = 'inventario/stock_detail.html'
    context_object_name = 'stock'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Movimientos recientes del producto en esta bodega
        context['movimientos_recientes'] = MovimientoInventario.objects.filter(
            producto=self.object.producto,
            bodega=self.object.bodega
        ).order_by('-fecha_creacion')[:20]
        
        # Stock en otras bodegas del mismo producto
        context['otros_stocks'] = Stock.objects.filter(
            producto=self.object.producto
        ).exclude(id=self.object.id).select_related('bodega')
        
        # Estadísticas del producto
        context['stock_total_producto'] = Stock.objects.filter(
            producto=self.object.producto
        ).aggregate(total=Sum('cantidad'))['total'] or 0
        
        context['valor_stock'] = self.object.cantidad * self.object.producto.costo_promedio
        context['necesita_reposicion'] = context['stock_total_producto'] <= self.object.producto.stock_minimo
        
        return context


# ============= BODEGAS =============

class BodegaListView(InventarioViewMixin, ListView):
    """Lista de bodegas con estadísticas"""
    model = Bodega
    template_name = 'inventario/bodega_list.html'
    context_object_name = 'bodegas'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Agregar estadísticas por bodega
        for bodega in context['bodegas']:
            bodega.total_productos = Stock.objects.filter(bodega=bodega).count()
            bodega.stock_total = Stock.objects.filter(bodega=bodega).aggregate(
                total=Sum('cantidad')
            )['total'] or 0
            bodega.valor_inventario = self._calcular_valor_bodega(bodega)
        
        return context
    
    def _calcular_valor_bodega(self, bodega):
        """Calcular valor total del inventario en una bodega"""
        valor_total = 0
        stocks = Stock.objects.filter(bodega=bodega).select_related('producto')
        for stock in stocks:
            valor_total += stock.cantidad * stock.producto.costo_promedio
        return valor_total


class BodegaCreateView(AdminInventarioMixin, CreateView):
    """Crear nueva bodega"""
    model = Bodega
    template_name = 'inventario/bodega_form.html'
    fields = ['nombre', 'direccion', 'telefono', 'activa', 'es_principal', 'link_ubicacion']
    success_url = reverse_lazy('inventario:bodega_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Bodega "{form.cleaned_data["nombre"]}" creada exitosamente.')
        return super().form_valid(form)


class BodegaDetailView(InventarioViewMixin, DetailView):
    """Detalle de bodega con productos y estadísticas"""
    model = Bodega
    template_name = 'inventario/bodega_detail.html'
    context_object_name = 'bodega'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Stock de la bodega
        context['stocks'] = Stock.objects.filter(
            bodega=self.object
        ).select_related('producto').order_by('producto__nombre')
        
        # Estadísticas
        context['total_productos'] = context['stocks'].count()
        context['productos_con_stock'] = context['stocks'].filter(cantidad__gt=0).count()
        context['productos_sin_stock'] = context['stocks'].filter(cantidad=0).count()
        
        # Valor total del inventario
        valor_total = 0
        for stock in context['stocks']:
            valor_total += stock.cantidad * stock.producto.costo_promedio
        context['valor_inventario'] = valor_total
        
        # Movimientos recientes en la bodega
        context['movimientos_recientes'] = MovimientoInventario.objects.filter(
            bodega=self.object
        ).order_by('-fecha_creacion')[:10]
        
        # Productos bajo mínimo en esta bodega
        productos_bajo_minimo = []
        for stock in context['stocks']:
            if stock.cantidad <= stock.producto.stock_minimo:
                productos_bajo_minimo.append(stock)
        context['productos_bajo_minimo'] = productos_bajo_minimo
        
        return context


class BodegaUpdateView(AdminInventarioMixin, UpdateView):
    """Editar bodega"""
    model = Bodega
    template_name = 'inventario/bodega_form.html'
    fields = ['nombre', 'direccion', 'telefono', 'activa', 'es_principal', 'link_ubicacion']
    success_url = reverse_lazy('inventario:bodega_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Bodega "{form.cleaned_data["nombre"]}" actualizada exitosamente.')
        return super().form_valid(form)


# ============= TRANSFERENCIAS ENTRE BODEGAS =============

def transferencia_producto(request):
    """Vista para manejar transferencias entre bodegas - Solo para administradores"""
    if not request.user.is_authenticated:
        messages.error(request, 'Debe iniciar sesión para acceder a esta función.')
        return redirect('accounts:login')
    
    if request.user.role == 'bodega':
        messages.error(request, 'Los bodegueros no tienen permisos para realizar transferencias entre bodegas.')
        return redirect('inventario:stock_list')
    
    if not request.user.role in ['superadmin', 'administrador']:
        messages.error(request, 'No tiene permisos para realizar transferencias entre bodegas.')
        return redirect('inventario:stock_list')
    
    if request.method == 'POST':
        try:
            producto_id = request.POST.get('producto_id')
            bodega_origen_id = request.POST.get('bodega_origen')
            bodega_destino_id = request.POST.get('bodega_destino')
            cantidad = int(request.POST.get('cantidad', 0))
            observaciones = request.POST.get('observaciones', '')
            
            # Validaciones
            if not all([producto_id, bodega_origen_id, bodega_destino_id, cantidad]):
                messages.error(request, 'Todos los campos son obligatorios.')
                return render(request, 'inventario/transferencia_form.html', {
                    'productos': Producto.objects.filter(activo=True),
                    'bodegas': Bodega.objects.filter(activa=True)
                })
            
            if bodega_origen_id == bodega_destino_id:
                messages.error(request, 'La bodega de origen debe ser diferente a la de destino.')
                return render(request, 'inventario/transferencia_form.html', {
                    'productos': Producto.objects.filter(activo=True),
                    'bodegas': Bodega.objects.filter(activa=True)
                })
            
            if cantidad <= 0:
                messages.error(request, 'La cantidad debe ser mayor a cero.')
                return render(request, 'inventario/transferencia_form.html', {
                    'productos': Producto.objects.filter(activo=True),
                    'bodegas': Bodega.objects.filter(activa=True)
                })
            
            producto = get_object_or_404(Producto, id=producto_id)
            bodega_origen = get_object_or_404(Bodega, id=bodega_origen_id)
            bodega_destino = get_object_or_404(Bodega, id=bodega_destino_id)
            
            # Verificar stock disponible en bodega origen
            stock_origen = Stock.objects.filter(
                producto=producto,
                bodega=bodega_origen
            ).first()
            
            if not stock_origen or stock_origen.cantidad < cantidad:
                stock_disponible = stock_origen.cantidad if stock_origen else 0
                messages.error(request, f'Stock insuficiente en {bodega_origen.nombre}. Stock disponible: {stock_disponible}')
                return render(request, 'inventario/transferencia_form.html', {
                    'productos': Producto.objects.filter(activo=True),
                    'bodegas': Bodega.objects.filter(activa=True)
                })
            
            # Realizar transferencia en una transacción
            with transaction.atomic():
                # 1. Reducir stock en bodega origen
                stock_origen.cantidad -= cantidad
                stock_origen.save()
                
                # 2. Aumentar stock en bodega destino (crear si no existe)
                stock_destino, created = Stock.objects.get_or_create(
                    producto=producto,
                    bodega=bodega_destino,
                    defaults={'cantidad': 0, 'cantidad_reservada': 0}
                )
                stock_destino.cantidad += cantidad
                stock_destino.save()
                
                # 3. Registrar movimiento de salida en bodega origen
                movimiento_salida = MovimientoInventario.objects.create(
                    producto=producto,
                    bodega=bodega_origen,
                    bodega_destino=bodega_destino,
                    tipo_movimiento='transferencia',
                    motivo='transferencia',
                    cantidad=cantidad,
                    costo_unitario=producto.costo_promedio,
                    observaciones=f'Transferencia a {bodega_destino.nombre}. {observaciones}',
                    usuario=request.user
                )
                
                # 4. Registrar movimiento de entrada en bodega destino
                MovimientoInventario.objects.create(
                    producto=producto,
                    bodega=bodega_destino,
                    tipo_movimiento='entrada',
                    motivo='transferencia',
                    cantidad=cantidad,
                    costo_unitario=producto.costo_promedio,
                    observaciones=f'Transferencia desde {bodega_origen.nombre}. {observaciones}',
                    usuario=request.user
                )
            
            messages.success(
                request, 
                f'Transferencia realizada exitosamente: {cantidad} unidades de {producto.nombre} '
                f'de {bodega_origen.nombre} a {bodega_destino.nombre}'
            )
            
            return redirect('inventario:stock_list')
            
        except Exception as e:
            messages.error(request, f'Error al realizar la transferencia: {str(e)}')
    
    # GET request - mostrar formulario
    context = {
        'productos': Producto.objects.filter(activo=True).order_by('nombre'),
        'bodegas': Bodega.objects.filter(activa=True).order_by('nombre'),
        'stocks': Stock.objects.select_related('producto', 'bodega').filter(
            cantidad__gt=0
        ).order_by('bodega__nombre', 'producto__nombre')
    }
    
    return render(request, 'inventario/transferencia_form.html', context)


# ============= AJUSTES DE INVENTARIO =============

def ajuste_inventario(request):
    """Vista para ajustar stock de productos"""
    if not request.user.can_adjust_inventory():
        messages.error(request, 'No tiene permisos para ajustar inventario.')
        return redirect('inventario:stock_list')
    
    if request.method == 'POST':
        try:
            producto_id = request.POST.get('producto_id')
            bodega_id = request.POST.get('bodega_id')
            cantidad_nueva = int(request.POST.get('cantidad_nueva', 0))
            motivo = request.POST.get('motivo', 'ajuste')
            observaciones = request.POST.get('observaciones', '')
            
            # Validaciones
            if not all([producto_id, bodega_id]):
                messages.error(request, 'Producto y bodega son obligatorios.')
                return render(request, 'inventario/ajuste_form.html', {
                    'productos': Producto.objects.filter(activo=True),
                    'bodegas': Bodega.objects.filter(activa=True)
                })
            
            if cantidad_nueva < 0:
                messages.error(request, 'La cantidad no puede ser negativa.')
                return render(request, 'inventario/ajuste_form.html', {
                    'productos': Producto.objects.filter(activo=True),
                    'bodegas': Bodega.objects.filter(activa=True)
                })
            
            producto = get_object_or_404(Producto, id=producto_id)
            bodega = get_object_or_404(Bodega, id=bodega_id)
            
            # Obtener o crear stock
            stock, created = Stock.objects.get_or_create(
                producto=producto,
                bodega=bodega,
                defaults={'cantidad': 0, 'cantidad_reservada': 0}
            )
            
            cantidad_anterior = stock.cantidad
            diferencia = cantidad_nueva - cantidad_anterior
            
            # Actualizar stock
            stock.cantidad = cantidad_nueva
            stock.save()
            
            # Registrar movimiento
            tipo_movimiento = 'entrada' if diferencia > 0 else 'salida'
            MovimientoInventario.objects.create(
                producto=producto,
                bodega=bodega,
                tipo_movimiento=tipo_movimiento,
                motivo=motivo,
                cantidad=abs(diferencia),
                costo_unitario=producto.costo_promedio,
                observaciones=f'Ajuste de inventario: {cantidad_anterior} → {cantidad_nueva}. {observaciones}',
                usuario=request.user
            )
            
            accion = 'aumentó' if diferencia > 0 else 'redujo'
            messages.success(
                request, 
                f'Stock ajustado exitosamente: se {accion} {abs(diferencia)} unidades de {producto.nombre} '
                f'en {bodega.nombre}. Stock actual: {cantidad_nueva}'
            )
            
            return redirect('inventario:stock_detail', pk=stock.pk)
            
        except Exception as e:
            messages.error(request, f'Error al ajustar inventario: {str(e)}')
    
    # GET request
    context = {
        'productos': Producto.objects.filter(activo=True).order_by('nombre'),
        'bodegas': Bodega.objects.filter(activa=True).order_by('nombre')
    }
    
    return render(request, 'inventario/ajuste_form.html', context)


# ============= APIS DE STOCK =============

def obtener_stock_producto_bodega(request):
    """API para obtener stock de un producto en una bodega específica"""
    if not request.user.can_view_inventory():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    producto_id = request.GET.get('producto_id')
    bodega_id = request.GET.get('bodega_id')
    
    if not producto_id or not bodega_id:
        return JsonResponse({'error': 'Faltan parámetros'}, status=400)
    
    try:
        stock = Stock.objects.get(producto_id=producto_id, bodega_id=bodega_id)
        return JsonResponse({
            'cantidad': stock.cantidad,
            'cantidad_reservada': stock.cantidad_reservada,
            'disponible': stock.cantidad - stock.cantidad_reservada
        })
    except Stock.DoesNotExist:
        return JsonResponse({
            'cantidad': 0,
            'cantidad_reservada': 0,
            'disponible': 0
        })


def reporte_stock_bajo_minimo(request):
    """API para obtener productos con stock bajo el mínimo"""
    if not request.user.can_view_inventory():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    productos_bajo_minimo = []
    stocks = Stock.objects.select_related('producto', 'bodega').all()
    
    for stock in stocks:
        if stock.cantidad <= stock.producto.stock_minimo:
            productos_bajo_minimo.append({
                'producto_id': stock.producto.id,
                'producto_nombre': stock.producto.nombre,
                'producto_codigo': stock.producto.codigo,
                'bodega_nombre': stock.bodega.nombre,
                'stock_actual': stock.cantidad,
                'stock_minimo': stock.producto.stock_minimo,
                'diferencia': stock.producto.stock_minimo - stock.cantidad
            })
    
    return JsonResponse({
        'productos_bajo_minimo': productos_bajo_minimo,
        'total': len(productos_bajo_minimo)
    })


def estadisticas_stock_api(request):
    """API para estadísticas generales de stock"""
    if not request.user.can_view_inventory():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    # Estadísticas generales
    total_productos = Producto.objects.filter(activo=True).count()
    productos_con_stock = Stock.objects.filter(cantidad__gt=0).values('producto').distinct().count()
    productos_sin_stock = total_productos - productos_con_stock
    
    # Valor total del inventario
    valor_total = 0
    stocks = Stock.objects.select_related('producto').filter(cantidad__gt=0)
    for stock in stocks:
        valor_total += stock.cantidad * stock.producto.costo_promedio
    
    # Productos bajo mínimo
    productos_bajo_minimo = 0
    for stock in Stock.objects.select_related('producto').all():
        if stock.cantidad <= stock.producto.stock_minimo:
            productos_bajo_minimo += 1
    
    return JsonResponse({
        'total_productos': total_productos,
        'productos_con_stock': productos_con_stock,
        'productos_sin_stock': productos_sin_stock,
        'productos_bajo_minimo': productos_bajo_minimo,
        'valor_total_inventario': float(valor_total),
        'bodegas_activas': Bodega.objects.filter(activa=True).count()
    })