from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.db.models import Q, Count, F
from django.core.paginator import Paginator
from inventario.models import Proveedor, ProductoProveedor, PresentacionProveedorProducto
from decimal import Decimal

@login_required
def gestion_proveedores_simple(request):
    """Vista simple para gestionar proveedores sin templates complejos"""
    
    # Obtener parámetros de búsqueda y filtros
    search = request.GET.get('search', '')
    activo_filter = request.GET.get('activo', '')
    page_number = request.GET.get('page', 1)
    
    # Construir queryset con anotaciones
    queryset = Proveedor.objects.annotate(
        total_productos=Count('proveedor_productos'),
        total_presentaciones=Count('proveedor_productos__presentaciones_disponibles')
    ).order_by('nombre')
    
    # Aplicar filtros
    if search:
        queryset = queryset.filter(
            Q(nombre__icontains=search) |
            Q(email__icontains=search) |
            Q(telefono__icontains=search) |
            Q(ciudad__icontains=search)
        )
    
    if activo_filter == 'true':
        queryset = queryset.filter(activo=True)
    elif activo_filter == 'false':
        queryset = queryset.filter(activo=False)
    
    # Paginación
    paginator = Paginator(queryset, 15)
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_proveedores = Proveedor.objects.count()
    proveedores_activos = Proveedor.objects.filter(activo=True).count()
    
    # Generar HTML directo
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gestión de Proveedores - Sistema Reyes</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .header-section {{
                background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
                color: white;
                padding: 1.5rem 0;
                margin-bottom: 2rem;
            }}
            .table-container {{
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .status-badge {{
                font-size: 0.8rem;
                padding: 0.25rem 0.5rem;
            }}
            .provider-card {{
                border: none;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                transition: transform 0.2s;
            }}
            .provider-card:hover {{
                transform: translateY(-2px);
            }}
            .stats-icon {{
                font-size: 2rem;
                margin-bottom: 0.5rem;
            }}
        </style>
    </head>
    <body class="bg-light">
        <div class="header-section">
            <div class="container">
                <div class="row align-items-center">
                    <div class="col">
                        <h1><i class="fas fa-building"></i> Gestión de Proveedores</h1>
                        <nav aria-label="breadcrumb">
                            <ol class="breadcrumb mb-0" style="background: rgba(255,255,255,0.1);">
                                <li class="breadcrumb-item"><a href="/accounts/dashboard/" style="color: white;">Inicio</a></li>
                                <li class="breadcrumb-item"><a href="/compras/gestion/" style="color: white;">Compras</a></li>
                                <li class="breadcrumb-item active" aria-current="page" style="color: rgba(255,255,255,0.8);">Proveedores</li>
                            </ol>
                        </nav>
                    </div>
                    <div class="col-auto">
                        <button class="btn btn-light" onclick="window.location.href='/admin/inventario/proveedor/add/'">
                            <i class="fas fa-plus"></i> Agregar Proveedor
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="container-fluid">
            <!-- Estadísticas -->
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card text-center provider-card">
                        <div class="card-body">
                            <div class="stats-icon text-primary">
                                <i class="fas fa-building"></i>
                            </div>
                            <h3 class="text-primary">{total_proveedores}</h3>
                            <p class="text-muted mb-0">Total Proveedores</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center provider-card">
                        <div class="card-body">
                            <div class="stats-icon text-success">
                                <i class="fas fa-check-circle"></i>
                            </div>
                            <h3 class="text-success">{proveedores_activos}</h3>
                            <p class="text-muted mb-0">Activos</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center provider-card">
                        <div class="card-body">
                            <div class="stats-icon text-warning">
                                <i class="fas fa-pause-circle"></i>
                            </div>
                            <h3 class="text-warning">{total_proveedores - proveedores_activos}</h3>
                            <p class="text-muted mb-0">Inactivos</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center provider-card">
                        <div class="card-body">
                            <div class="stats-icon text-info">
                                <i class="fas fa-search"></i>
                            </div>
                            <h3 class="text-info">{paginator.count}</h3>
                            <p class="text-muted mb-0">Encontrados</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Filtros -->
            <div class="card mb-4">
                <div class="card-body">
                    <form method="GET" class="row g-3">
                        <div class="col-md-6">
                            <label for="search" class="form-label">Buscar Proveedor</label>
                            <input type="text" class="form-control" id="search" name="search" 
                                   value="{search}" placeholder="Nombre, email, teléfono o ciudad...">
                        </div>
                        <div class="col-md-4">
                            <label for="activo" class="form-label">Estado</label>
                            <select class="form-select" id="activo" name="activo">
                                <option value="">Todos los estados</option>
                                <option value="true" {"selected" if activo_filter == "true" else ""}>Activos</option>
                                <option value="false" {"selected" if activo_filter == "false" else ""}>Inactivos</option>
                            </select>
                        </div>
                        <div class="col-md-2 d-flex align-items-end">
                            <button type="submit" class="btn btn-primary me-2">
                                <i class="fas fa-search"></i> Buscar
                            </button>
                            <a href="/compras/gestion/proveedores/" class="btn btn-outline-secondary">
                                <i class="fas fa-times"></i>
                            </a>
                        </div>
                    </form>
                </div>
            </div>
            
            <!-- Tabla de proveedores -->
            <div class="table-container">
                <div class="table-responsive">
                    <table class="table table-hover mb-0">
                        <thead class="table-dark">
                            <tr>
                                <th>Proveedor</th>
                                <th>Contacto</th>
                                <th>Ubicación</th>
                                <th>Productos</th>
                                <th>Presentaciones</th>
                                <th>Estado</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
    """
    
    # Agregar filas de proveedores
    for proveedor in page_obj:
        activo_badge = '<span class="badge bg-success status-badge">Activo</span>' if proveedor.activo else '<span class="badge bg-danger status-badge">Inactivo</span>'
        
        # Datos de contacto
        contacto_info = []
        if proveedor.email:
            contacto_info.append(f'<small><i class="fas fa-envelope text-primary"></i> {proveedor.email}</small>')
        if proveedor.telefono:
            contacto_info.append(f'<small><i class="fas fa-phone text-success"></i> {proveedor.telefono}</small>')
        contacto_html = '<br>'.join(contacto_info) if contacto_info else '<small class="text-muted">Sin contacto</small>'
        
        # Ubicación
        ubicacion_info = []
        if proveedor.ciudad:
            ubicacion_info.append(proveedor.ciudad)
        ubicacion_html = ', '.join(ubicacion_info) if ubicacion_info else '<small class="text-muted">-</small>'
        
        html += f"""
                            <tr>
                                <td>
                                    <strong>{proveedor.nombre}</strong><br>
                                    <small class="text-muted">ID: {proveedor.id}</small>
                                </td>
                                <td>{contacto_html}</td>
                                <td>{ubicacion_html}</td>
                                <td>
                                    <span class="badge bg-primary">{proveedor.total_productos}</span>
                                </td>
                                <td>
                                    <span class="badge bg-info">{proveedor.total_presentaciones}</span>
                                </td>
                                <td>{activo_badge}</td>
                                <td>
                                    <div class="btn-group btn-group-sm">
                                        <a href="/admin/inventario/proveedor/{proveedor.id}/change/" 
                                           class="btn btn-outline-primary" title="Editar">
                                            <i class="fas fa-edit"></i>
                                        </a>
                                        <a href="/admin/inventario/productoproveedor/?proveedor__id__exact={proveedor.id}" 
                                           class="btn btn-outline-success" title="Ver Productos">
                                            <i class="fas fa-boxes"></i>
                                        </a>
                                        <button class="btn btn-outline-info" title="Ver Presentaciones"
                                                onclick="verPresentaciones({proveedor.id})">
                                            <i class="fas fa-cube"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>
        """
    
    # Paginación
    pagination_html = ""
    if page_obj.has_other_pages():
        pagination_html = f"""
                        </tbody>
                    </table>
                </div>
                <div class="card-footer">
                    <nav aria-label="Paginación">
                        <ul class="pagination justify-content-center mb-0">
        """
        
        if page_obj.has_previous():
            pagination_html += f'<li class="page-item"><a class="page-link" href="?page=1&search={search}&activo={activo_filter}">Primera</a></li>'
            pagination_html += f'<li class="page-item"><a class="page-link" href="?page={page_obj.previous_page_number()}&search={search}&activo={activo_filter}">Anterior</a></li>'
        
        # Páginas numéricas
        for num in page_obj.paginator.page_range:
            if num == page_obj.number:
                pagination_html += f'<li class="page-item active"><span class="page-link">{num}</span></li>'
            elif abs(num - page_obj.number) <= 2:
                pagination_html += f'<li class="page-item"><a class="page-link" href="?page={num}&search={search}&activo={activo_filter}">{num}</a></li>'
        
        if page_obj.has_next():
            pagination_html += f'<li class="page-item"><a class="page-link" href="?page={page_obj.next_page_number()}&search={search}&activo={activo_filter}">Siguiente</a></li>'
            pagination_html += f'<li class="page-item"><a class="page-link" href="?page={page_obj.paginator.num_pages}&search={search}&activo={activo_filter}">Última</a></li>'
        
        pagination_html += """
                        </ul>
                    </nav>
                </div>
        """
    else:
        pagination_html = """
                        </tbody>
                    </table>
                </div>
        """
    
    # Cerrar HTML
    html += pagination_html + f"""
            </div>
            
            <!-- Enlaces rápidos -->
            <div class="row mt-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h6 class="card-title">Información de Resultados</h6>
                            <p class="card-text">
                                Mostrando {page_obj.start_index()} - {page_obj.end_index()} de {paginator.count} proveedores
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h6 class="card-title">Enlaces Rápidos</h6>
                            <div class="d-flex flex-wrap gap-2">
                                <a href="/admin/inventario/proveedor/" class="btn btn-outline-primary btn-sm">
                                    <i class="fas fa-cog"></i> Admin Proveedores
                                </a>
                                <a href="/admin/inventario/productoproveedor/" class="btn btn-outline-success btn-sm">
                                    <i class="fas fa-link"></i> Productos-Proveedores
                                </a>
                                <a href="/inventario/presentaciones-simple/" class="btn btn-outline-info btn-sm">
                                    <i class="fas fa-cube"></i> Presentaciones
                                </a>
                                <a href="/compras/gestion/" class="btn btn-outline-secondary btn-sm">
                                    <i class="fas fa-arrow-left"></i> Volver
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function verPresentaciones(proveedorId) {{
                window.location.href = '/inventario/presentaciones-simple/?proveedor=' + proveedorId;
            }}
        </script>
    </body>
    </html>
    """
    
    return HttpResponse(html)


@login_required
def gestion_presentaciones_simple(request):
    """Vista simple para gestionar presentaciones (redirige a la vista ya existente)"""
    return redirect('/inventario/presentaciones-simple/')


@login_required  
def gestion_alertas_stock_simple(request):
    """Vista simple para alertas de stock sin templates complejos"""
    
    # Obtener productos con stock bajo
    from inventario.models import Stock, Producto
    
    # Parámetros
    search = request.GET.get('search', '')
    categoria_filter = request.GET.get('categoria', '')
    page_number = request.GET.get('page', 1)
    
    # Stock con alertas (stock actual <= stock mínimo)
    queryset = Stock.objects.select_related(
        'producto', 'bodega'
    ).filter(
        cantidad__lte=F('producto__stock_minimo')
    ).order_by('cantidad')
    
    # Filtros
    if search:
        queryset = queryset.filter(
            Q(producto__nombre__icontains=search) |
            Q(producto__codigo__icontains=search)
        )
    
    if categoria_filter:
        queryset = queryset.filter(producto__categoria__id=categoria_filter)
    
    # Paginación
    paginator = Paginator(queryset, 20)
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_alertas = queryset.count()
    alertas_criticas = queryset.filter(cantidad=0).count()
    
    # Categorías para filtro
    from inventario.models import Categoria
    categorias = Categoria.objects.filter(activa=True).order_by('nombre')
    
    # HTML directo
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Alertas de Stock - Sistema Reyes</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .header-section {{
                background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
                color: white;
                padding: 1.5rem 0;
                margin-bottom: 2rem;
            }}
            .alert-critical {{ background-color: #ffebee; border-left: 4px solid #f44336; }}
            .alert-warning {{ background-color: #fff3e0; border-left: 4px solid #ff9800; }}
            .stock-level {{
                font-weight: bold;
                padding: 0.25rem 0.5rem;
                border-radius: 4px;
                font-size: 0.9rem;
            }}
            .stock-critical {{ background-color: #ffcdd2; color: #c62828; }}
            .stock-low {{ background-color: #ffe0b2; color: #ef6c00; }}
        </style>
    </head>
    <body class="bg-light">
        <div class="header-section">
            <div class="container">
                <div class="row align-items-center">
                    <div class="col">
                        <h1><i class="fas fa-exclamation-triangle"></i> Alertas de Stock</h1>
                        <nav aria-label="breadcrumb">
                            <ol class="breadcrumb mb-0" style="background: rgba(255,255,255,0.1);">
                                <li class="breadcrumb-item"><a href="/accounts/dashboard/" style="color: white;">Inicio</a></li>
                                <li class="breadcrumb-item"><a href="/compras/gestion/" style="color: white;">Compras</a></li>
                                <li class="breadcrumb-item active" aria-current="page" style="color: rgba(255,255,255,0.8);">Alertas Stock</li>
                            </ol>
                        </nav>
                    </div>
                    <div class="col-auto">
                        <button class="btn btn-light" onclick="window.location.href='/inventario/generar-orden-compra/'">
                            <i class="fas fa-plus"></i> Generar Orden de Compra
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="container-fluid">
            <!-- Estadísticas de alertas -->
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <div class="text-danger" style="font-size: 2rem;">
                                <i class="fas fa-exclamation-triangle"></i>
                            </div>
                            <h3 class="text-danger">{total_alertas}</h3>
                            <p class="text-muted mb-0">Total Alertas</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <div class="text-danger" style="font-size: 2rem;">
                                <i class="fas fa-times-circle"></i>
                            </div>
                            <h3 class="text-danger">{alertas_criticas}</h3>
                            <p class="text-muted mb-0">Stock Agotado</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <div class="text-warning" style="font-size: 2rem;">
                                <i class="fas fa-exclamation"></i>
                            </div>
                            <h3 class="text-warning">{total_alertas - alertas_criticas}</h3>
                            <p class="text-muted mb-0">Stock Bajo</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <div class="text-info" style="font-size: 2rem;">
                                <i class="fas fa-shopping-cart"></i>
                            </div>
                            <h3 class="text-info">{'Generar' if total_alertas > 0 else 'No hay'}</h3>
                            <p class="text-muted mb-0">Orden de Compra</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Filtros -->
            <div class="card mb-4">
                <div class="card-body">
                    <form method="GET" class="row g-3">
                        <div class="col-md-6">
                            <label for="search" class="form-label">Buscar Producto</label>
                            <input type="text" class="form-control" id="search" name="search" 
                                   value="{search}" placeholder="Nombre o código del producto...">
                        </div>
                        <div class="col-md-4">
                            <label for="categoria" class="form-label">Categoría</label>
                            <select class="form-select" id="categoria" name="categoria">
                                <option value="">Todas las categorías</option>
                                {''.join([f'<option value="{c.id}" {"selected" if str(c.id) == categoria_filter else ""}>{c.nombre}</option>' for c in categorias])}
                            </select>
                        </div>
                        <div class="col-md-2 d-flex align-items-end">
                            <button type="submit" class="btn btn-primary me-2">
                                <i class="fas fa-search"></i> Buscar
                            </button>
                            <a href="/compras/gestion/alertas-stock/" class="btn btn-outline-secondary">
                                <i class="fas fa-times"></i>
                            </a>
                        </div>
                    </form>
                </div>
            </div>
            
            <!-- Tabla de alertas -->
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">
                        <i class="fas fa-list"></i> Productos con Stock Bajo
                        <span class="badge bg-danger ms-2">{paginator.count}</span>
                    </h5>
                </div>
                <div class="table-responsive">
                    <table class="table table-hover mb-0">
                        <thead class="table-dark">
                            <tr>
                                <th>Producto</th>
                                <th>Bodega</th>
                                <th>Stock Actual</th>
                                <th>Stock Mínimo</th>
                                <th>Diferencia</th>
                                <th>Estado</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
    """
    
    # Agregar filas de alertas
    for stock in page_obj:
        diferencia = stock.cantidad - stock.producto.stock_minimo
        
        if stock.cantidad == 0:
            estado_badge = '<span class="badge bg-danger">AGOTADO</span>'
            row_class = 'alert-critical'
        else:
            estado_badge = '<span class="badge bg-warning">BAJO</span>'
            row_class = 'alert-warning'
        
        stock_class = 'stock-critical' if stock.cantidad == 0 else 'stock-low'
        
        html += f"""
                            <tr class="{row_class}">
                                <td>
                                    <strong>{stock.producto.codigo}</strong><br>
                                    <small>{stock.producto.nombre}</small>
                                </td>
                                <td>{stock.bodega.nombre}</td>
                                <td><span class="stock-level {stock_class}">{stock.cantidad}</span></td>
                                <td>{stock.producto.stock_minimo}</td>
                                <td>
                                    <span class="badge bg-danger">{diferencia}</span>
                                </td>
                                <td>{estado_badge}</td>
                                <td>
                                    <div class="btn-group btn-group-sm">
                                        <a href="/admin/inventario/stock/{stock.id}/change/" 
                                           class="btn btn-outline-primary" title="Editar Stock">
                                            <i class="fas fa-edit"></i>
                                        </a>
                                        <button class="btn btn-outline-success" title="Reabastecer"
                                                onclick="reabastecer({stock.producto.id})">
                                            <i class="fas fa-plus"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>
        """
    
    # Cerrar HTML y paginación
    html += """
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Enlaces rápidos -->
            <div class="row mt-4">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-body">
                            <h6 class="card-title">Acciones Rápidas</h6>
                            <div class="d-flex flex-wrap gap-2">
                                <a href="/inventario/generar-orden-compra/" class="btn btn-success btn-sm">
                                    <i class="fas fa-shopping-cart"></i> Generar Orden de Compra
                                </a>
                                <a href="/admin/inventario/stock/" class="btn btn-outline-primary btn-sm">
                                    <i class="fas fa-warehouse"></i> Admin Stock
                                </a>
                                <a href="/inventario/productos/" class="btn btn-outline-info btn-sm">
                                    <i class="fas fa-boxes"></i> Ver Productos
                                </a>
                                <a href="/compras/gestion/" class="btn btn-outline-secondary btn-sm">
                                    <i class="fas fa-arrow-left"></i> Volver a Compras
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function reabastecer(productoId) {{
                if (confirm('¿Generar orden de compra para este producto?')) {{
                    window.location.href = '/inventario/generar-orden-compra/?producto=' + productoId;
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return HttpResponse(html)


@login_required
def gestion_ordenes_simple(request):
    """Vista simple para gestionar órdenes de compra sin templates complejos"""
    
    from .models import OrdenCompra, EstadoOrdenCompra
    from django.db.models import F, Count
    
    # Parámetros de filtros
    search = request.GET.get('search', '')
    estado_filter = request.GET.get('estado', '')
    proveedor_filter = request.GET.get('proveedor', '')
    page_number = request.GET.get('page', 1)
    
    # Construir queryset
    queryset = OrdenCompra.objects.select_related(
        'proveedor', 'creado_por'
    ).annotate(
        total_items=Count('items')
    ).order_by('-fecha_creacion')
    
    # Aplicar filtros
    if search:
        queryset = queryset.filter(
            Q(numero_orden__icontains=search) |
            Q(proveedor__nombre__icontains=search) |
            Q(notas__icontains=search)
        )
    
    if estado_filter:
        queryset = queryset.filter(estado=estado_filter)
    
    if proveedor_filter:
        queryset = queryset.filter(proveedor__id=proveedor_filter)
    
    # Paginación
    paginator = Paginator(queryset, 15)
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_ordenes = OrdenCompra.objects.count()
    ordenes_pendientes = OrdenCompra.objects.filter(estado='pendiente').count()
    ordenes_enviadas = OrdenCompra.objects.filter(estado='enviada').count()
    
    # Estados y proveedores para filtros
    estados = [
        ('pendiente', 'Pendiente'),
        ('enviada', 'Enviada'),
        ('recibida_parcial', 'Recibida Parcial'),
        ('recibida_total', 'Recibida Total'),
        ('cancelada', 'Cancelada')
    ]
    
    from inventario.models import Proveedor
    proveedores = Proveedor.objects.filter(activo=True).order_by('nombre')
    
    # HTML directo
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gestión de Órdenes de Compra - Sistema Reyes</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .header-section {{
                background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
                color: white;
                padding: 1.5rem 0;
                margin-bottom: 2rem;
            }}
            .order-card {{
                border: none;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                transition: transform 0.2s;
                margin-bottom: 1rem;
            }}
            .order-card:hover {{
                transform: translateY(-2px);
            }}
            .status-badge {{
                font-size: 0.8rem;
                padding: 0.4rem 0.8rem;
                border-radius: 20px;
            }}
            .stats-card {{
                border: none;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
        </style>
    </head>
    <body class="bg-light">
        <div class="header-section">
            <div class="container">
                <div class="row align-items-center">
                    <div class="col">
                        <h1><i class="fas fa-file-invoice"></i> Gestión de Órdenes de Compra</h1>
                        <nav aria-label="breadcrumb">
                            <ol class="breadcrumb mb-0" style="background: rgba(255,255,255,0.1);">
                                <li class="breadcrumb-item"><a href="/accounts/dashboard/" style="color: white;">Inicio</a></li>
                                <li class="breadcrumb-item"><a href="/compras/gestion/" style="color: white;">Compras</a></li>
                                <li class="breadcrumb-item active" aria-current="page" style="color: rgba(255,255,255,0.8);">Órdenes</li>
                            </ol>
                        </nav>
                    </div>
                    <div class="col-auto">
                        <button class="btn btn-light" onclick="window.location.href='/compras/ordenes/crear/'">
                            <i class="fas fa-plus"></i> Nueva Orden
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="container-fluid">
            <!-- Estadísticas -->
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card stats-card text-center">
                        <div class="card-body">
                            <div class="text-info" style="font-size: 2.5rem;">
                                <i class="fas fa-file-invoice"></i>
                            </div>
                            <h3 class="text-info">{total_ordenes}</h3>
                            <p class="text-muted mb-0">Total Órdenes</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stats-card text-center">
                        <div class="card-body">
                            <div class="text-warning" style="font-size: 2.5rem;">
                                <i class="fas fa-clock"></i>
                            </div>
                            <h3 class="text-warning">{ordenes_pendientes}</h3>
                            <p class="text-muted mb-0">Pendientes</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stats-card text-center">
                        <div class="card-body">
                            <div class="text-success" style="font-size: 2.5rem;">
                                <i class="fas fa-shipping-fast"></i>
                            </div>
                            <h3 class="text-success">{ordenes_enviadas}</h3>
                            <p class="text-muted mb-0">Enviadas</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stats-card text-center">
                        <div class="card-body">
                            <div class="text-primary" style="font-size: 2.5rem;">
                                <i class="fas fa-search"></i>
                            </div>
                            <h3 class="text-primary">{paginator.count}</h3>
                            <p class="text-muted mb-0">Encontradas</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Filtros -->
            <div class="card mb-4">
                <div class="card-body">
                    <form method="GET" class="row g-3">
                        <div class="col-md-4">
                            <label for="search" class="form-label">Buscar Orden</label>
                            <input type="text" class="form-control" id="search" name="search" 
                                   value="{search}" placeholder="Número de orden, proveedor o notas...">
                        </div>
                        <div class="col-md-3">
                            <label for="estado" class="form-label">Estado</label>
                            <select class="form-select" id="estado" name="estado">
                                <option value="">Todos los estados</option>
                                {''.join([f'<option value="{estado[0]}" {"selected" if estado[0] == estado_filter else ""}>{estado[1]}</option>' for estado in estados])}
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label for="proveedor" class="form-label">Proveedor</label>
                            <select class="form-select" id="proveedor" name="proveedor">
                                <option value="">Todos los proveedores</option>
                                {''.join([f'<option value="{p.id}" {"selected" if str(p.id) == proveedor_filter else ""}>{p.nombre}</option>' for p in proveedores])}
                            </select>
                        </div>
                        <div class="col-md-2 d-flex align-items-end">
                            <button type="submit" class="btn btn-primary me-2">
                                <i class="fas fa-search"></i> Buscar
                            </button>
                            <a href="/compras/ordenes/" class="btn btn-outline-secondary">
                                <i class="fas fa-times"></i>
                            </a>
                        </div>
                    </form>
                </div>
            </div>
            
            <!-- Lista de órdenes -->
            <div class="row">
    """
    
    # Agregar cards de órdenes
    for orden in page_obj:
        # Estado badge
        estado_badges = {
            'pendiente': '<span class="status-badge bg-warning text-dark">Pendiente</span>',
            'enviada': '<span class="status-badge bg-info text-white">Enviada</span>',
            'recibida_parcial': '<span class="status-badge bg-primary text-white">Recibida Parcial</span>',
            'recibida_total': '<span class="status-badge bg-success text-white">Recibida Total</span>',
            'cancelada': '<span class="status-badge bg-danger text-white">Cancelada</span>'
        }
        
        estado_badge = estado_badges.get(orden.estado, '<span class="status-badge bg-secondary text-white">Desconocido</span>')
        
        # Fecha formateada
        fecha_formateada = orden.fecha_creacion.strftime('%d/%m/%Y')
        fecha_entrega = orden.fecha_entrega_esperada.strftime('%d/%m/%Y') if orden.fecha_entrega_esperada else 'No definida'
        
        html += f"""
                <div class="col-md-6 col-lg-4">
                    <div class="card order-card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <strong>#{orden.numero_orden}</strong>
                            {estado_badge}
                        </div>
                        <div class="card-body">
                            <h6 class="card-title">
                                <i class="fas fa-building text-primary"></i> 
                                {orden.proveedor.nombre}
                            </h6>
                            <div class="mb-2">
                                <small class="text-muted">
                                    <i class="fas fa-calendar"></i> Creada: {fecha_formateada}<br>
                                    <i class="fas fa-truck"></i> Entrega: {fecha_entrega}<br>
                                    <i class="fas fa-user"></i> Por: {orden.creado_por.username if orden.creado_por else 'Sistema'}
                                </small>
                            </div>
                            <div class="mb-3">
                                <span class="badge bg-light text-dark">
                                    <i class="fas fa-boxes"></i> {orden.total_items} items
                                </span>
                                <span class="badge bg-light text-dark">
                                    <i class="fas fa-dollar-sign"></i> ${orden.total:,.2f}
                                </span>
                            </div>
                            <div class="d-flex gap-1">
                                <a href="/compras/ordenes/{orden.id}/" class="btn btn-sm btn-outline-primary flex-fill">
                                    <i class="fas fa-eye"></i> Ver
                                </a>
                                <a href="/compras/ordenes/{orden.id}/editar/" class="btn btn-sm btn-outline-secondary">
                                    <i class="fas fa-edit"></i>
                                </a>
                                <a href="/compras/ordenes/{orden.id}/imprimir/" class="btn btn-sm btn-outline-info" target="_blank">
                                    <i class="fas fa-print"></i>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
        """
    
    # Cerrar contenido
    html += """
            </div>
            
            <!-- Enlaces rápidos -->
            <div class="row mt-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h6 class="card-title">Información de Resultados</h6>
                            <p class="card-text">
                                Mostrando resultados de órdenes de compra
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h6 class="card-title">Acciones Rápidas</h6>
                            <div class="d-flex flex-wrap gap-2">
                                <a href="/compras/ordenes/crear/" class="btn btn-success btn-sm">
                                    <i class="fas fa-plus"></i> Nueva Orden
                                </a>
                                <a href="/compras/solicitudes/" class="btn btn-outline-primary btn-sm">
                                    <i class="fas fa-clipboard-list"></i> Solicitudes
                                </a>
                                <a href="/compras/reportes/" class="btn btn-outline-info btn-sm">
                                    <i class="fas fa-chart-bar"></i> Reportes
                                </a>
                                <a href="/compras/gestion/" class="btn btn-outline-secondary btn-sm">
                                    <i class="fas fa-arrow-left"></i> Volver
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