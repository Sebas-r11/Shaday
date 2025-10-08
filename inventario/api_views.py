# inventario/api_views.py
# Vistas API y AJAX para el módulo de inventario

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Q, F, Sum, Count, Avg
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
import json

# Importaciones locales
from .models import (
    Producto, Categoria, Subcategoria, MovimientoInventario,
    Stock, Bodega, ProductoProveedor, PresentacionProveedorProducto,
    RecomendacionReposicion
)

# ========================================
# APIs PARA CARGAR DATOS DINÁMICOS
# ========================================

def subcategorias_api(request):
    """API para obtener subcategorías por categoría"""
    categoria_id = request.GET.get('categoria')
    
    if categoria_id:
        subcategorias = Subcategoria.objects.filter(
            categoria_id=categoria_id, 
            activa=True
        ).values('id', 'nombre')
        return JsonResponse(list(subcategorias), safe=False)
    
    return JsonResponse([], safe=False)


def stock_api(request):
    """API para obtener stock actual de un producto en una bodega"""
    producto_id = request.GET.get('producto')
    bodega_id = request.GET.get('bodega')
    
    if producto_id and bodega_id:
        try:
            stock = Stock.objects.get(producto_id=producto_id, bodega_id=bodega_id)
            return JsonResponse({'stock': stock.cantidad})
        except Stock.DoesNotExist:
            return JsonResponse({'stock': 0})
    
    return JsonResponse({'error': 'Parámetros inválidos'}, status=400)


def obtener_presentaciones_proveedor(request, proveedor_id, producto_id):
    """Vista API para obtener presentaciones disponibles de un proveedor para un producto específico"""
    try:
        # Verificar que el usuario tenga permisos
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'No autorizado'}, status=401)
        
        # Obtener la relación producto-proveedor
        try:
            producto_proveedor = ProductoProveedor.objects.get(
                id=proveedor_id,
                producto_id=producto_id
            )
        except ProductoProveedor.DoesNotExist:
            return JsonResponse({'error': 'Relación producto-proveedor no encontrada'}, status=404)
        
        # Obtener presentaciones disponibles para este proveedor
        presentaciones = producto_proveedor.presentaciones_disponibles.filter(
            disponible=True
        ).select_related('presentacion_base').order_by('es_presentacion_preferida', 'presentacion_base__orden')
        
        presentaciones_data = []
        for pres_prov in presentaciones:
            presentaciones_data.append({
                'id': pres_prov.id,
                'nombre': pres_prov.presentacion_base.nombre,
                'unidades_por_presentacion': pres_prov.presentacion_base.unidades_por_presentacion,
                'precio_compra_presentacion': float(pres_prov.precio_compra_presentacion),
                'es_presentacion_preferida': pres_prov.es_presentacion_preferida,
                'codigo_proveedor': pres_prov.codigo_proveedor,
                'tiempo_entrega_dias': pres_prov.tiempo_entrega_dias,
                'descuento_volumen': float(pres_prov.descuento_volumen) if pres_prov.descuento_volumen else 0,
                'cantidad_descuento': pres_prov.cantidad_descuento
            })
        
        return JsonResponse({
            'presentaciones': presentaciones_data,
            'proveedor': producto_proveedor.proveedor.nombre,
            'producto': producto_proveedor.producto.codigo
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def buscar_productos_api(request):
    """API para buscar productos por código o nombre"""
    query = request.GET.get('q', '').strip()
    limite = int(request.GET.get('limit', 20))
    
    if not query or len(query) < 2:
        return JsonResponse({'productos': []})
    
    # Buscar por código o nombre
    productos = Producto.objects.filter(
        Q(codigo__icontains=query) | Q(nombre__icontains=query),
        activo=True
    ).select_related('categoria', 'subcategoria')[:limite]
    
    productos_data = []
    for producto in productos:
        # Calcular stock total de todas las bodegas
        stock_total = sum(stock.cantidad for stock in producto.stock.all()) if hasattr(producto, 'stock') else 0
        
        productos_data.append({
            'id': producto.id,
            'codigo': producto.codigo,
            'nombre': producto.nombre,
            'categoria': producto.categoria.nombre if producto.categoria else '',
            'stock_actual': stock_total,
            'precio_venta': float(producto.precio_minorista or 0),
            'precio_minorista': float(producto.precio_minorista or 0),
            'precio_mayorista': float(producto.precio_mayorista or 0),
            'activo': producto.activo
        })
    
    return JsonResponse({'productos': productos_data})


def productos_por_categoria_api(request):
    """API para obtener productos filtrados por categoría"""
    categoria_id = request.GET.get('categoria')
    subcategoria_id = request.GET.get('subcategoria')
    
    productos = Producto.objects.filter(activo=True)
    
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    
    if subcategoria_id:
        productos = productos.filter(subcategoria_id=subcategoria_id)
    
    productos = productos.select_related('categoria', 'subcategoria')[:100]
    
    productos_data = []
    for producto in productos:
        productos_data.append({
            'id': producto.id,
            'codigo': producto.codigo,
            'nombre': producto.nombre,
            'stock_actual': producto.stock_actual,
            'precio_venta': float(producto.precio_venta) if producto.precio_venta else 0
        })
    
    return JsonResponse({'productos': productos_data})


def stock_por_bodega_api(request):
    """API para obtener stock de un producto en todas las bodegas"""
    producto_id = request.GET.get('producto')
    
    if not producto_id:
        return JsonResponse({'error': 'ID de producto requerido'}, status=400)
    
    try:
        producto = Producto.objects.get(id=producto_id, activo=True)
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)
    
    stocks = Stock.objects.filter(
        producto=producto
    ).select_related('bodega').filter(bodega__activa=True)
    
    stocks_data = []
    for stock in stocks:
        stocks_data.append({
            'bodega_id': stock.bodega.id,
            'bodega_nombre': stock.bodega.nombre,
            'cantidad': stock.cantidad,
            'stock_minimo': stock.stock_minimo,
            'stock_maximo': stock.stock_maximo
        })
    
    return JsonResponse({
        'producto': {
            'id': producto.id,
            'codigo': producto.codigo,
            'nombre': producto.nombre
        },
        'stocks': stocks_data,
        'total_stock': producto.stock_actual
    })


# ========================================
# APIs PARA AJUSTES DE INVENTARIO
# ========================================

@csrf_exempt
def crear_ajuste_inventario(request):
    """Vista para crear ajustes de inventario (entradas y salidas)"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    # Verificar permisos de inventario
    if not (request.user.is_superuser or 
            request.user.role in ['superadmin', 'administrador'] or
            hasattr(request.user, 'can_adjust_inventory') and request.user.can_adjust_inventory()):
        return JsonResponse({'error': 'Sin permisos para ajustar inventario'}, status=403)
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            producto_id = request.POST.get('producto_id')
            bodega_id = request.POST.get('bodega_id')
            tipo_movimiento = request.POST.get('tipo_movimiento')  # 'entrada' o 'salida'
            cantidad = int(request.POST.get('cantidad', 0))
            motivo_form = request.POST.get('motivo', '')
            observaciones = request.POST.get('observaciones', '')
            
            # Mapear motivos del formulario a opciones del modelo
            motivos_map = {
                'Compra': 'compra',
                'Ajuste inicial': 'ajuste_inventario',
                'Corrección': 'ajuste_inventario',
                'Producto dañado': 'producto_dañado',
                'Producto vencido': 'producto_vencido',
                'Pérdida': 'ajuste_inventario',
                'Promoción': 'ajuste_inventario',
                'Otro': 'ajuste_inventario',
            }
            
            motivo = motivos_map.get(motivo_form, 'ajuste_inventario')
            
            # Validaciones
            if not all([producto_id, bodega_id, tipo_movimiento, cantidad]):
                return JsonResponse({'error': 'Todos los campos son requeridos'}, status=400)
            
            if cantidad <= 0:
                return JsonResponse({'error': 'La cantidad debe ser mayor a 0'}, status=400)
            
            if tipo_movimiento not in ['entrada', 'salida']:
                return JsonResponse({'error': 'Tipo de movimiento inválido'}, status=400)
            
            # Obtener objetos
            try:
                producto = Producto.objects.get(id=producto_id, activo=True)
                bodega = Bodega.objects.get(id=bodega_id, activa=True)
            except (Producto.DoesNotExist, Bodega.DoesNotExist):
                return JsonResponse({'error': 'Producto o bodega no encontrados'}, status=404)
            
            # Realizar ajuste en transacción
            with transaction.atomic():
                # Obtener o crear stock
                stock, created = Stock.objects.get_or_create(
                    producto=producto,
                    bodega=bodega,
                    defaults={'cantidad': 0}
                )
                
                stock_anterior = stock.cantidad
                
                # Aplicar ajuste según el tipo
                if tipo_movimiento == 'entrada':
                    stock.cantidad += cantidad
                elif tipo_movimiento == 'salida':
                    if stock.cantidad < cantidad:
                        return JsonResponse({
                            'error': f'Stock insuficiente. Disponible: {stock.cantidad}, solicitado: {cantidad}'
                        }, status=400)
                    stock.cantidad -= cantidad
                
                stock.save()
                
                # Actualizar stock total del producto
                producto.actualizar_stock_total()
                
                # Crear movimiento de inventario
                movimiento = MovimientoInventario.objects.create(
                    producto=producto,
                    bodega_origen=bodega if tipo_movimiento == 'salida' else None,
                    bodega_destino=bodega if tipo_movimiento == 'entrada' else None,
                    tipo='ajuste',
                    cantidad=cantidad if tipo_movimiento == 'entrada' else -cantidad,
                    motivo=motivo,
                    observaciones=f'{motivo_form or f"Ajuste de {tipo_movimiento}"}. Stock anterior: {stock_anterior}, Stock actual: {stock.cantidad}. {observaciones}',
                    usuario=request.user
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'Ajuste de {tipo_movimiento} realizado exitosamente',
                    'movimiento_id': str(movimiento.id),
                    'stock_anterior': stock_anterior,
                    'stock_actual': stock.cantidad,
                    'cantidad_ajustada': cantidad,
                    'pdf_url': f'/inventario/ajustes/{movimiento.id}/pdf/'
                })
                
        except ValueError as e:
            return JsonResponse({'error': f'Error en los datos: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@csrf_exempt
def ajuste_masivo_inventario(request):
    """API para realizar ajustes masivos de inventario"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    if not (request.user.is_superuser or 
            request.user.role in ['superadmin', 'administrador']):
        return JsonResponse({'error': 'Sin permisos para ajustes masivos'}, status=403)
    
    if request.method == 'POST':
        try:
            # Obtener datos JSON
            data = json.loads(request.body)
            ajustes = data.get('ajustes', [])
            motivo_general = data.get('motivo', 'Ajuste masivo de inventario')
            observaciones_general = data.get('observaciones', '')
            
            if not ajustes:
                return JsonResponse({'error': 'No se proporcionaron ajustes'}, status=400)
            
            resultados = []
            errores = []
            
            # Procesar ajustes en transacción
            with transaction.atomic():
                for i, ajuste in enumerate(ajustes):
                    try:
                        producto_id = ajuste.get('producto_id')
                        bodega_id = ajuste.get('bodega_id')
                        nueva_cantidad = int(ajuste.get('nueva_cantidad', 0))
                        
                        # Obtener objetos
                        producto = Producto.objects.get(id=producto_id, activo=True)
                        bodega = Bodega.objects.get(id=bodega_id, activa=True)
                        
                        # Obtener o crear stock
                        stock, created = Stock.objects.get_or_create(
                            producto=producto,
                            bodega=bodega,
                            defaults={'cantidad': 0}
                        )
                        
                        stock_anterior = stock.cantidad
                        diferencia = nueva_cantidad - stock_anterior
                        
                        if diferencia != 0:
                            # Actualizar stock
                            stock.cantidad = nueva_cantidad
                            stock.save()
                            
                            # Actualizar stock total del producto
                            producto.actualizar_stock_total()
                            
                            # Crear movimiento
                            MovimientoInventario.objects.create(
                                producto=producto,
                                bodega_origen=bodega if diferencia < 0 else None,
                                bodega_destino=bodega if diferencia > 0 else None,
                                tipo='ajuste',
                                cantidad=diferencia,
                                motivo='ajuste_inventario',
                                observaciones=f'{motivo_general}. Stock anterior: {stock_anterior}, Stock nuevo: {nueva_cantidad}. {observaciones_general}',
                                usuario=request.user
                            )
                            
                            resultados.append({
                                'producto': producto.codigo,
                                'bodega': bodega.nombre,
                                'stock_anterior': stock_anterior,
                                'stock_nuevo': nueva_cantidad,
                                'diferencia': diferencia
                            })
                        
                    except Exception as e:
                        errores.append({
                            'indice': i,
                            'error': str(e)
                        })
            
            return JsonResponse({
                'success': True,
                'message': f'Ajuste masivo completado. {len(resultados)} productos actualizados.',
                'resultados': resultados,
                'errores': errores
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


# ========================================
# APIs PARA REPORTES Y ESTADÍSTICAS
# ========================================

def validar_codigo_producto_api(request):
    """API para validar si un código de producto ya existe"""
    codigo = request.GET.get('codigo', '').strip()
    producto_id = request.GET.get('producto_id')  # Para excluir en edición
    
    if not codigo:
        return JsonResponse({'valido': False, 'mensaje': 'Código requerido'})
    
    query = Producto.objects.filter(codigo=codigo)
    
    # Excluir el producto actual en caso de edición
    if producto_id:
        query = query.exclude(id=producto_id)
    
    existe = query.exists()
    
    return JsonResponse({
        'valido': not existe,
        'mensaje': 'Código disponible' if not existe else 'Código ya existe'
    })


def historial_movimientos_api(request):
    """API para obtener historial de movimientos de un producto"""
    producto_id = request.GET.get('producto')
    limite = int(request.GET.get('limit', 50))
    
    if not producto_id:
        return JsonResponse({'error': 'ID de producto requerido'}, status=400)
    
    try:
        producto = Producto.objects.get(id=producto_id, activo=True)
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)
    
    movimientos = MovimientoInventario.objects.filter(
        producto=producto
    ).select_related(
        'bodega_origen', 'bodega_destino', 'usuario'
    ).order_by('-fecha_movimiento')[:limite]
    
    movimientos_data = []
    for mov in movimientos:
        movimientos_data.append({
            'id': str(mov.id),
            'fecha': mov.fecha_movimiento.strftime('%Y-%m-%d %H:%M'),
            'tipo': mov.tipo,
            'cantidad': mov.cantidad,
            'bodega_origen': mov.bodega_origen.nombre if mov.bodega_origen else None,
            'bodega_destino': mov.bodega_destino.nombre if mov.bodega_destino else None,
            'motivo': mov.get_motivo_display(),
            'observaciones': mov.observaciones,
            'usuario': mov.usuario.get_full_name() if mov.usuario else 'Sistema'
        })
    
    return JsonResponse({
        'producto': {
            'id': producto.id,
            'codigo': producto.codigo,
            'nombre': producto.nombre
        },
        'movimientos': movimientos_data
    })


def productos_bajo_stock_api(request):
    """API para obtener productos con stock bajo o crítico"""
    tipo = request.GET.get('tipo', 'bajo')  # 'bajo', 'critico', 'sin_stock'
    limite = int(request.GET.get('limit', 100))
    
    productos = Producto.objects.filter(activo=True).select_related('categoria')
    
    if tipo == 'sin_stock':
        productos = productos.filter(stock_actual=0)
    elif tipo == 'critico':
        productos = productos.filter(stock_actual__lte=F('stock_minimo'))
    elif tipo == 'bajo':
        productos = productos.filter(
            stock_actual__lte=F('stock_minimo') * 1.5,
            stock_actual__gt=0
        )
    
    productos = productos.order_by('stock_actual')[:limite]
    
    productos_data = []
    for producto in productos:
        productos_data.append({
            'id': producto.id,
            'codigo': producto.codigo,
            'nombre': producto.nombre,
            'categoria': producto.categoria.nombre if producto.categoria else '',
            'stock_actual': producto.stock_actual,
            'stock_minimo': producto.stock_minimo,
            'stock_maximo': producto.stock_maximo,
            'dias_sin_stock': (timezone.now().date() - producto.fecha_ultimo_movimiento).days if producto.fecha_ultimo_movimiento else None
        })
    
    return JsonResponse({
        'tipo': tipo,
        'total': len(productos_data),
        'productos': productos_data
    })