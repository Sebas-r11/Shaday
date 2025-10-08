# ventas/cotizaciones_views.py
"""
Vistas especializadas para gestión de cotizaciones
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
from django.template.loader import render_to_string
from reportlab.pdfgen import canvas
from decimal import Decimal
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from io import BytesIO
import datetime

from .models import Cotizacion, ItemCotizacion, Cliente
from inventario.models import Producto
from .forms import CotizacionForm
# from .forms import CotizacionItemFormSet  # No existe


class VentasRequiredMixin(UserPassesTestMixin):
    """Mixin para verificar permisos de ventas"""
    def test_func(self):
        return self.request.user.can_create_sales()


# ============= VISTAS DE COTIZACIONES =============

class CotizacionListView(VentasRequiredMixin, ListView):
    """Lista de cotizaciones"""
    model = Cotizacion
    template_name = 'ventas/cotizacion_list.html'
    context_object_name = 'cotizaciones'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Cotizacion.objects.select_related('cliente')
        
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
        context['total_cotizaciones'] = Cotizacion.objects.count()
        context['cotizaciones_pendientes'] = Cotizacion.objects.filter(estado='pendiente').count()
        context['cotizaciones_aprobadas'] = Cotizacion.objects.filter(estado='aprobada').count()
        return context


class CotizacionCreateView(VentasRequiredMixin, CreateView):
    """Crear nueva cotización"""
    model = Cotizacion
    form_class = CotizacionForm
    template_name = 'ventas/cotizacion_form.html'
    success_url = reverse_lazy('ventas:cotizacion_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # FormSet temporalmente desactivado - CotizacionItemFormSet no existe
        # if self.request.POST:
        #     context['items_formset'] = CotizacionItemFormSet(self.request.POST)
        # else:
        #     context['items_formset'] = CotizacionItemFormSet()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        items_formset = context['items_formset']
        
        if form.is_valid() and items_formset.is_valid():
            form.instance.vendedor = self.request.user
            cotizacion = form.save()
            
            items_formset.instance = cotizacion
            items_formset.save()
            
            # Calcular totales
            cotizacion.calcular_totales()
            cotizacion.save()
            
            messages.success(self.request, f'Cotización {cotizacion.numero} creada exitosamente.')
            return redirect('ventas:cotizacion_detail', pk=cotizacion.pk)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class CotizacionDetailView(VentasRequiredMixin, DetailView):
    """Detalle de cotización"""
    model = Cotizacion
    template_name = 'ventas/cotizacion_detail.html'
    context_object_name = 'cotizacion'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        return context


class CotizacionUpdateView(VentasRequiredMixin, UpdateView):
    """Editar cotización"""
    model = Cotizacion
    form_class = CotizacionForm
    template_name = 'ventas/cotizacion_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # FormSet temporalmente desactivado - CotizacionItemFormSet no existe
        # if self.request.POST:
        #     context['items_formset'] = CotizacionItemFormSet(
        #         self.request.POST, 
        #         instance=self.object
        #     )
        # else:
        #     context['items_formset'] = CotizacionItemFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        # context = self.get_context_data()
        # items_formset = context['items_formset']
        
        # FormSet temporalmente desactivado
        # if form.is_valid() and items_formset.is_valid():
        if form.is_valid():
            cotizacion = form.save()
            # items_formset.save()
            
            # Recalcular totales
            cotizacion.calcular_totales()
            cotizacion.save()
            
            messages.success(self.request, f'Cotización {cotizacion.numero} actualizada exitosamente.')
            return redirect('ventas:cotizacion_detail', pk=cotizacion.pk)
        else:
            return self.render_to_response(self.get_context_data(form=form))


# ============= ACCIONES DE COTIZACIONES =============

@login_required
def aprobar_cotizacion(request, pk):
    """Aprobar cotización"""
    if not request.user.can_create_sales():
        messages.error(request, 'No tienes permisos para aprobar cotizaciones.')
        return redirect('ventas:cotizacion_list')
    
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    
    if cotizacion.estado == 'pendiente':
        cotizacion.estado = 'aprobada'
        cotizacion.save()
        
        messages.success(request, f'Cotización {cotizacion.numero} aprobada exitosamente.')
    else:
        messages.warning(request, 'La cotización ya ha sido procesada.')
    
    return redirect('ventas:cotizacion_detail', pk=pk)


@login_required
def rechazar_cotizacion(request, pk):
    """Rechazar cotización"""
    if not request.user.can_create_sales():
        messages.error(request, 'No tienes permisos para rechazar cotizaciones.')
        return redirect('ventas:cotizacion_list')
    
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    
    if cotizacion.estado == 'pendiente':
        cotizacion.estado = 'rechazada'
        cotizacion.save()
        
        messages.success(request, f'Cotización {cotizacion.numero} rechazada.')
    else:
        messages.warning(request, 'La cotización ya ha sido procesada.')
    
    return redirect('ventas:cotizacion_detail', pk=pk)


@login_required
def marcar_pendiente_cotizacion(request, pk):
    """Marcar cotización como pendiente"""
    if not request.user.can_create_sales():
        messages.error(request, 'No tienes permisos para modificar cotizaciones.')
        return redirect('ventas:cotizacion_list')
    
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    
    if cotizacion.estado == 'borrador':
        cotizacion.estado = 'pendiente'
        cotizacion.save()
        
        messages.success(request, f'Cotización {cotizacion.numero} marcada como pendiente.')
    else:
        messages.warning(request, 'Solo se pueden marcar como pendientes las cotizaciones en borrador.')
    
    return redirect('ventas:cotizacion_detail', pk=pk)


@login_required
def convertir_cotizacion_pedido(request, pk):
    """Convertir cotización a pedido"""
    if not request.user.can_create_sales():
        messages.error(request, 'No tienes permisos para convertir cotizaciones.')
        return redirect('ventas:cotizacion_list')
    
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    
    if cotizacion.estado != 'aprobada':
        messages.error(request, 'Solo se pueden convertir cotizaciones aprobadas.')
        return redirect('ventas:cotizacion_detail', pk=pk)
    
    from .models import Pedido, ItemPedido
    from datetime import datetime
    
    # Generar número único para el pedido
    año_actual = datetime.now().year
    prefijo = f"PED{año_actual}"
    
    ultimos_pedidos = Pedido.objects.filter(
        numero__startswith=prefijo
    ).order_by('-numero')
    
    if ultimos_pedidos.exists():
        ultimo_numero = ultimos_pedidos.first().numero
        try:
            # Extraer el número secuencial
            parte_numerica = ultimo_numero.replace(prefijo, '').lstrip('0') or '0'
            siguiente_numero = int(parte_numerica) + 1
        except ValueError:
            siguiente_numero = 1
    else:
        siguiente_numero = 1
    
    # Formatear con ceros a la izquierda
    numero_formateado = f"{prefijo}{siguiente_numero:03d}"
    
    # Verificar que no exista
    while Pedido.objects.filter(numero=numero_formateado).exists():
        siguiente_numero += 1
        numero_formateado = f"{prefijo}{siguiente_numero:03d}"
    
    # Crear pedido
    pedido = Pedido.objects.create(
        numero=numero_formateado,
        cliente=cotizacion.cliente,
        total=cotizacion.total,
        estado='pendiente'
    )
    
    # Copiar items
    for item in cotizacion.items.all():
        ItemPedido.objects.create(
            pedido=pedido,
            producto=item.producto,
            cantidad=item.cantidad,
            precio_unitario=item.precio_unitario
        )
    
    # Marcar cotización como convertida
    cotizacion.estado = 'convertida'
    cotizacion.save()
    
    messages.success(request, f'Cotización convertida a pedido {pedido.numero} exitosamente.')
    return redirect('ventas:pedido_detail', pk=pedido.pk)


# ============= REPORTES DE COTIZACIONES =============

@login_required
def imprimir_cotizacion(request, pk):
    """Generar PDF de cotización"""
    if not request.user.can_create_sales():
        return HttpResponse('Sin permisos', status=403)
    
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Título
    title = Paragraph(f"COTIZACIÓN {cotizacion.numero}", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Información del cliente
    cliente_info = f"""
    <b>Cliente:</b> {cotizacion.cliente.nombre_completo}<br/>
    <b>Documento:</b> {cotizacion.cliente.numero_documento}<br/>
    <b>Teléfono:</b> {cotizacion.cliente.telefono}<br/>
    <b>Dirección:</b> {cotizacion.cliente.direccion}
    """
    cliente_para = Paragraph(cliente_info, styles['Normal'])
    elements.append(cliente_para)
    elements.append(Spacer(1, 12))
    
    # Información de la cotización
    cotiz_info = f"""
    <b>Fecha:</b> {cotizacion.fecha_creacion.strftime('%d/%m/%Y')}<br/>
    <b>Estado:</b> {getattr(cotizacion, "estado", "Pendiente")}<br/>
    """
    cotiz_para = Paragraph(cotiz_info, styles['Normal'])
    elements.append(cotiz_para)
    elements.append(Spacer(1, 12))
    
    # Tabla de items
    data = [['Producto', 'Cantidad', 'Precio Unit.', 'Subtotal']]
    
    for item in cotizacion.items.all():
        data.append([
            item.producto.nombre,
            str(item.cantidad),
            f'${item.precio_unitario:,.2f}',
            f'${item.subtotal:,.2f}'
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
    <b>Subtotal:</b> ${cotizacion.total:,.2f}<br/>
    <b>Impuestos:</b> ${cotizacion.total * Decimal('0.19'):,.2f}<br/>
    <b>Total:</b> ${cotizacion.total * Decimal('1.19'):,.2f}
    """
    totales_para = Paragraph(totales_info, styles['Normal'])
    elements.append(totales_para)
    
    # Construir PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="cotizacion_{cotizacion.numero}.pdf"'
    
    return response