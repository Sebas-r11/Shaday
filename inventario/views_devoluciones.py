from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Sum
import json
from datetime import datetime, timedelta

from .models import DevolucionVentas, DevolucionItem, Producto, MovimientoInventario


def es_bodeguero(user):
    """Verificar si el usuario es bodeguero"""
    return user.groups.filter(name='Bodegueros').exists() or user.is_superuser


@login_required
@user_passes_test(es_bodeguero)
def lista_devoluciones(request):
    """Lista de devoluciones pendientes y procesadas"""
    
    # Filtros
    estado = request.GET.get('estado', '')
    motivo = request.GET.get('motivo', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    buscar = request.GET.get('buscar', '')
    
    # Query base
    devoluciones = DevolucionVentas.objects.select_related(
        'repartidor', 'bodeguero_recibe'
    ).prefetch_related('items__producto')
    
    # Aplicar filtros
    if estado:
        devoluciones = devoluciones.filter(estado=estado)
    
    if motivo:
        devoluciones = devoluciones.filter(motivo=motivo)
    
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            devoluciones = devoluciones.filter(fecha_creacion__gte=fecha_desde_dt)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            devoluciones = devoluciones.filter(fecha_creacion__lte=fecha_hasta_dt)
        except ValueError:
            pass
    
    if buscar:
        devoluciones = devoluciones.filter(
            Q(numero_devolucion__icontains=buscar) |
            Q(cliente_nombre__icontains=buscar) |
            Q(pedido_numero__icontains=buscar)
        )
    
    # Paginación
    paginator = Paginator(devoluciones, 20)
    page = request.GET.get('page')
    devoluciones_page = paginator.get_page(page)
    
    # Estadísticas
    estadisticas = {
        'pendientes': DevolucionVentas.objects.filter(estado='pendiente').count(),
        'parciales': DevolucionVentas.objects.filter(estado='parcial').count(),
        'completas': DevolucionVentas.objects.filter(estado='completa').count(),
        'valor_pendiente': DevolucionVentas.objects.filter(
            estado__in=['pendiente', 'parcial']
        ).aggregate(total=Sum('total_valor_devuelto'))['total'] or 0,
    }
    
    context = {
        'devoluciones': devoluciones_page,
        'estadisticas': estadisticas,
        'estados': DevolucionVentas.ESTADO_CHOICES,
        'motivos': DevolucionVentas.MOTIVO_CHOICES,
        'filtros': {
            'estado': estado,
            'motivo': motivo,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'buscar': buscar,
        }
    }
    
    return render(request, 'inventario/devoluciones/lista.html', context)


@login_required
@user_passes_test(es_bodeguero)
def detalle_devolucion(request, devolucion_id):
    """Detalle de una devolución específica"""
    
    devolucion = get_object_or_404(
        DevolucionVentas.objects.select_related(
            'repartidor', 'bodeguero_recibe'
        ).prefetch_related('items__producto'),
        id=devolucion_id
    )
    
    context = {
        'devolucion': devolucion,
        'condiciones': DevolucionVentas.CONDICION_CHOICES,
    }
    
    return render(request, 'inventario/devoluciones/detalle.html', context)


@login_required
@user_passes_test(es_bodeguero)
def recibir_devolucion(request, devolucion_id):
    """Procesar recepción de devolución en bodega"""
    
    devolucion = get_object_or_404(DevolucionVentas, id=devolucion_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                datos = json.loads(request.body)
                items_recibidos = datos.get('items', [])
                observaciones_bodega = datos.get('observaciones_bodega', '')
                
                items_procesados = 0
                valor_total_recibido = 0
                
                for item_data in items_recibidos:
                    item_id = item_data.get('item_id')
                    cantidad_recibida = int(item_data.get('cantidad_recibida', 0))
                    condicion = item_data.get('condicion', 'excelente')
                    ubicacion = item_data.get('ubicacion_bodega', '')
                    observaciones_item = item_data.get('observaciones', '')
                    
                    # Buscar el item
                    try:
                        item = DevolucionItem.objects.get(
                            id=item_id, 
                            devolucion=devolucion
                        )
                    except DevolucionItem.DoesNotExist:
                        continue
                    
                    # Validar cantidad
                    if cantidad_recibida > item.cantidad_pendiente_recibir:
                        return JsonResponse({
                            'success': False,
                            'error': f'Cantidad recibida excede la pendiente para {item.producto.nombre}'
                        })
                    
                    if cantidad_recibida > 0:
                        # Actualizar item
                        item.cantidad_recibida += cantidad_recibida
                        item.condicion = condicion
                        item.ubicacion_bodega = ubicacion
                        item.observaciones = observaciones_item
                        item.fecha_recepcion = timezone.now()
                        item.save()
                        
                        # Actualizar inventario si está en buena condición
                        if item.debe_aumentar_inventario:
                            # Crear movimiento de entrada por devolución
                            MovimientoInventario.objects.create(
                                producto=item.producto,
                                tipo='entrada',
                                cantidad=cantidad_recibida,
                                motivo='devolucion_ventas',
                                observaciones=f'Devolución {devolucion.numero_devolucion} - {condicion}',
                                usuario=request.user,
                                precio_unitario=item.precio_unitario
                            )
                            
                            # Actualizar stock del producto
                            item.producto.stock_actual += cantidad_recibida
                            item.producto.save()
                        
                        items_procesados += 1
                        valor_total_recibido += cantidad_recibida * item.precio_unitario
                
                # Actualizar estado de la devolución
                if items_procesados > 0:
                    devolucion.observaciones_bodega = observaciones_bodega
                    devolucion.bodeguero_recibe = request.user
                    
                    # Verificar si está completa
                    todos_recibidos = all(
                        item.cantidad_recibida >= item.cantidad_devuelta 
                        for item in devolucion.items.all()
                    )
                    
                    if todos_recibidos:
                        devolucion.estado = 'completa'
                        devolucion.fecha_recepcion = timezone.now()
                    else:
                        devolucion.estado = 'parcial'
                    
                    devolucion.save()
                    
                    messages.success(
                        request, 
                        f'Se procesaron {items_procesados} items por valor de ${valor_total_recibido:,.0f}'
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Devolución procesada correctamente',
                        'items_procesados': items_procesados,
                        'valor_recibido': valor_total_recibido,
                        'estado': devolucion.estado
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'No se procesó ningún item'
                    })
                    
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al procesar devolución: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required  
def crear_devolucion_desde_entrega(request):
    """Crear devolución desde el sistema de entregas"""
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                datos = json.loads(request.body)
                
                # Datos básicos
                cliente_nombre = datos.get('cliente_nombre', '')
                cliente_direccion = datos.get('cliente_direccion', '')
                pedido_numero = datos.get('pedido_numero', '')
                motivo = datos.get('motivo', 'cliente_rechazo')
                observaciones = datos.get('observaciones', '')
                items = datos.get('items', [])
                
                if not cliente_nombre or not items:
                    return JsonResponse({
                        'success': False,
                        'error': 'Faltan datos requeridos'
                    })
                
                # Crear devolución
                devolucion = DevolucionVentas.objects.create(
                    repartidor=request.user,
                    cliente_nombre=cliente_nombre,
                    cliente_direccion=cliente_direccion,
                    pedido_numero=pedido_numero,
                    fecha_entrega=timezone.now(),
                    motivo=motivo,
                    observaciones_repartidor=observaciones,
                    estado='pendiente'
                )
                
                # Crear items
                total_valor = 0
                for item_data in items:
                    try:
                        producto = Producto.objects.get(id=item_data.get('producto_id'))
                    except Producto.DoesNotExist:
                        continue
                    
                    cantidad_original = int(item_data.get('cantidad_original', 0))
                    cantidad_entregada = int(item_data.get('cantidad_entregada', 0))
                    cantidad_devuelta = cantidad_original - cantidad_entregada
                    precio_unitario = float(item_data.get('precio_unitario', 0))
                    
                    if cantidad_devuelta > 0:
                        DevolucionItem.objects.create(
                            devolucion=devolucion,
                            producto=producto,
                            cantidad_original=cantidad_original,
                            cantidad_entregada=cantidad_entregada,
                            cantidad_devuelta=cantidad_devuelta,
                            precio_unitario=precio_unitario,
                            valor_devuelto=cantidad_devuelta * precio_unitario
                        )
                        
                        total_valor += cantidad_devuelta * precio_unitario
                
                # Actualizar total
                devolucion.total_valor_devuelto = total_valor
                devolucion.save()
                
                return JsonResponse({
                    'success': True,
                    'devolucion_id': devolucion.id,
                    'numero_devolucion': devolucion.numero_devolucion,
                    'message': f'Devolución {devolucion.numero_devolucion} creada correctamente'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al crear devolución: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
@user_passes_test(es_bodeguero) 
def rechazar_devolucion(request, devolucion_id):
    """Rechazar una devolución (productos no aptos para venta)"""
    
    if request.method == 'POST':
        devolucion = get_object_or_404(DevolucionVentas, id=devolucion_id)
        
        try:
            datos = json.loads(request.body)
            motivo_rechazo = datos.get('motivo_rechazo', '')
            
            devolucion.estado = 'rechazada'
            devolucion.observaciones_bodega = f'RECHAZADA: {motivo_rechazo}'
            devolucion.bodeguero_recibe = request.user
            devolucion.fecha_recepcion = timezone.now()
            devolucion.save()
            
            # Marcar todos los items como rechazados
            devolucion.items.update(
                condicion='dañado',
                observaciones=f'Rechazado: {motivo_rechazo}',
                fecha_recepcion=timezone.now()
            )
            
            messages.warning(request, f'Devolución {devolucion.numero_devolucion} rechazada')
            
            return JsonResponse({
                'success': True,
                'message': 'Devolución rechazada correctamente'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al rechazar devolución: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
@user_passes_test(es_bodeguero)
def reporte_devoluciones(request):
    """Reporte de devoluciones para análisis"""
    
    # Parámetros de fecha
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    
    if not fecha_desde:
        fecha_desde = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not fecha_hasta:
        fecha_hasta = timezone.now().strftime('%Y-%m-%d')
    
    # Filtrar devoluciones
    devoluciones = DevolucionVentas.objects.filter(
        fecha_creacion__date__gte=fecha_desde,
        fecha_creacion__date__lte=fecha_hasta
    )
    
    # Estadísticas por motivo
    estadisticas_motivo = {}
    for motivo_key, motivo_name in DevolucionVentas.MOTIVO_CHOICES:
        count = devoluciones.filter(motivo=motivo_key).count()
        valor = devoluciones.filter(motivo=motivo_key).aggregate(
            total=Sum('total_valor_devuelto')
        )['total'] or 0
        
        estadisticas_motivo[motivo_name] = {
            'cantidad': count,
            'valor': valor
        }
    
    # Productos más devueltos
    productos_devueltos = DevolucionItem.objects.filter(
        devolucion__fecha_creacion__date__gte=fecha_desde,
        devolucion__fecha_creacion__date__lte=fecha_hasta
    ).values(
        'producto__nombre', 'producto__codigo'
    ).annotate(
        total_devuelto=Sum('cantidad_devuelta'),
        valor_total=Sum('valor_devuelto')
    ).order_by('-total_devuelto')[:10]
    
    # Repartidores con más devoluciones
    repartidores_devoluciones = devoluciones.values(
        'repartidor__first_name', 'repartidor__last_name'
    ).annotate(
        total_devoluciones=models.Count('id'),
        valor_total=Sum('total_valor_devuelto')
    ).order_by('-total_devoluciones')[:10]
    
    context = {
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'estadisticas_motivo': estadisticas_motivo,
        'productos_devueltos': productos_devueltos,
        'repartidores_devoluciones': repartidores_devoluciones,
        'total_devoluciones': devoluciones.count(),
        'valor_total_devuelto': devoluciones.aggregate(
            total=Sum('total_valor_devuelto')
        )['total'] or 0,
    }
    
    return render(request, 'inventario/devoluciones/reporte.html', context)


@login_required
@user_passes_test(es_bodeguero)
def imprimir_devolucion(request, devolucion_id):
    """Vista simple para imprimir devolución"""
    devolucion = get_object_or_404(DevolucionVentas, id=devolucion_id)
    messages.info(request, 'Devolución enviada a impresión.')
    return redirect('inventario:detalle_devolucion', devolucion_id=devolucion_id)