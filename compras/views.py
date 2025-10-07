from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count, Avg, F, Case, When, Value
from django.contrib import messages
from django.http import JsonResponse
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import DecimalField

from .models import Proveedor, OrdenCompra, ItemOrdenCompra, RecepcionCompra, ItemRecepcionCompra, EstadoOrdenCompra, SolicitudCompra, ItemSolicitudCompra
from .forms import ProveedorForm, OrdenCompraForm, ItemOrdenCompraFormSet
from inventario.models import Producto

# ============= MIXINS =============

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

# ============= DASHBOARD COMPRAS =============

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

# ============= VISTAS PROVEEDORES =============

class ProveedorListView(ComprasRequiredMixin, ListView):
    """Lista de proveedores"""
    model = Proveedor
    template_name = 'compras/proveedor_list.html'
    context_object_name = 'proveedores'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Proveedor.objects.select_related('ciudad', 'ciudad__departamento')
        
        # Filtros
        search = self.request.GET.get('search')
        activo = self.request.GET.get('activo')
        
        if search:
            queryset = queryset.filter(
                Q(razon_social__icontains=search) |
                Q(nombre_comercial__icontains=search) |
                Q(numero_documento__icontains=search) |
                Q(codigo__icontains=search)
            )
        
        if activo == 'true':
            queryset = queryset.filter(activo=True)
        elif activo == 'false':
            queryset = queryset.filter(activo=False)
        
        return queryset.order_by('razon_social')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filtro_search'] = self.request.GET.get('search', '')
        context['filtro_activo'] = self.request.GET.get('activo', 'all')
        return context

class ProveedorCreateView(ComprasRequiredMixin, CreateView):
    """Crear nuevo proveedor"""
    model = Proveedor
    template_name = 'compras/proveedor_form.html'
    fields = [
        'codigo', 'razon_social', 'nombre_comercial', 'tipo_documento', 
        'numero_documento', 'telefono', 'email', 'sitio_web',
        'direccion', 'ciudad', 'codigo_postal',
        'condiciones_pago', 'limite_credito', 'descuento_comercial',
        'contacto_nombre', 'contacto_cargo', 'contacto_telefono', 'contacto_email',
        'observaciones'
    ]
    
    def form_valid(self, form):
        form.instance.usuario_creacion = self.request.user
        messages.success(self.request, 'Proveedor creado exitosamente.')
        return super().form_valid(form)

class ProveedorDetailView(ComprasRequiredMixin, DetailView):
    """Detalle de proveedor"""
    model = Proveedor
    template_name = 'compras/proveedor_detail.html'
    context_object_name = 'proveedor'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Órdenes del proveedor
        context['ordenes_recientes'] = self.object.ordenes_compra.select_related(
            'usuario_creacion'
        ).order_by('-fecha_creacion')[:10]
        
        # Estadísticas
        context['total_ordenes'] = self.object.ordenes_compra.count()
        context['valor_total_ordenes'] = self.object.ordenes_compra.aggregate(
            total=Sum('total')
        )['total'] or 0
        
        return context

class ProveedorUpdateView(ComprasRequiredMixin, UpdateView):
    """Editar proveedor"""
    model = Proveedor
    template_name = 'compras/proveedor_form.html'
    fields = [
        'codigo', 'razon_social', 'nombre_comercial', 'tipo_documento', 
        'numero_documento', 'telefono', 'email', 'sitio_web',
        'direccion', 'ciudad', 'codigo_postal',
        'condiciones_pago', 'limite_credito', 'descuento_comercial',
        'contacto_nombre', 'contacto_cargo', 'contacto_telefono', 'contacto_email',
        'observaciones', 'activo'
    ]
    
    def form_valid(self, form):
        messages.success(self.request, 'Proveedor actualizado exitosamente.')
        return super().form_valid(form)

# ============= VISTAS ÓRDENES DE COMPRA =============

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

# ============= VISTAS RECEPCIONES =============

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

# ============= VISTAS AJAX =============

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

# ============= REPORTES =============

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


# ============= SOLICITUDES DE COMPRA =============

class SolicitudCompraListView(ComprasRequiredMixin, ListView):
    """Lista de solicitudes de compra"""
    model = SolicitudCompra
    template_name = 'compras/solicitud_list.html'
    context_object_name = 'solicitudes'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = SolicitudCompra.objects.all().select_related(
            'solicitante', 'aprobador'
        ).prefetch_related('items__producto')
        
        # Filtros
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
            
        prioridad = self.request.GET.get('prioridad')
        if prioridad:
            queryset = queryset.filter(prioridad=prioridad)
            
        fecha_desde = self.request.GET.get('fecha_desde')
        if fecha_desde:
            queryset = queryset.filter(fecha_solicitud__gte=fecha_desde)
            
        fecha_hasta = self.request.GET.get('fecha_hasta')
        if fecha_hasta:
            queryset = queryset.filter(fecha_solicitud__lte=fecha_hasta)
        
        # Búsqueda por código o justificación
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(codigo__icontains=q) | 
                Q(justificacion__icontains=q)
            )
        
        return queryset.order_by('-fecha_solicitud')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filtros'] = {
            'estado': self.request.GET.get('estado', ''),
            'prioridad': self.request.GET.get('prioridad', ''),
            'fecha_desde': self.request.GET.get('fecha_desde', ''),
            'fecha_hasta': self.request.GET.get('fecha_hasta', ''),
            'q': self.request.GET.get('q', ''),
        }
        context['estados_choices'] = SolicitudCompra.ESTADO_CHOICES
        context['prioridades_choices'] = SolicitudCompra.PRIORIDAD_CHOICES
        return context


class SolicitudCompraCreateView(ComprasRequiredMixin, CreateView):
    """Crear nueva solicitud de compra"""
    model = SolicitudCompra
    template_name = 'compras/solicitud_form.html'
    fields = ['prioridad', 'justificacion', 'fecha_requerida']
    
    def form_valid(self, form):
        form.instance.solicitante = self.request.user
        messages.success(
            self.request, 
            f'Solicitud de compra {form.instance.codigo} creada exitosamente.'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('compras:solicitud_detail', kwargs={'pk': self.object.pk})


class SolicitudCompraDetailView(ComprasRequiredMixin, DetailView):
    """Detalle de solicitud de compra"""
    model = SolicitudCompra
    template_name = 'compras/solicitud_detail.html'
    context_object_name = 'solicitud'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all().select_related('producto')
        context['puede_aprobar'] = self.object.puede_ser_aprobada_por(self.request.user)
        context['puede_rechazar'] = self.object.puede_ser_rechazada_por(self.request.user)
        return context


class SolicitudCompraUpdateView(ComprasRequiredMixin, UpdateView):
    """Actualizar solicitud de compra"""
    model = SolicitudCompra
    template_name = 'compras/solicitud_form.html'
    fields = ['prioridad', 'justificacion', 'fecha_requerida']
    
    def get_queryset(self):
        # Solo permitir editar si está en borrador
        return SolicitudCompra.objects.filter(estado='borrador')
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            f'Solicitud de compra {form.instance.codigo} actualizada exitosamente.'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('compras:solicitud_detail', kwargs={'pk': self.object.pk})


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


# ============= ITEMS DE SOLICITUD =============

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


# ============================
# VISTAS DE REDIRECCIÓN - MEJOR ORGANIZACIÓN MODULAR
# ============================

@login_required
def gestion_compras_dashboard(request):
    """Dashboard centralizado simplificado para gestión de compras y proveedores"""
    from django.http import HttpResponse
    
    # HTML directo sin template complejo
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard de Compras - Sistema Reyes</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .dashboard-header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 2rem 0;
                margin-bottom: 2rem;
            }}
            .module-card {{
                border: none;
                border-radius: 15px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: transform 0.3s ease;
                height: 100%;
            }}
            .module-card:hover {{
                transform: translateY(-5px);
            }}
            .module-icon {{
                font-size: 3rem;
                margin-bottom: 1rem;
            }}
        </style>
    </head>
    <body>
        <div class="dashboard-header">
            <div class="container">
                <div class="row">
                    <div class="col-12 text-center">
                        <h1><i class="fas fa-truck"></i> Dashboard de Compras</h1>
                        <p class="lead">Sistema centralizado para gestión de proveedores y compras</p>
                        <nav aria-label="breadcrumb">
                            <ol class="breadcrumb justify-content-center" style="background: rgba(255,255,255,0.1);">
                                <li class="breadcrumb-item"><a href="/accounts/dashboard/" style="color: white;">Inicio</a></li>
                                <li class="breadcrumb-item active" aria-current="page" style="color: rgba(255,255,255,0.8);">Gestión de Compras</li>
                            </ol>
                        </nav>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="container">
            <div class="row g-4">
                <!-- Gestión de Proveedores -->
                <div class="col-md-6 col-lg-3">
                    <div class="card module-card">
                        <div class="card-body text-center">
                            <div class="module-icon text-primary">
                                <i class="fas fa-building"></i>
                            </div>
                            <h5 class="card-title">Gestión de Proveedores</h5>
                            <p class="card-text">Administrar proveedores y sus productos</p>
                            <a href="/compras/gestion/proveedores/" class="btn btn-primary">
                                <i class="fas fa-arrow-right"></i> Acceder
                            </a>
                        </div>
                    </div>
                </div>
                
                <!-- Presentaciones -->
                <div class="col-md-6 col-lg-3">
                    <div class="card module-card">
                        <div class="card-body text-center">
                            <div class="module-icon text-success">
                                <i class="fas fa-boxes"></i>
                            </div>
                            <h5 class="card-title">Presentaciones</h5>
                            <p class="card-text">Configurar presentaciones por proveedor</p>
                            <a href="/compras/gestion/presentaciones/" class="btn btn-success">
                                <i class="fas fa-arrow-right"></i> Acceder
                            </a>
                        </div>
                    </div>
                </div>
                
                <!-- Alertas de Stock -->
                <div class="col-md-6 col-lg-3">
                    <div class="card module-card">
                        <div class="card-body text-center">
                            <div class="module-icon text-warning">
                                <i class="fas fa-exclamation-triangle"></i>
                            </div>
                            <h5 class="card-title">Alertas de Stock</h5>
                            <p class="card-text">Monitorear niveles de inventario</p>
                            <a href="/compras/gestion/alertas-stock/" class="btn btn-warning">
                                <i class="fas fa-arrow-right"></i> Acceder
                            </a>
                        </div>
                    </div>
                </div>
                
                <!-- Órdenes de Compra -->
                <div class="col-md-6 col-lg-3">
                    <div class="card module-card">
                        <div class="card-body text-center">
                            <div class="module-icon text-info">
                                <i class="fas fa-file-invoice"></i>
                            </div>
                            <h5 class="card-title">Órdenes de Compra</h5>
                            <p class="card-text">Gestionar órdenes de compra</p>
                            <a href="/compras/ordenes/" class="btn btn-info">
                                <i class="fas fa-arrow-right"></i> Acceder
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Información del Sistema -->
            <div class="row mt-5">
                <div class="col-12">
                    <div class="card">
                        <div class="card-body text-center">
                            <h5 class="card-title">
                                <i class="fas fa-info-circle text-primary"></i> 
                                Información del Sistema
                            </h5>
                            <p class="card-text">
                                Este dashboard centraliza todas las funcionalidades relacionadas con compras y proveedores. 
                                Accede rápidamente a la gestión de proveedores, configuración de presentaciones, 
                                monitoreo de alertas de stock y administración de órdenes de compra.
                            </p>
                            <small class="text-muted">
                                <i class="fas fa-lightbulb"></i> 
                                Tip: Utiliza las presentaciones dinámicas para configurar diferentes formatos de venta por proveedor.
                            </small>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Links de navegación rápida -->
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-body">
                            <h6 class="card-title">Navegación Rápida</h6>
                            <div class="d-flex flex-wrap gap-2">
                                <a href="/admin/inventario/proveedor/" class="btn btn-outline-primary btn-sm">
                                    <i class="fas fa-cog"></i> Admin Proveedores
                                </a>
                                <a href="/admin/inventario/productoproveedor/" class="btn btn-outline-primary btn-sm">
                                    <i class="fas fa-link"></i> Admin Productos-Proveedores
                                </a>
                                <a href="/admin/inventario/presentacionproveedorproducto/" class="btn btn-outline-primary btn-sm">
                                    <i class="fas fa-boxes"></i> Admin Presentaciones
                                </a>
                                <a href="/inventario/alertas-stock/" class="btn btn-outline-warning btn-sm">
                                    <i class="fas fa-exclamation-triangle"></i> Alertas Stock
                                </a>
                                <a href="/compras/ordenes/" class="btn btn-outline-info btn-sm">
                                    <i class="fas fa-shopping-cart"></i> Lista Órdenes
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    return HttpResponse(html)


@login_required
def redirigir_admin_proveedores(request):
    """Redirección al admin de proveedores de inventario"""
    from django.shortcuts import redirect
    return redirect('/admin/inventario/productoproveedor/')


@login_required
def redirigir_admin_presentaciones(request):
    """Redirección al admin de presentaciones proveedor-producto"""
    from django.shortcuts import redirect
    return redirect('/admin/inventario/presentacionproveedorproducto/')


@login_required
def redirigir_alertas_stock(request):
    """Redirección a alertas de stock de inventario"""
    from django.shortcuts import redirect
    return redirect('/inventario/alertas-stock/')
