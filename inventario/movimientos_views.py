# inventario/movimientos_views.py
"""
Vistas especializadas para movimientos de inventario
Extraído de inventario/views.py para mejorar organización
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

# Imports para PDF
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

from .models import MovimientoInventario, Producto, Bodega, Stock


class AdminInventarioMixin(UserPassesTestMixin):
    """Mixin para funciones estratégicas de inventario (admins y bodega)"""
    def test_func(self):
        return (self.request.user.is_superuser or 
                self.request.user.role in ['superadmin', 'administrador', 'bodega'])


# ============= VISTAS DE MOVIMIENTOS =============

class MovimientoInventarioListView(AdminInventarioMixin, ListView):
    """Vista de movimientos de inventario - Solo para administradores"""
    model = MovimientoInventario
    template_name = 'inventario/movimiento_list.html'
    context_object_name = 'movimientos'
    paginate_by = 30
    
    def get_queryset(self):
        queryset = MovimientoInventario.objects.select_related(
            'producto', 'bodega', 'bodega_destino', 'usuario'
        ).all()
        
        # Filtros
        producto_search = self.request.GET.get('producto')
        if producto_search:
            queryset = queryset.filter(
                Q(producto__codigo__icontains=producto_search) |
                Q(producto__nombre__icontains=producto_search)
            )
        
        bodega_id = self.request.GET.get('bodega')
        if bodega_id:
            try:
                queryset = queryset.filter(bodega_id=bodega_id)
            except (ValueError, TypeError):
                pass
        
        tipo_movimiento = self.request.GET.get('tipo')
        if tipo_movimiento:
            queryset = queryset.filter(tipo_movimiento=tipo_movimiento)
        
        motivo = self.request.GET.get('motivo')
        if motivo:
            queryset = queryset.filter(motivo=motivo)
        
        fecha_desde = self.request.GET.get('fecha_desde')
        if fecha_desde:
            try:
                fecha = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_creacion__date__gte=fecha)
            except ValueError:
                pass
        
        fecha_hasta = self.request.GET.get('fecha_hasta')
        if fecha_hasta:
            try:
                fecha = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_creacion__date__lte=fecha)
            except ValueError:
                pass
        
        return queryset.order_by('-fecha_movimiento')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bodegas'] = Bodega.objects.filter(activa=True)
        
        # Estadísticas de movimientos
        context['total_movimientos_hoy'] = MovimientoInventario.objects.filter(
            fecha_movimiento__date=timezone.now().date()
        ).count()
        
        context['movimientos_por_tipo'] = MovimientoInventario.objects.values(
            'tipo_movimiento'
        ).annotate(count=Count('id')).order_by('-count')
        
        context['filtros'] = {
            'producto': self.request.GET.get('producto', ''),
            'bodega': self.request.GET.get('bodega', ''),
            'tipo': self.request.GET.get('tipo', ''),
            'motivo': self.request.GET.get('motivo', ''),
            'fecha_desde': self.request.GET.get('fecha_desde', ''),
            'fecha_hasta': self.request.GET.get('fecha_hasta', ''),
        }
        
        return context


class MovimientoInventarioDetailView(AdminInventarioMixin, DetailView):
    """Detalle de movimiento de inventario"""
    model = MovimientoInventario
    template_name = 'inventario/movimiento_detail.html'
    context_object_name = 'movimiento'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Otros movimientos del mismo producto en fechas cercanas
        fecha_desde = self.object.fecha_creacion - timedelta(days=7)
        fecha_hasta = self.object.fecha_creacion + timedelta(days=7)
        
        context['movimientos_relacionados'] = MovimientoInventario.objects.filter(
            producto=self.object.producto,
            fecha_creacion__range=[fecha_desde, fecha_hasta]
        ).exclude(id=self.object.id).order_by('-fecha_creacion')[:10]
        
        # Stock actual del producto en la bodega
        try:
            stock_actual = Stock.objects.get(
                producto=self.object.producto,
                bodega=self.object.bodega
            )
            context['stock_actual'] = stock_actual.cantidad
        except Stock.DoesNotExist:
            context['stock_actual'] = 0
        
        # Información adicional para transferencias
        if self.object.tipo_movimiento == 'transferencia' and self.object.bodega_destino:
            try:
                stock_destino = Stock.objects.get(
                    producto=self.object.producto,
                    bodega=self.object.bodega_destino
                )
                context['stock_destino_actual'] = stock_destino.cantidad
            except Stock.DoesNotExist:
                context['stock_destino_actual'] = 0
        
        return context


# ============= FUNCIONES DE AJUSTE DE INVENTARIO =============

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
                    'bodegas': Bodega.objects.filter(activa=True),
                    'motivos_ajuste': [
                        ('ajuste', 'Ajuste de inventario'),
                        ('dañado', 'Producto dañado'),
                        ('vencido', 'Producto vencido'),
                        ('perdido', 'Producto perdido'),
                        ('found', 'Producto encontrado'),
                        ('reconteo', 'Reconteo físico'),
                    ]
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
            
            if diferencia == 0:
                messages.warning(request, 'No hay diferencia en la cantidad. No se realizó ningún ajuste.')
                return render(request, 'inventario/ajuste_form.html', {
                    'productos': Producto.objects.filter(activo=True),
                    'bodegas': Bodega.objects.filter(activa=True)
                })
            
            # Actualizar stock
            with transaction.atomic():
                stock.cantidad = cantidad_nueva
                stock.save()
                
                # Registrar movimiento
                tipo_movimiento = 'entrada' if diferencia > 0 else 'salida'
                movimiento = MovimientoInventario.objects.create(
                    producto=producto,
                    bodega=bodega,
                    tipo_movimiento=tipo_movimiento,
                    motivo=motivo,
                    cantidad=abs(diferencia),
                    costo_unitario=producto.costo_promedio,
                    observaciones=f'Ajuste: {cantidad_anterior} → {cantidad_nueva}. {observaciones}',
                    usuario=request.user
                )
            
            accion = 'aumentó' if diferencia > 0 else 'redujo'
            messages.success(
                request, 
                f'Stock ajustado exitosamente: se {accion} {abs(diferencia)} unidades de {producto.nombre} '
                f'en {bodega.nombre}. Stock actual: {cantidad_nueva}'
            )
            
            # Verificar si se solicita generar PDF
            if request.POST.get('generar_pdf'):
                return generar_pdf_ajuste(request, movimiento.id)
            
            return redirect('inventario:movimiento_detail', pk=movimiento.pk)
            
        except Exception as e:
            messages.error(request, f'Error al ajustar inventario: {str(e)}')
    
    # GET request
    context = {
        'productos': Producto.objects.filter(activo=True).order_by('nombre'),
        'bodegas': Bodega.objects.filter(activa=True).order_by('nombre'),
        'motivos_ajuste': [
            ('ajuste', 'Ajuste de inventario'),
            ('dañado', 'Producto dañado'),
            ('vencido', 'Producto vencido'),
            ('perdido', 'Producto perdido'),
            ('found', 'Producto encontrado'),
            ('reconteo', 'Reconteo físico'),
        ]
    }
    
    return render(request, 'inventario/ajuste_form.html', context)


def ajuste_masivo_inventario(request):
    """Vista para ajustar múltiples productos a la vez"""
    if not request.user.can_adjust_inventory():
        messages.error(request, 'No tiene permisos para ajustar inventario.')
        return redirect('inventario:stock_list')
    
    if request.method == 'POST':
        try:
            bodega_id = request.POST.get('bodega_id')
            observaciones_generales = request.POST.get('observaciones_generales', '')
            
            if not bodega_id:
                messages.error(request, 'Debe seleccionar una bodega.')
                return render(request, 'inventario/ajuste_masivo_form.html', {
                    'bodegas': Bodega.objects.filter(activa=True)
                })
            
            bodega = get_object_or_404(Bodega, id=bodega_id)
            ajustes_realizados = 0
            
            # Procesar ajustes
            with transaction.atomic():
                for key, value in request.POST.items():
                    if key.startswith('ajuste_') and value:
                        try:
                            producto_id = key.replace('ajuste_', '')
                            cantidad_nueva = int(value)
                            
                            if cantidad_nueva < 0:
                                continue
                            
                            producto = Producto.objects.get(id=producto_id)
                            
                            # Obtener o crear stock
                            stock, created = Stock.objects.get_or_create(
                                producto=producto,
                                bodega=bodega,
                                defaults={'cantidad': 0, 'cantidad_reservada': 0}
                            )
                            
                            cantidad_anterior = stock.cantidad
                            diferencia = cantidad_nueva - cantidad_anterior
                            
                            if diferencia != 0:
                                # Actualizar stock
                                stock.cantidad = cantidad_nueva
                                stock.save()
                                
                                # Registrar movimiento
                                tipo_movimiento = 'entrada' if diferencia > 0 else 'salida'
                                MovimientoInventario.objects.create(
                                    producto=producto,
                                    bodega=bodega,
                                    tipo_movimiento=tipo_movimiento,
                                    motivo='reconteo',
                                    cantidad=abs(diferencia),
                                    costo_unitario=producto.costo_promedio,
                                    observaciones=f'Ajuste masivo: {cantidad_anterior} → {cantidad_nueva}. {observaciones_generales}',
                                    usuario=request.user
                                )
                                
                                ajustes_realizados += 1
                        
                        except (ValueError, Producto.DoesNotExist):
                            continue
            
            messages.success(
                request, 
                f'Ajuste masivo completado: {ajustes_realizados} productos ajustados en {bodega.nombre}'
            )
            
            return redirect('inventario:stock_list')
            
        except Exception as e:
            messages.error(request, f'Error en ajuste masivo: {str(e)}')
    
    # GET request
    context = {
        'bodegas': Bodega.objects.filter(activa=True).order_by('nombre')
    }
    
    # Si se seleccionó una bodega, mostrar sus productos
    bodega_id = request.GET.get('bodega_id')
    if bodega_id:
        try:
            bodega = Bodega.objects.get(id=bodega_id)
            context['bodega_seleccionada'] = bodega
            context['stocks'] = Stock.objects.filter(
                bodega=bodega
            ).select_related('producto').order_by('producto__nombre')
        except Bodega.DoesNotExist:
            pass
    
    return render(request, 'inventario/ajuste_masivo_form.html', context)


# ============= GENERACIÓN DE PDFs =============

def generar_pdf_transferencia(request, movimiento_id):
    """Vista para generar PDF del documento de transferencia"""
    movimiento = get_object_or_404(MovimientoInventario, id=movimiento_id, tipo_movimiento='transferencia')
    
    # Crear respuesta PDF
    response = HttpResponse(content_type='application/pdf')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'transferencia_{movimiento.producto.codigo}_{timestamp}.pdf'
    response['Content-Disposition'] = f'attachment; filename={filename}'
    
    # Configurar documento
    doc = SimpleDocTemplate(response, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # Estilo personalizado para título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,  # Center
        textColor=colors.navy
    )
    
    # Estilo para subtítulos
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    # Título del documento
    story.append(Paragraph("DOCUMENTO DE TRANSFERENCIA DE INVENTARIO", title_style))
    story.append(Paragraph("Sistema de Gestión de Inventario", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Información de la transferencia
    story.append(Paragraph("INFORMACIÓN GENERAL", subtitle_style))
    
    transfer_data = [
        ['Fecha de Transferencia:', movimiento.fecha_creacion.strftime('%d/%m/%Y %H:%M')],
        ['N° de Documento:', f"TR-{movimiento.id:06d}"],
        ['Usuario Responsable:', movimiento.usuario.get_full_name() or movimiento.usuario.username],
        ['', ''],  # Línea vacía
    ]
    
    transfer_table = Table(transfer_data, colWidths=[2*inch, 3*inch])
    transfer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -2), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(transfer_table)
    story.append(Spacer(1, 20))
    
    # Información de bodegas
    story.append(Paragraph("MOVIMIENTO ENTRE BODEGAS", subtitle_style))
    
    bodega_data = [
        ['BODEGA ORIGEN', 'BODEGA DESTINO'],
        [movimiento.bodega.nombre, movimiento.bodega_destino.nombre if movimiento.bodega_destino else 'N/A'],
        [movimiento.bodega.direccion or 'Sin dirección', 
         movimiento.bodega_destino.direccion or 'Sin dirección' if movimiento.bodega_destino else ''],
    ]
    
    bodega_table = Table(bodega_data, colWidths=[2.5*inch, 2.5*inch])
    bodega_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(bodega_table)
    story.append(Spacer(1, 20))
    
    # Detalle del producto
    story.append(Paragraph("DETALLE DEL PRODUCTO", subtitle_style))
    
    producto_data = [
        ['Código', 'Descripción', 'Cantidad', 'Costo Unit.', 'Total'],
        [
            movimiento.producto.codigo,
            movimiento.producto.nombre,
            str(movimiento.cantidad),
            f"${movimiento.costo_unitario:,.2f}",
            f"${movimiento.costo_unitario * movimiento.cantidad:,.2f}"
        ]
    ]
    
    producto_table = Table(producto_data, colWidths=[1*inch, 2.5*inch, 0.8*inch, 1*inch, 1*inch])
    producto_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(producto_table)
    story.append(Spacer(1, 20))
    
    # Observaciones
    if movimiento.observaciones:
        story.append(Paragraph("OBSERVACIONES", subtitle_style))
        story.append(Paragraph(movimiento.observaciones, styles['Normal']))
        story.append(Spacer(1, 30))
    else:
        story.append(Spacer(1, 50))
    
    # Firmas
    story.append(Paragraph("FIRMAS Y AUTORIZACIONES", subtitle_style))
    story.append(Spacer(1, 40))
    
    firma_data = [
        ['_____________________', '_____________________', '_____________________'],
        ['ENTREGA', 'RECIBE', 'AUTORIZA'],
        ['Responsable Bodega Origen', 'Responsable Bodega Destino', 'Supervisor'],
    ]
    
    firma_table = Table(firma_data, colWidths=[2*inch, 2*inch, 2*inch])
    firma_table.setStyle(TableStyle([
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 10),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica'),
        ('FONTSIZE', (0, 2), (-1, 2), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(firma_table)
    
    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph(
        f"Documento generado automáticamente el {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=1)
    ))
    
    # Construir PDF
    doc.build(story)
    
    return response


def generar_pdf_ajuste(request, movimiento_id):
    """Vista para generar PDF del documento de ajuste"""
    movimiento = get_object_or_404(MovimientoInventario, id=movimiento_id, motivo__in=['ajuste', 'reconteo', 'dañado', 'vencido', 'perdido', 'found'])
    
    # Crear respuesta PDF
    response = HttpResponse(content_type='application/pdf')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'ajuste_{movimiento.producto.codigo}_{timestamp}.pdf'
    response['Content-Disposition'] = f'attachment; filename={filename}'
    
    # Configurar documento
    doc = SimpleDocTemplate(response, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # Título del documento
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,
        textColor=colors.navy
    )
    
    story.append(Paragraph("DOCUMENTO DE AJUSTE DE INVENTARIO", title_style))
    story.append(Paragraph("Sistema de Gestión de Inventario", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Información del ajuste
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    story.append(Paragraph("INFORMACIÓN DEL AJUSTE", subtitle_style))
    
    ajuste_data = [
        ['Fecha del Ajuste:', movimiento.fecha_creacion.strftime('%d/%m/%Y %H:%M')],
        ['N° de Documento:', f"AJ-{movimiento.id:06d}"],
        ['Usuario Responsable:', movimiento.usuario.get_full_name() or movimiento.usuario.username],
        ['Motivo:', dict(movimiento.MOTIVOS_CHOICES).get(movimiento.motivo, movimiento.motivo)],
        ['Bodega:', movimiento.bodega.nombre],
    ]
    
    ajuste_table = Table(ajuste_data, colWidths=[2*inch, 3*inch])
    ajuste_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(ajuste_table)
    story.append(Spacer(1, 20))
    
    # Detalle del producto
    story.append(Paragraph("DETALLE DEL AJUSTE", subtitle_style))
    
    # Extraer cantidad anterior de las observaciones si está disponible
    cantidad_anterior = 'N/A'
    if '→' in movimiento.observaciones:
        try:
            parte_cantidad = movimiento.observaciones.split('→')[0].split(':')[-1].strip()
            cantidad_anterior = parte_cantidad
        except:
            pass
    
    tipo_ajuste = "AUMENTO" if movimiento.tipo_movimiento == 'entrada' else "REDUCCIÓN"
    
    detalle_data = [
        ['Producto', 'Cantidad Anterior', 'Cantidad Ajustada', 'Tipo de Ajuste', 'Valor Unit.'],
        [
            f"{movimiento.producto.codigo} - {movimiento.producto.nombre}",
            cantidad_anterior,
            str(movimiento.cantidad),
            tipo_ajuste,
            f"${movimiento.costo_unitario:,.2f}"
        ]
    ]
    
    detalle_table = Table(detalle_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1*inch, 1*inch])
    detalle_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(detalle_table)
    story.append(Spacer(1, 20))
    
    # Observaciones
    if movimiento.observaciones:
        story.append(Paragraph("OBSERVACIONES", subtitle_style))
        story.append(Paragraph(movimiento.observaciones, styles['Normal']))
        story.append(Spacer(1, 30))
    
    # Firmas
    story.append(Paragraph("FIRMAS Y AUTORIZACIONES", subtitle_style))
    story.append(Spacer(1, 40))
    
    firma_data = [
        ['_____________________', '_____________________'],
        ['RESPONSABLE', 'SUPERVISOR'],
        ['Quien realizó el ajuste', 'Quien autoriza'],
    ]
    
    firma_table = Table(firma_data, colWidths=[3*inch, 3*inch])
    firma_table.setStyle(TableStyle([
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 10),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica'),
        ('FONTSIZE', (0, 2), (-1, 2), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(firma_table)
    
    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph(
        f"Documento generado automáticamente el {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=1)
    ))
    
    # Construir PDF
    doc.build(story)
    
    return response


# ============= APIS DE MOVIMIENTOS =============

def estadisticas_movimientos_api(request):
    """API para estadísticas de movimientos"""
    if not request.user.can_view_inventory():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    # Movimientos del día
    hoy = timezone.now().date()
    movimientos_hoy = MovimientoInventario.objects.filter(fecha_creacion__date=hoy)
    
    # Movimientos por tipo
    movimientos_por_tipo = MovimientoInventario.objects.values(
        'tipo_movimiento'
    ).annotate(count=Count('id')).order_by('-count')
    
    # Movimientos por motivo
    movimientos_por_motivo = MovimientoInventario.objects.values(
        'motivo'
    ).annotate(count=Count('id')).order_by('-count')[:10]
    
    return JsonResponse({
        'movimientos_hoy': movimientos_hoy.count(),
        'entradas_hoy': movimientos_hoy.filter(tipo_movimiento='entrada').count(),
        'salidas_hoy': movimientos_hoy.filter(tipo_movimiento='salida').count(),
        'transferencias_hoy': movimientos_hoy.filter(tipo_movimiento='transferencia').count(),
        'movimientos_por_tipo': list(movimientos_por_tipo),
        'movimientos_por_motivo': list(movimientos_por_motivo),
        'total_movimientos': MovimientoInventario.objects.count()
    })


def movimientos_recientes_api(request):
    """API para obtener movimientos recientes"""
    if not request.user.can_view_inventory():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    limite = int(request.GET.get('limite', 10))
    producto_id = request.GET.get('producto_id')
    bodega_id = request.GET.get('bodega_id')
    
    queryset = MovimientoInventario.objects.select_related(
        'producto', 'bodega', 'bodega_destino', 'usuario'
    )
    
    if producto_id:
        queryset = queryset.filter(producto_id=producto_id)
    
    if bodega_id:
        queryset = queryset.filter(bodega_id=bodega_id)
    
    movimientos = queryset.order_by('-fecha_creacion')[:limite]
    
    data = []
    for movimiento in movimientos:
        data.append({
            'id': movimiento.id,
            'fecha': movimiento.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            'producto': {
                'id': movimiento.producto.id,
                'codigo': movimiento.producto.codigo,
                'nombre': movimiento.producto.nombre
            },
            'bodega': movimiento.bodega.nombre,
            'bodega_destino': movimiento.bodega_destino.nombre if movimiento.bodega_destino else None,
            'tipo_movimiento': movimiento.tipo_movimiento,
            'motivo': movimiento.motivo,
            'cantidad': movimiento.cantidad,
            'usuario': movimiento.usuario.get_full_name() or movimiento.usuario.username
        })
    
    return JsonResponse(data, safe=False)