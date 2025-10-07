from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
import json
from decimal import Decimal

# ==================== APIs GEOGRÁFICAS ====================

@require_http_methods(["GET"])
def api_ciudades(request):
    """API pública para obtener ciudades básicas (implementación simple)"""
    try:
        # Lista básica de ciudades colombianas principales
        ciudades_colombia = [
            {'id': 1, 'nombre': 'Bogotá', 'departamento': 'Cundinamarca', 'codigo_postal': '11001'},
            {'id': 2, 'nombre': 'Medellín', 'departamento': 'Antioquia', 'codigo_postal': '05001'},
            {'id': 3, 'nombre': 'Cali', 'departamento': 'Valle del Cauca', 'codigo_postal': '76001'},
            {'id': 4, 'nombre': 'Barranquilla', 'departamento': 'Atlántico', 'codigo_postal': '08001'},
            {'id': 5, 'nombre': 'Cartagena', 'departamento': 'Bolívar', 'codigo_postal': '13001'},
            {'id': 6, 'nombre': 'Bucaramanga', 'departamento': 'Santander', 'codigo_postal': '68001'},
            {'id': 7, 'nombre': 'Pereira', 'departamento': 'Risaralda', 'codigo_postal': '66001'},
            {'id': 8, 'nombre': 'Santa Marta', 'departamento': 'Magdalena', 'codigo_postal': '47001'},
            {'id': 9, 'nombre': 'Ibagué', 'departamento': 'Tolima', 'codigo_postal': '73001'},
            {'id': 10, 'nombre': 'Villavicencio', 'departamento': 'Meta', 'codigo_postal': '50001'},
        ]
        
        # Filtros básicos
        search = request.GET.get('search', '').strip().lower()
        departamento_filtro = request.GET.get('departamento', '').strip().lower()
        
        data = ciudades_colombia
        
        if search:
            data = [c for c in data if search in c['nombre'].lower() or search in c['departamento'].lower()]
            
        if departamento_filtro:
            data = [c for c in data if departamento_filtro in c['departamento'].lower()]
        
        return JsonResponse({
            'success': True,
            'count': len(data),
            'results': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def api_departamentos(request):
    """API pública para obtener departamentos de Colombia"""
    try:
        departamentos_colombia = [
            {'id': 1, 'nombre': 'Cundinamarca', 'codigo': 'CUN'},
            {'id': 2, 'nombre': 'Antioquia', 'codigo': 'ANT'},
            {'id': 3, 'nombre': 'Valle del Cauca', 'codigo': 'VAC'},
            {'id': 4, 'nombre': 'Atlántico', 'codigo': 'ATL'},
            {'id': 5, 'nombre': 'Bolívar', 'codigo': 'BOL'},
            {'id': 6, 'nombre': 'Santander', 'codigo': 'SAN'},
            {'id': 7, 'nombre': 'Risaralda', 'codigo': 'RIS'},
            {'id': 8, 'nombre': 'Magdalena', 'codigo': 'MAG'},
            {'id': 9, 'nombre': 'Tolima', 'codigo': 'TOL'},
            {'id': 10, 'nombre': 'Meta', 'codigo': 'MET'},
        ]
        
        return JsonResponse({
            'success': True,
            'count': len(departamentos_colombia),
            'results': departamentos_colombia
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def api_ciudades_por_departamento(request, departamento_id):
    """API para obtener ciudades de un departamento específico"""
    try:
        # Mapeo básico departamento -> ciudades
        ciudades_por_depto = {
            1: [{'id': 1, 'nombre': 'Bogotá', 'codigo_postal': '11001'}],  # Cundinamarca
            2: [{'id': 2, 'nombre': 'Medellín', 'codigo_postal': '05001'}],  # Antioquia
            3: [{'id': 3, 'nombre': 'Cali', 'codigo_postal': '76001'}],  # Valle del Cauca
            4: [{'id': 4, 'nombre': 'Barranquilla', 'codigo_postal': '08001'}],  # Atlántico
            5: [{'id': 5, 'nombre': 'Cartagena', 'codigo_postal': '13001'}],  # Bolívar
        }
        
        data = ciudades_por_depto.get(departamento_id, [])
        
        return JsonResponse({
            'success': True,
            'departamento_id': departamento_id,
            'count': len(data),
            'results': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# ==================== APIs DE PRODUCTOS ====================

@require_http_methods(["GET"])
def api_productos(request):
    """API pública para obtener productos con paginación"""
    try:
        from inventario.models import Producto
        
        # Parámetros
        search = request.GET.get('search', '').strip()
        categoria_id = request.GET.get('categoria_id')
        activos_solo = request.GET.get('activos', 'true').lower() == 'true'
        page = int(request.GET.get('page', 1))
        per_page = min(int(request.GET.get('per_page', 20)), 100)  # Max 100 por página
        
        # Query base
        productos = Producto.objects.select_related('categoria').all().order_by('id')
        
        # Filtros
        if activos_solo:
            productos = productos.filter(activo=True)
            
        if categoria_id:
            productos = productos.filter(categoria_id=categoria_id)
            
        if search:
            productos = productos.filter(
                Q(nombre__icontains=search) | 
                Q(codigo__icontains=search) |
                Q(descripcion__icontains=search)
            )
        
        # Paginación
        paginator = Paginator(productos, per_page)
        page_obj = paginator.get_page(page)
        
        # Serializar
        data = []
        for producto in page_obj:
            # Usar los campos correctos del modelo
            precio = producto.precio_minorista if hasattr(producto, 'precio_minorista') else 0.0
            data.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'codigo': producto.codigo,
                'descripcion': producto.descripcion,
                'precio_minorista': float(precio) if precio else 0.0,
                'precio_mayorista': float(producto.precio_mayorista) if hasattr(producto, 'precio_mayorista') and producto.precio_mayorista else 0.0,
                'categoria': {
                    'id': producto.categoria.id,
                    'nombre': producto.categoria.nombre
                } if producto.categoria else None,
                'activo': producto.activo
            })
        
        return JsonResponse({
            'success': True,
            'page': page,
            'per_page': per_page,
            'total': paginator.count,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'results': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def api_producto_detalle(request, producto_id):
    """API para obtener detalle de un producto específico"""
    try:
        from inventario.models import Producto
        
        producto = Producto.objects.select_related('categoria').get(id=producto_id)
        
        data = {
            'id': producto.id,
            'nombre': producto.nombre,
            'codigo': producto.codigo,
            'descripcion': producto.descripcion,
            'precio_minorista': float(producto.precio_minorista) if producto.precio_minorista else 0.0,
            'precio_mayorista': float(producto.precio_mayorista) if producto.precio_mayorista else 0.0,
            'stock_minimo': producto.stock_minimo if hasattr(producto, 'stock_minimo') else 0,
            'categoria': {
                'id': producto.categoria.id,
                'nombre': producto.categoria.nombre
            } if producto.categoria else None,
            'activo': producto.activo,
            'fecha_creacion': producto.fecha_creacion.isoformat() if hasattr(producto, 'fecha_creacion') else None
        }
        
        return JsonResponse({
            'success': True,
            'result': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=404 if 'DoesNotExist' in str(type(e)) else 500)

@require_http_methods(["GET"])
def api_buscar_productos(request):
    """API para búsqueda rápida de productos"""
    try:
        from inventario.models import Producto
        
        query = request.GET.get('q', '').strip()
        if not query:
            return JsonResponse({
                'success': False,
                'error': 'Parámetro q (query) requerido'
            }, status=400)
        
        productos = Producto.objects.filter(
            Q(nombre__icontains=query) | 
            Q(codigo__icontains=query),
            activo=True
        )[:10]  # Máximo 10 resultados
        
        data = []
        for producto in productos:
            data.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'codigo': producto.codigo,
                'precio_minorista': float(producto.precio_minorista) if producto.precio_minorista else 0.0,
                'precio_mayorista': float(producto.precio_mayorista) if producto.precio_mayorista else 0.0
            })
        
        return JsonResponse({
            'success': True,
            'query': query,
            'count': len(data),
            'results': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def api_categorias(request):
    """API para obtener categorías de productos"""
    try:
        from inventario.models import Categoria
        
        categorias = Categoria.objects.all()
        
        data = []
        for categoria in categorias:
            data.append({
                'id': categoria.id,
                'nombre': categoria.nombre,
                'descripcion': getattr(categoria, 'descripcion', ''),
                'activa': getattr(categoria, 'activa', True)
            })
        
        return JsonResponse({
            'success': True,
            'count': len(data),
            'results': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# ==================== APIs DE CRM/CLIENTES ====================

@require_http_methods(["GET"])
def api_clientes(request):
    """API pública para obtener clientes (información limitada)"""
    try:
        from ventas.models import Cliente
        
        # Solo información básica por seguridad
        search = request.GET.get('search', '').strip()
        page = int(request.GET.get('page', 1))
        per_page = min(int(request.GET.get('per_page', 20)), 50)  # Max 50
        
        clientes = Cliente.objects.all().order_by('id')
        
        if search:
            clientes = clientes.filter(
                Q(nombre_completo__icontains=search) |
                Q(numero_documento__icontains=search)
            )
        
        # Paginación
        paginator = Paginator(clientes, per_page)
        page_obj = paginator.get_page(page)
        
        data = []
        for cliente in page_obj:
            data.append({
                'id': cliente.id,
                'nombre_completo': cliente.nombre_completo,
                'numero_documento': cliente.numero_documento,
                'telefono': cliente.telefono,
                'ciudad': cliente.ciudad,  # Es un CharField, no FK
                'tipo_cliente': cliente.tipo_cliente,
                'activo': cliente.activo
            })
        
        return JsonResponse({
            'success': True,
            'page': page,
            'per_page': per_page,
            'total': paginator.count,
            'total_pages': paginator.num_pages,
            'results': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def api_cliente_detalle(request, cliente_id):
    """API para obtener detalle básico de un cliente"""
    try:
        from ventas.models import Cliente
        
        cliente = Cliente.objects.get(id=cliente_id)
        
        data = {
            'id': cliente.id,
            'nombre_completo': cliente.nombre_completo,
            'numero_documento': cliente.numero_documento,
            'telefono': cliente.telefono,
            'direccion': cliente.direccion,
            'ciudad': cliente.ciudad,  # Es un CharField
            'tipo_cliente': cliente.tipo_cliente,
            'activo': cliente.activo
        }
        
        return JsonResponse({
            'success': True,
            'result': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=404 if 'DoesNotExist' in str(type(e)) else 500)

@require_http_methods(["GET"])
def api_buscar_clientes(request):
    """API para búsqueda rápida de clientes"""
    try:
        from ventas.models import Cliente
        
        query = request.GET.get('q', '').strip()
        if not query:
            return JsonResponse({
                'success': False,
                'error': 'Parámetro q (query) requerido'
            }, status=400)
        
        clientes = Cliente.objects.filter(
            Q(nombre_completo__icontains=query) |
            Q(numero_documento__icontains=query)
        )[:10]
        
        data = []
        for cliente in clientes:
            data.append({
                'id': cliente.id,
                'nombre_completo': cliente.nombre_completo,
                'numero_documento': cliente.numero_documento,
                'telefono': cliente.telefono
            })
        
        return JsonResponse({
            'success': True,
            'query': query,
            'count': len(data),
            'results': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# ==================== APIs DE ESTADÍSTICAS ====================

@require_http_methods(["GET"])
def api_productos_populares(request):
    """API para obtener productos más vendidos"""
    try:
        from inventario.models import Producto
        
        # Esta es una implementación básica
        # En un sistema real, consultarías las ventas reales
        productos = Producto.objects.filter(activo=True).order_by('-stock_disponible')[:10]
        
        data = []
        for producto in productos:
            data.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'codigo': producto.codigo,
                'precio': float(producto.precio) if producto.precio else 0.0,
                'stock_disponible': producto.stock_disponible
            })
        
        return JsonResponse({
            'success': True,
            'count': len(data),
            'results': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def api_categorias_activas(request):
    """API para obtener categorías con productos activos"""
    try:
        from inventario.models import Categoria, Producto
        from django.db.models import Count
        
        categorias = Categoria.objects.annotate(
            total_productos=Count('producto', filter=Q(producto__activo=True))
        ).filter(total_productos__gt=0)
        
        data = []
        for categoria in categorias:
            data.append({
                'id': categoria.id,
                'nombre': categoria.nombre,
                'total_productos': categoria.total_productos
            })
        
        return JsonResponse({
            'success': True,
            'count': len(data),
            'results': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# ==================== APIs DE INFORMACIÓN ====================

@require_http_methods(["GET"])
def api_info_sistema(request):
    """API para obtener información básica del sistema"""
    try:
        from django.conf import settings
        
        data = {
            'nombre': 'Sistema de Gestión Empresarial',
            'version': '1.0.0',
            'descripcion': 'ERP completo para gestión de ventas, inventario y CRM',
            'endpoints': {
                'ciudades': '/api/ciudades/',
                'productos': '/api/productos/',
                'clientes': '/api/clientes/',
                'categorias': '/api/categorias/',
                'buscar_productos': '/api/productos/buscar/',
                'buscar_clientes': '/api/clientes/buscar/'
            },
            'documentacion': 'Disponible en /api/docs/ (próximamente)',
            'soporte_cors': True,
            'autenticacion': 'No requerida para APIs públicas'
        }
        
        return JsonResponse({
            'success': True,
            'result': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def api_version(request):
    """API para obtener versión del sistema"""
    return JsonResponse({
        'success': True,
        'version': '1.0.0',
        'build': '2025.10.07',
        'status': 'stable'
    })

# ==================== APIs ESTADÍSTICAS AVANZADAS ====================

@require_http_methods(["GET"])
def api_estadisticas_dashboard(request):
    """API para estadísticas del dashboard"""
    from ventas.general_views import api_estadisticas_dashboard as ventas_api
    return ventas_api(request)

@require_http_methods(["GET"])
def api_ventas_por_mes(request):
    """API para ventas por mes"""
    from ventas.general_views import api_ventas_por_mes as ventas_api
    return ventas_api(request)

@require_http_methods(["GET"])
def api_productos_mas_vendidos(request):
    """API para productos más vendidos"""
    from ventas.general_views import api_productos_mas_vendidos as ventas_api
    return ventas_api(request)

@require_http_methods(["GET"])
def api_estados_pedidos(request):
    """API para estados de pedidos"""
    from ventas.general_views import api_estados_pedidos as ventas_api
    return ventas_api(request)

@require_http_methods(["GET"])
def api_ventas_por_vendedor(request):
    """API para ventas por vendedor"""
    from ventas.general_views import api_ventas_por_vendedor as ventas_api
    return ventas_api(request)