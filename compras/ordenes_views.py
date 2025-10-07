# compras/ordenes_views.py
# Vistas para la gestión de órdenes de compra, solicitudes y recepciones

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Sum, Count, Avg, F, Case, When, Value
from django.contrib import messages
from django.http import JsonResponse
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.utils import timezone
from django.db.models import DecimalField

# Importaciones locales
from .models import (
    Proveedor, OrdenCompra, ItemOrdenCompra, RecepcionCompra, 
    ItemRecepcionCompra, EstadoOrdenCompra, SolicitudCompra, ItemSolicitudCompra
)
from .forms import ProveedorForm, OrdenCompraForm, ItemOrdenCompraFormSet
from inventario.models import Producto

# ========================================
# MIXIN DE PERMISOS PARA COMPRAS
# ========================================

class ComprasRequiredMixin(UserPassesTestMixin):
    """Mixin para verificar permisos de compras"""
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_superuser or 
            self.request.user.groups.filter(name__in=['Compras', 'Administradores']).exists() or
            self.request.user.role in ['administrador']
        )
    
    def handle_no_permission(self):
        messages.error(self.request, "No tienes permisos para acceder al módulo de Compras.")
        return redirect('accounts:dashboard')


# ========================================
# DASHBOARD DE COMPRAS
# ========================================

@login_required
def compras_dashboard(request):
    """Dashboard principal de compras"""
    
    # Filtros de fecha - último trimestre por defecto
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=90)
    
    # KPIs principales
    total_proveedores = Proveedor.objects.filter(activo=True).count()
    ordenes_activas = OrdenCompra.objects.exclude(
        estado__in=['cancelada', 'recibida_total']
    ).count()
    
    # Órdenes por estado
    ordenes_por_estado = OrdenCompra.objects.values('estado').annotate(
        count=Count('id'),
        valor=Sum('total')
    ).order_by('estado')
    
    # Valor total de órdenes abiertas
    valor_ordenes_abiertas = OrdenCompra.objects.filter(
        estado__in=['enviada', 'confirmada', 'recibida_parcial']
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Órdenes pendientes de recibir
    ordenes_pendientes = OrdenCompra.objects.filter(
        estado__in=['enviada', 'confirmada', 'recibida_parcial']
    ).select_related('proveedor').order_by('fecha_entrega_estimada')[:5]
    
    # Recepciones recientes
    recepciones_recientes = RecepcionCompra.objects.select_related(
        'orden_compra', 'orden_compra__proveedor', 'usuario_recepcion'
    ).order_by('-fecha_recepcion')[:5]
    
    # Top proveedores (por valor de órdenes del mes)
    mes_actual = timezone.now().replace(day=1)
    top_proveedores = OrdenCompra.objects.filter(
        fecha_orden__gte=mes_actual,
        estado__in=['confirmada', 'recibida_parcial', 'recibida_total']
    ).values('proveedor__razon_social', 'proveedor__codigo').annotate(
        total_valor=Sum('total'),
        count=Count('id')
    ).order_by('-total_valor')[:5]
    
    # Órdenes vencidas (fecha entrega pasada)
    ordenes_vencidas = OrdenCompra.objects.filter(
        fecha_entrega_estimada__lt=fecha_fin,
        estado__in=['enviada', 'confirmada', 'recibida_parcial']
    ).count()
    
    # Productos más comprados (del mes)
    productos_top = ItemOrdenCompra.objects.filter(
        orden_compra__fecha_orden__gte=mes_actual,
        orden_compra__estado__in=['confirmada', 'recibida_parcial', 'recibida_total']
    ).values('producto__codigo', 'producto__nombre').annotate(
        cantidad_total=Sum('cantidad'),
        valor_total=Sum('total')
    ).order_by('-cantidad_total')[:5]
    
    context = {
        'total_proveedores': total_proveedores,
        'ordenes_activas': ordenes_activas,
        'valor_ordenes_abiertas': valor_ordenes_abiertas,
        'ordenes_vencidas': ordenes_vencidas,
        'ordenes_por_estado': ordenes_por_estado,
        'ordenes_pendientes': ordenes_pendientes,
        'recepciones_recientes': recepciones_recientes,
        'top_proveedores': top_proveedores,
        'productos_top': productos_top,
        'estados_orden': EstadoOrdenCompra.choices,
    }
    
    return render(request, 'compras/dashboard.html', context)


# ========================================
# VISTAS DE ÓRDENES DE COMPRA
# ========================================

class OrdenCompraListView(ComprasRequiredMixin, ListView):
    """Lista de órdenes de compra"""
    model = OrdenCompra
    template_name = 'compras/orden_compra_list.html'
    context_object_name = 'ordenes'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = OrdenCompra.objects.select_related(
            'proveedor', 'usuario_creacion'
        ).prefetch_related('items')
        
        # Filtros del template
        estados = self.request.GET.getlist('estado')
        proveedor = self.request.GET.get('proveedor')
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        search = self.request.GET.get('search')
        numero_orden = self.request.GET.get('numero_orden')
        
        # Filtro por número de orden específico
        if numero_orden:
            queryset = queryset.filter(numero__icontains=numero_orden)
        
        # Filtro por estados (puede ser múltiple)
        if estados:
            # El filtro viene como string separado por comas desde la URL
            if len(estados) == 1 and ',' in estados[0]:
                estados = estados[0].split(',')
            queryset = queryset.filter(estado__in=estados)
        
        # Filtro por proveedor (búsqueda por nombre)
        if proveedor:
            queryset = queryset.filter(
                Q(proveedor__razon_social__icontains=proveedor) |
                Q(proveedor__nombre_comercial__icontains=proveedor)
            )
        
        # Filtro por rango de fechas
        if fecha_desde:
            queryset = queryset.filter(fecha_orden__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_orden__lte=fecha_hasta)
            
        # Búsqueda general
        if search:
            queryset = queryset.filter(
                Q(numero__icontains=search) |
                Q(proveedor__razon_social__icontains=search) |
                Q(proveedor__numero_documento__icontains=search) |
                Q(numero_referencia_proveedor__icontains=search)
            )
        
        return queryset.order_by('-fecha_orden')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Fechas para comparaciones
        context['today'] = date.today()
        context['future_week'] = date.today() + timedelta(days=7)
        
        # Filtros disponibles
        context['estados'] = EstadoOrdenCompra.choices
        context['proveedores'] = Proveedor.objects.filter(activo=True).order_by('razon_social')
        context['filtro_estado'] = self.request.GET.get('estado', 'all')
        context['filtro_search'] = self.request.GET.get('search', '')
        
        # Estadísticas básicas
        all_orders = OrdenCompra.objects.all()
        context['stats'] = {
            'total': all_orders.count(),
            'pendientes': all_orders.filter(estado__in=['borrador', 'enviada']).count(),
            'proceso': all_orders.filter(estado__in=['confirmada', 'recibida_parcial']).count(),
            'total_valor': all_orders.aggregate(total=Sum('total'))['total'] or 0,
        }
        
        return context


class OrdenCompraCreateView(ComprasRequiredMixin, CreateView):
    """Crear nueva orden de compra"""
    model = OrdenCompra
    form_class = OrdenCompraForm
    template_name = 'compras/orden_compra_form.html'
    success_url = reverse_lazy('compras:orden_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.POST:
            context['formset'] = ItemOrdenCompraFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = ItemOrdenCompraFormSet(instance=self.object)
            
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        # Validar formset
        if formset.is_valid():
            form.instance.usuario_creacion = self.request.user
            
            # Guardar la orden primero
            self.object = form.save()
            
            # Guardar los items
            formset.instance = self.object
            formset.save()
            
            messages.success(self.request, f'Orden de compra {self.object.numero} creada exitosamente con {formset.total_form_count()} items.')
            return redirect(self.get_success_url())
        else:
            # Si hay errores en el formset, mostrarlos
            for error in formset.non_form_errors():
                messages.error(self.request, error)
            return self.render_to_response(self.get_context_data(form=form))
    
    def get_success_url(self):
        # Redirigir al detalle de la orden creada
        return reverse_lazy('compras:orden_detail', kwargs={'pk': self.object.pk})


class OrdenCompraDetailView(ComprasRequiredMixin, DetailView):
    """Detalle de orden de compra"""
    model = OrdenCompra
    template_name = 'compras/orden_compra_detail_fixed.html'
    context_object_name = 'orden'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Fecha de hoy para comparaciones
        context['today'] = date.today()
        
        # Items de la orden
        context['items'] = self.object.items.select_related(
            'producto', 'variante'
        ).order_by('producto__nombre')
        
        # Recepciones de esta orden
        context['recepciones'] = self.object.recepciones.select_related(
            'usuario_recepcion'
        ).order_by('-fecha_recepcion')
        
        return context


class OrdenCompraUpdateView(ComprasRequiredMixin, UpdateView):
    """Editar orden de compra"""
    model = OrdenCompra
    form_class = OrdenCompraForm
    template_name = 'compras/orden_compra_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.POST:
            context['formset'] = ItemOrdenCompraFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = ItemOrdenCompraFormSet(instance=self.object)
            
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        # Validar formset
        if formset.is_valid():
            # Guardar la orden
            self.object = form.save()
            
            # Guardar los items
            formset.instance = self.object
            formset.save()
            
            messages.success(self.request, f'Orden de compra {self.object.numero} actualizada exitosamente.')
            return redirect(self.get_success_url())
        else:
            # Si hay errores en el formset, mostrarlos
            for error in formset.non_form_errors():
                messages.error(self.request, error)
            return self.render_to_response(self.get_context_data(form=form))
    
    def get_success_url(self):
        return reverse_lazy('compras:orden_detail', kwargs={'pk': self.object.pk})


class OrdenCompraCancelView(ComprasRequiredMixin, UpdateView):
    """Cancelar orden de compra"""
    model = OrdenCompra
    template_name = 'compras/orden_compra_cancel.html'
    fields = ['motivo_cancelacion']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['orden'] = self.object
        return context
    
    def form_valid(self, form):
        try:
            # Intentar cancelar la orden
            self.object.cancelar(
                usuario=self.request.user,
                motivo=form.cleaned_data['motivo_cancelacion']
            )
            
            messages.success(
                self.request, 
                f'Orden de compra {self.object.numero} cancelada exitosamente.'
            )
            return redirect('compras:orden_detail', pk=self.object.pk)
            
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.render_to_response(self.get_context_data(form=form))
    
    def get_object(self):
        obj = super().get_object()
        
        # Verificar que se puede cancelar
        if not obj.puede_cancelarse():
            messages.error(
                self.request, 
                f'No se puede cancelar una orden en estado {obj.get_estado_display()}'
            )
            
        return obj


class OrdenCompraPrintView(ComprasRequiredMixin, DetailView):
    """Vista de impresión para orden de compra"""
    model = OrdenCompra
    template_name = 'compras/orden_compra_print.html'
    context_object_name = 'orden'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Agregar información del usuario actual
        context['user'] = self.request.user
        
        return context


# ========================================
# VISTAS DE RECEPCIONES
# ========================================

class RecepcionCompraCreateView(ComprasRequiredMixin, CreateView):
    """Crear nueva recepción"""
    model = RecepcionCompra
    template_name = 'compras/recepcion_form.html'
    fields = [
        'orden_compra', 'numero_factura_proveedor', 'numero_remision',
        'transportadora', 'observaciones', 'observaciones_calidad'
    ]
    
    def get_initial(self):
        initial = super().get_initial()
        orden_id = self.request.GET.get('orden')
        if orden_id:
            initial['orden_compra'] = orden_id
        return initial
    
    def form_valid(self, form):
        form.instance.usuario_recepcion = self.request.user
        messages.success(self.request, 'Recepción creada exitosamente.')
        return super().form_valid(form)


class RecepcionCompraDetailView(ComprasRequiredMixin, DetailView):
    """Detalle de recepción"""
    model = RecepcionCompra
    template_name = 'compras/recepcion_detail.html'
    context_object_name = 'recepcion'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Items recibidos
        context['items'] = self.object.items.select_related(
            'item_orden', 'item_orden__producto', 'item_orden__variante'
        ).order_by('item_orden__producto__nombre')
        
        return context


# ========================================
# VISTAS DE SOLICITUDES DE COMPRA
# ========================================

class SolicitudCompraListView(ComprasRequiredMixin, ListView):
    """Lista de solicitudes de compra"""
    model = SolicitudCompra
    template_name = 'compras/solicitud_list.html'
    context_object_name = 'solicitudes'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = SolicitudCompra.objects.select_related(
            'usuario_solicita', 'usuario_aprueba'
        ).prefetch_related('items')
        
        # Filtros básicos
        estado = self.request.GET.get('estado')
        usuario = self.request.GET.get('usuario')
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        
        if estado and estado != 'all':
            queryset = queryset.filter(estado=estado)
        
        if usuario:
            queryset = queryset.filter(usuario_solicita__id=usuario)
        
        if fecha_desde:
            queryset = queryset.filter(fecha_solicitud__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_solicitud__lte=fecha_hasta)
        
        return queryset.order_by('-fecha_solicitud')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Opciones para filtros
        context['estados_solicitud'] = SolicitudCompra._meta.get_field('estado').choices
        context['usuarios'] = self.request.user.__class__.objects.filter(is_active=True)
        
        return context


class SolicitudCompraCreateView(ComprasRequiredMixin, CreateView):
    """Crear nueva solicitud de compra"""
    model = SolicitudCompra
    template_name = 'compras/solicitud_form.html'
    fields = ['motivo', 'prioridad', 'observaciones']
    
    def form_valid(self, form):
        form.instance.usuario_solicita = self.request.user
        form.instance.estado = 'borrador'
        messages.success(self.request, 'Solicitud de compra creada exitosamente.')
        return super().form_valid(form)


class SolicitudCompraDetailView(ComprasRequiredMixin, DetailView):
    """Detalle de solicitud de compra"""
    model = SolicitudCompra
    template_name = 'compras/solicitud_detail.html'
    context_object_name = 'solicitud'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Items de la solicitud
        context['items'] = self.object.items.select_related('producto').order_by('producto__nombre')
        
        return context


class SolicitudCompraUpdateView(ComprasRequiredMixin, UpdateView):
    """Editar solicitud de compra"""
    model = SolicitudCompra
    template_name = 'compras/solicitud_form.html'
    fields = ['motivo', 'prioridad', 'observaciones']
    
    def get_object(self):
        obj = super().get_object()
        
        # Solo permitir edición si está en borrador
        if obj.estado != 'borrador':
            messages.error(
                self.request, 
                'Solo se pueden editar solicitudes en estado borrador.'
            )
            return redirect('compras:solicitud_detail', pk=obj.pk)
        
        return obj
    
    def form_valid(self, form):
        messages.success(self.request, 'Solicitud de compra actualizada exitosamente.')
        return super().form_valid(form)


# ========================================
# FUNCIONES DE GESTIÓN DE SOLICITUDES
# ========================================

@login_required
def aprobar_solicitud(request, pk):
    """Aprobar una solicitud de compra"""
    solicitud = get_object_or_404(SolicitudCompra, pk=pk)
    
    if not solicitud.puede_ser_aprobada_por(request.user):
        messages.error(request, "No tienes permisos para aprobar esta solicitud.")
        return redirect('compras:solicitud_detail', pk=pk)
    
    if request.method == 'POST':
        observaciones = request.POST.get('observaciones', '')
        
        try:
            solicitud.aprobar(request.user, observaciones)
            messages.success(request, f"Solicitud {solicitud.codigo} aprobada exitosamente.")
        except Exception as e:
            messages.error(request, f"Error al aprobar la solicitud: {e}")
    
    return redirect('compras:solicitud_detail', pk=pk)


@login_required
def rechazar_solicitud(request, pk):
    """Rechazar una solicitud de compra"""
    solicitud = get_object_or_404(SolicitudCompra, pk=pk)
    
    if not solicitud.puede_ser_rechazada_por(request.user):
        messages.error(request, "No tienes permisos para rechazar esta solicitud.")
        return redirect('compras:solicitud_detail', pk=pk)
    
    if request.method == 'POST':
        observaciones = request.POST.get('observaciones', '')
        
        if not observaciones:
            messages.error(request, "Las observaciones son obligatorias para rechazar una solicitud.")
            return redirect('compras:solicitud_detail', pk=pk)
        
        try:
            solicitud.rechazar(request.user, observaciones)
            messages.success(request, f"Solicitud {solicitud.codigo} rechazada.")
        except Exception as e:
            messages.error(request, f"Error al rechazar la solicitud: {e}")
    
    return redirect('compras:solicitud_detail', pk=pk)


@login_required
def enviar_solicitud(request, pk):
    """Enviar solicitud a aprobación"""
    solicitud = get_object_or_404(SolicitudCompra, pk=pk)
    
    # Verificar que el usuario es el solicitante o tiene permisos
    if solicitud.solicitante != request.user and not request.user.is_superuser:
        messages.error(request, "Solo el solicitante puede enviar la solicitud a aprobación.")
        return redirect('compras:solicitud_detail', pk=pk)
    
    if request.method == 'POST':
        try:
            solicitud.enviar_a_aprobacion()
            messages.success(request, f"Solicitud {solicitud.codigo} enviada a aprobación.")
        except Exception as e:
            messages.error(request, f"Error al enviar la solicitud: {e}")
    
    return redirect('compras:solicitud_detail', pk=pk)


@login_required
def crear_orden_desde_solicitud(request, pk):
    """Crear orden de compra desde solicitud aprobada"""
    solicitud = get_object_or_404(SolicitudCompra, pk=pk)
    
    if solicitud.estado != 'aprobada':
        messages.error(request, "Solo se pueden crear órdenes desde solicitudes aprobadas.")
        return redirect('compras:solicitud_detail', pk=pk)
    
    if request.method == 'POST':
        proveedor_id = request.POST.get('proveedor')
        if not proveedor_id:
            messages.error(request, "Debe seleccionar un proveedor.")
            return redirect('compras:solicitud_detail', pk=pk)
        
        try:
            proveedor = Proveedor.objects.get(pk=proveedor_id)
            orden = solicitud.crear_orden_compra(proveedor, request.user)
            messages.success(
                request, 
                f"Orden de compra {orden.numero_orden} creada exitosamente."
            )
            return redirect('compras:orden_detail', pk=orden.pk)
        except Exception as e:
            messages.error(request, f"Error al crear la orden: {e}")
    
    return redirect('compras:solicitud_detail', pk=pk)


@login_required
def agregar_item_solicitud(request, pk):
    """Agregar item a una solicitud de compra"""
    solicitud = get_object_or_404(SolicitudCompra, pk=pk)
    
    if solicitud.estado != 'borrador':
        messages.error(request, "Solo se pueden agregar items a solicitudes en borrador.")
        return redirect('compras:solicitud_detail', pk=pk)
    
    if request.method == 'POST':
        producto_id = request.POST.get('producto')
        descripcion_item = request.POST.get('descripcion_item')
        especificaciones = request.POST.get('especificaciones', '')
        cantidad = request.POST.get('cantidad')
        unidad_medida = request.POST.get('unidad_medida', 'UND')
        precio_estimado = request.POST.get('precio_estimado')
        
        if not all([cantidad]) or (not producto_id and not descripcion_item):
            messages.error(request, "Cantidad y descripción o producto son obligatorios.")
            return redirect('compras:solicitud_detail', pk=pk)
        
        try:
            producto = None
            if producto_id:
                producto = Producto.objects.get(pk=producto_id)
                # Si hay producto, usar su descripción por defecto
                if not descripcion_item:
                    descripcion_item = producto.nombre
            
            ItemSolicitudCompra.objects.create(
                solicitud=solicitud,
                producto=producto,
                descripcion_item=descripcion_item,
                especificaciones=especificaciones,
                cantidad=Decimal(cantidad),
                unidad_medida=unidad_medida,
                precio_estimado=Decimal(precio_estimado) if precio_estimado else Decimal('0.0000'),
            )
            
            messages.success(request, "Item agregado exitosamente.")
            
        except Exception as e:
            messages.error(request, f"Error al agregar el item: {e}")
    
    return redirect('compras:solicitud_detail', pk=pk)


@login_required
def eliminar_item_solicitud(request, pk, item_pk):
    """Eliminar item de solicitud de compra"""
    solicitud = get_object_or_404(SolicitudCompra, pk=pk)
    item = get_object_or_404(ItemSolicitudCompra, pk=item_pk, solicitud=solicitud)
    
    if solicitud.estado != 'borrador':
        messages.error(request, "Solo se pueden eliminar items de solicitudes en borrador.")
        return redirect('compras:solicitud_detail', pk=pk)
    
    if request.method == 'POST':
        item.delete()
        messages.success(request, "Item eliminado exitosamente.")
    
    return redirect('compras:solicitud_detail', pk=pk)


# ========================================
# FUNCIONES AJAX PARA ÓRDENES
# ========================================

@login_required
def agregar_item_orden(request, pk):
    """Agregar item a orden de compra via AJAX"""
    if request.method == 'POST':
        orden = get_object_or_404(OrdenCompra, pk=pk)
        
        # Solo permitir si la orden está en borrador
        if orden.estado != 'borrador':
            return JsonResponse({
                'success': False, 
                'message': 'Solo se pueden agregar items a órdenes en borrador'
            })
        
        producto_id = request.POST.get('producto_id')
        cantidad = request.POST.get('cantidad')
        precio_unitario = request.POST.get('precio_unitario')
        
        try:
            producto = Producto.objects.get(id=producto_id)
            
            item, created = ItemOrdenCompra.objects.get_or_create(
                orden_compra=orden,
                producto=producto,
                defaults={
                    'cantidad': Decimal(cantidad),
                    'precio_unitario': Decimal(precio_unitario)
                }
            )
            
            if not created:
                item.cantidad = Decimal(cantidad)
                item.precio_unitario = Decimal(precio_unitario)
                item.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Item agregado exitosamente',
                'item': {
                    'id': str(item.id),
                    'producto': producto.nombre,
                    'cantidad': float(item.cantidad),
                    'precio_unitario': float(item.precio_unitario),
                    'total': float(item.total)
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al agregar item: {str(e)}'
            })
    
    return JsonResponse({'success': False})


@login_required
def cambiar_estado_orden(request, pk):
    """Cambiar estado de orden de compra via AJAX"""
    if request.method == 'POST':
        orden = get_object_or_404(OrdenCompra, pk=pk)
        nuevo_estado = request.POST.get('estado')
        
        if nuevo_estado in [choice[0] for choice in EstadoOrdenCompra.choices]:
            orden.estado = nuevo_estado
            orden.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Estado cambiado a {orden.get_estado_display()}'
            })
    
    return JsonResponse({'success': False})


# ========================================
# REPORTES DE COMPRAS
# ========================================

@login_required
def reporte_compras(request):
    """Reporte de compras por período"""
    
    # Parámetros de fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if not fecha_inicio:
        fecha_inicio = timezone.now().replace(day=1).date()
    else:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    
    if not fecha_fin:
        fecha_fin = timezone.now().date()
    else:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    
    # Datos del reporte
    ordenes = OrdenCompra.objects.filter(
        fecha_orden__range=[fecha_inicio, fecha_fin]
    ).select_related('proveedor').order_by('-fecha_orden')
    
    # Resumen por proveedor
    resumen_proveedores = ordenes.values(
        'proveedor__razon_social', 'proveedor__codigo'
    ).annotate(
        total_ordenes=Count('id'),
        valor_total=Sum('total')
    ).order_by('-valor_total')
    
    # Resumen por estado
    resumen_estados = ordenes.values('estado').annotate(
        count=Count('id'),
        valor=Sum('total')
    ).order_by('estado')
    
    context = {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'ordenes': ordenes,
        'resumen_proveedores': resumen_proveedores,
        'resumen_estados': resumen_estados,
        'total_ordenes': ordenes.count(),
        'valor_total': ordenes.aggregate(Sum('total'))['total'] or 0,
    }
    
    return render(request, 'compras/reporte_compras.html', context)