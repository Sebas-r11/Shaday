# ventas/facturas_views.py
"""
Vistas especializadas para gestión de facturas
Extraído de ventas/views.py para mejorar organización
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.template.loader import render_to_string
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from io import BytesIO
import datetime

from .models import Factura, ItemFactura, Cliente
from inventario.models import Producto
from .forms import FacturaForm
# from .forms import FacturaItemFormSet  # No existe


class VentasRequiredMixin(UserPassesTestMixin):
    """Mixin para verificar permisos de ventas"""
    def test_func(self):
        return self.request.user.can_create_sales()


# ============= VISTAS DE FACTURAS =============

class FacturaListView(VentasRequiredMixin, ListView):
    """Lista de facturas"""
    model = Factura
    template_name = 'ventas/factura_list.html'
    context_object_name = 'facturas'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Factura.objects.select_related('cliente')
        
        # Filtros
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(numero__icontains=search) |
                Q(cliente__nombre__icontains=search) |
                Q(cliente__documento__icontains=search)
            )
        
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        vendedor = self.request.GET.get('vendedor')
        if vendedor:
            queryset = queryset.filter(vendedor__id=vendedor)
        
        fecha_desde = self.request.GET.get('fecha_desde')
        if fecha_desde:
            queryset = queryset.filter(fecha_creacion__date__gte=fecha_desde)
        
        fecha_hasta = self.request.GET.get('fecha_hasta')
        if fecha_hasta:
            queryset = queryset.filter(fecha_creacion__date__lte=fecha_hasta)
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_facturas'] = Factura.objects.count()
        context['facturas_pendientes'] = Factura.objects.filter(estado='pendiente').count()
        context['facturas_pagadas'] = Factura.objects.filter(estado='pagada').count()
        context['total_por_cobrar'] = Factura.objects.filter(
            estado='pendiente'
        ).aggregate(Sum('total'))['total__sum'] or 0
        return context


class FacturaCreateView(VentasRequiredMixin, CreateView):
    """Crear nueva factura"""
    model = Factura
    form_class = FacturaForm
    template_name = 'ventas/factura_form.html'
    success_url = reverse_lazy('ventas:factura_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Comentado temporalmente hasta implementar FacturaItemFormSet
        # if self.request.POST:
        #     context['items_formset'] = FacturaItemFormSet(self.request.POST)
        # else:
        #     context['items_formset'] = FacturaItemFormSet()
        return context
    
    def form_valid(self, form):
        # Simplificado temporalmente - sin formset de items
        factura = form.save()
        
        # Calcular totales si el método existe
        if hasattr(factura, 'calcular_totales'):
            factura.calcular_totales()
            factura.save()
        
        messages.success(self.request, f'Factura {factura.numero} creada exitosamente.')
        return redirect('ventas:factura_detail', pk=factura.pk)


class FacturaDetailView(VentasRequiredMixin, DetailView):
    """Detalle de factura"""
    model = Factura
    template_name = 'ventas/factura_detail.html'
    context_object_name = 'factura'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['puede_marcar_pagada'] = (
            self.request.user.can_create_sales() and 
            self.object.estado == 'pendiente'
        )
        return context


class FacturaUpdateView(VentasRequiredMixin, UpdateView):
    """Editar factura"""
    model = Factura
    form_class = FacturaForm
    template_name = 'ventas/factura_form.html'
    
    def get_queryset(self):
        # Solo permitir editar facturas pendientes
        return Factura.objects.filter(estado='pendiente')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Comentado temporalmente hasta implementar FacturaItemFormSet
        # if self.request.POST:
        #     context['items_formset'] = FacturaItemFormSet(
        #         self.request.POST, 
        #         instance=self.object
        #     )
        # else:
        #     context['items_formset'] = FacturaItemFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        # Simplificado temporalmente - sin formset de items
        factura = form.save()
        
        # Recalcular totales si el método existe
        if hasattr(factura, 'calcular_totales'):
            factura.calcular_totales()
            factura.save()
        
        messages.success(self.request, f'Factura {factura.numero} actualizada exitosamente.')
        return redirect('ventas:factura_detail', pk=factura.pk)


# ============= ACCIONES DE FACTURAS =============

@login_required
def marcar_factura_pagada(request, pk):
    """Marcar factura como pagada"""
    if not request.user.can_create_sales():
        messages.error(request, 'No tienes permisos para marcar facturas como pagadas.')
        return redirect('ventas:factura_list')
    
    factura = get_object_or_404(Factura, pk=pk)
    
    if factura.estado == 'pendiente':
        factura.estado = 'pagada'
        factura.fecha_pago = timezone.now()
        factura.usuario_pago = request.user
        factura.save()
        
        messages.success(request, f'Factura {factura.numero} marcada como pagada.')
    else:
        messages.warning(request, 'La factura ya está pagada o cancelada.')
    
    return redirect('ventas:factura_detail', pk=pk)


@login_required
def cancelar_factura(request, pk):
    """Cancelar factura"""
    if not request.user.can_create_sales():
        messages.error(request, 'No tienes permisos para cancelar facturas.')
        return redirect('ventas:factura_list')
    
    factura = get_object_or_404(Factura, pk=pk)
    
    if factura.estado == 'pagada':
        messages.error(request, 'No se puede cancelar una factura pagada.')
        return redirect('ventas:factura_detail', pk=pk)
    
    factura.estado = 'cancelada'
    factura.fecha_cancelacion = timezone.now()
    factura.usuario_cancelacion = request.user
    factura.save()
    
    # Si la factura proviene de un pedido, revertir estado del pedido
    if factura.pedido:
        factura.pedido.estado = 'completado'
        factura.pedido.save()
    
    messages.success(request, f'Factura {factura.numero} cancelada exitosamente.')
    return redirect('ventas:factura_detail', pk=pk)


# ============= REPORTES DE FACTURAS =============

@login_required
def imprimir_factura(request, pk):
    """Generar PDF de factura"""
    if not request.user.can_create_sales():
        return HttpResponse('Sin permisos', status=403)
    
    factura = get_object_or_404(Factura, pk=pk)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Título
    title = Paragraph(f"FACTURA {factura.numero}", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Información del cliente
    cliente_info = f"""
    <b>Cliente:</b> {factura.cliente.nombre_completo}<br/>
    <b>Documento:</b> {factura.cliente.numero_documento}<br/>
    <b>Teléfono:</b> {factura.cliente.telefono}<br/>
    <b>Dirección:</b> {factura.cliente.direccion}
    """
    cliente_para = Paragraph(cliente_info, styles['Normal'])
    elements.append(cliente_para)
    elements.append(Spacer(1, 12))
    
    # Información de la factura
    factura_info = f"""
    <b>Fecha:</b> {factura.fecha_creacion.strftime('%d/%m/%Y')}<br/>
    <b>Estado:</b> {factura.estado}<br/>
    """
    
    factura_para = Paragraph(factura_info, styles['Normal'])
    elements.append(factura_para)
    elements.append(Spacer(1, 12))
    
    # Tabla de items
    data = [['Producto', 'Cantidad', 'Precio Unit.', 'Descuento', 'Subtotal']]
    
    # Si hay items, agregarlos (modelo simplificado)
    if factura.items.exists():
        for item in factura.itemfactura_set.all():
            data.append([
                f'Item #{item.id}',
                str(item.cantidad),
                f'${item.precio:,.2f}',
                '0%',
                f'${item.cantidad * item.precio:,.2f}'
            ])
    else:
        # Sin items detallados
        data.append([
            'Items de factura',
            '1',
            f'${factura.total:,.2f}',
            '0%',
            f'${factura.total:,.2f}'
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # Totales
    totales_info = f"""
    <b>TOTAL:</b> ${factura.total:,.2f}
    """
    totales_para = Paragraph(totales_info, styles['Normal'])
    elements.append(totales_para)
    
    # Construir PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="factura_{factura.numero}.pdf"'
    
    return response


# ============= REPORTES Y ESTADÍSTICAS =============

@login_required
def reporte_ventas_periodo(request):
    """Reporte de ventas por período"""
    if not request.user.can_create_sales():
        return HttpResponse('Sin permisos', status=403)
    
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if not fecha_desde or not fecha_hasta:
        messages.error(request, 'Debe especificar fecha desde y fecha hasta.')
        return redirect('ventas:factura_list')
    
    facturas = Factura.objects.filter(
        fecha_creacion__date__gte=fecha_desde,
        fecha_creacion__date__lte=fecha_hasta,
        estado='pagada'
    ).select_related('cliente')
    
    # Calcular totales
    total_ventas = facturas.aggregate(Sum('total'))['total__sum'] or 0
    total_facturas = facturas.count()
    
    # Ventas por vendedor
    ventas_vendedor = facturas.values(
        'vendedor__first_name', 
        'vendedor__last_name'
    ).annotate(
        total=Sum('total'),
        cantidad=Count('id')
    ).order_by('-total')
    
    # Ventas por producto (top 10)
    from django.db.models import F
    from ventas.models import ItemFactura
    ventas_producto = ItemFactura.objects.filter(
        factura__in=facturas
    ).values(
        'producto__nombre'
    ).annotate(
        cantidad_vendida=Sum('cantidad'),
        total_vendido=Sum(F('cantidad') * F('precio_unitario'))
    ).order_by('-total_vendido')[:10]
    
    context = {
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'facturas': facturas,
        'total_ventas': total_ventas,
        'total_facturas': total_facturas,
        'ventas_vendedor': ventas_vendedor,
        'ventas_producto': ventas_producto
    }
    
    return render(request, 'ventas/reporte_ventas.html', context)


# ============= API FACTURAS =============

@login_required
def estadisticas_ventas_api(request):
    """API para estadísticas de ventas"""
    if not request.user.can_create_sales():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    # Ventas del mes actual
    from django.utils import timezone
    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)
    
    ventas_mes = Factura.objects.filter(
        fecha_creacion__date__gte=primer_dia_mes,
        estado='pagada'
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    # Facturas pendientes de pago
    facturas_pendientes = Factura.objects.filter(
        estado='pendiente'
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    # Número de ventas del día
    ventas_hoy = Factura.objects.filter(
        fecha_creacion__date=hoy,
        estado='pagada'
    ).count()
    
    return JsonResponse({
        'ventas_mes': float(ventas_mes),
        'facturas_pendientes': float(facturas_pendientes),
        'ventas_hoy': ventas_hoy
    })