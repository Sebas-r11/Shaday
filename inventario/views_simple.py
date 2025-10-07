from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import PresentacionProveedorProducto, ProductoProveedor, PresentacionProducto
from decimal import Decimal

@login_required
def presentaciones_proveedor_simple(request):
    """Vista simple para gestionar presentaciones proveedor-producto sin templates complejos"""
    
    # Obtener parámetros de búsqueda y filtros
    search = request.GET.get('search', '')
    proveedor_filter = request.GET.get('proveedor', '')
    disponible_filter = request.GET.get('disponible', '')
    page_number = request.GET.get('page', 1)
    
    # Construir queryset
    queryset = PresentacionProveedorProducto.objects.select_related(
        'producto_proveedor__producto',
        'producto_proveedor__proveedor',
        'presentacion_base'
    )
    
    # Aplicar filtros
    if search:
        queryset = queryset.filter(
            Q(producto_proveedor__producto__nombre__icontains=search) |
            Q(producto_proveedor__producto__codigo__icontains=search) |
            Q(producto_proveedor__proveedor__nombre__icontains=search) |
            Q(codigo_proveedor__icontains=search)
        )
    
    if proveedor_filter:
        queryset = queryset.filter(producto_proveedor__proveedor__id=proveedor_filter)
    
    if disponible_filter == 'true':
        queryset = queryset.filter(disponible=True)
    elif disponible_filter == 'false':
        queryset = queryset.filter(disponible=False)
    
    # Paginación
    paginator = Paginator(queryset, 20)
    page_obj = paginator.get_page(page_number)
    
    # Obtener lista de proveedores para el filtro
    from inventario.models import Proveedor
    proveedores = Proveedor.objects.filter(activo=True).order_by('nombre')
    
    # Generar HTML directo
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Presentaciones Proveedor-Producto - Sistema Reyes</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .header-section {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
            .btn-sm {{
                font-size: 0.75rem;
                padding: 0.25rem 0.5rem;
            }}
        </style>
    </head>
    <body class="bg-light">
        <div class="header-section">
            <div class="container">
                <div class="row align-items-center">
                    <div class="col">
                        <h1><i class="fas fa-boxes"></i> Presentaciones Proveedor-Producto</h1>
                        <nav aria-label="breadcrumb">
                            <ol class="breadcrumb mb-0" style="background: rgba(255,255,255,0.1);">
                                <li class="breadcrumb-item"><a href="/accounts/dashboard/" style="color: white;">Inicio</a></li>
                                <li class="breadcrumb-item"><a href="/compras/gestion/" style="color: white;">Compras</a></li>
                                <li class="breadcrumb-item active" aria-current="page" style="color: rgba(255,255,255,0.8);">Presentaciones</li>
                            </ol>
                        </nav>
                    </div>
                    <div class="col-auto">
                        <button class="btn btn-light" onclick="window.location.href='/admin/inventario/presentacionproveedorproducto/add/'">
                            <i class="fas fa-plus"></i> Agregar Presentación
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="container-fluid">
            <!-- Filtros -->
            <div class="card mb-4">
                <div class="card-body">
                    <form method="GET" class="row g-3">
                        <div class="col-md-4">
                            <label for="search" class="form-label">Buscar</label>
                            <input type="text" class="form-control" id="search" name="search" 
                                   value="{search}" placeholder="Producto, código o proveedor...">
                        </div>
                        <div class="col-md-3">
                            <label for="proveedor" class="form-label">Proveedor</label>
                            <select class="form-select" id="proveedor" name="proveedor">
                                <option value="">Todos los proveedores</option>
                                {''.join([f'<option value="{p.id}" {"selected" if str(p.id) == proveedor_filter else ""}>{p.nombre}</option>' for p in proveedores])}
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label for="disponible" class="form-label">Disponibilidad</label>
                            <select class="form-select" id="disponible" name="disponible">
                                <option value="">Todos</option>
                                <option value="true" {"selected" if disponible_filter == "true" else ""}>Disponibles</option>
                                <option value="false" {"selected" if disponible_filter == "false" else ""}>No disponibles</option>
                            </select>
                        </div>
                        <div class="col-md-2 d-flex align-items-end">
                            <button type="submit" class="btn btn-primary me-2">
                                <i class="fas fa-search"></i> Buscar
                            </button>
                            <a href="/inventario/presentaciones-simple/" class="btn btn-outline-secondary">
                                <i class="fas fa-times"></i>
                            </a>
                        </div>
                    </form>
                </div>
            </div>
            
            <!-- Tabla de resultados -->
            <div class="table-container">
                <div class="table-responsive">
                    <table class="table table-hover mb-0">
                        <thead class="table-dark">
                            <tr>
                                <th>Producto</th>
                                <th>Proveedor</th>
                                <th>Presentación Base</th>
                                <th>Código Proveedor</th>
                                <th>Precio Compra</th>
                                <th>Estado</th>
                                <th>Preferida</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
    """
    
    # Agregar filas de datos
    for presentacion in page_obj:
        disponible_badge = '<span class="badge bg-success status-badge">Disponible</span>' if presentacion.disponible else '<span class="badge bg-danger status-badge">No disponible</span>'
        preferida_badge = '<span class="badge bg-primary status-badge">Preferida</span>' if presentacion.es_presentacion_preferida else '<span class="badge bg-secondary status-badge">Normal</span>'
        
        html += f"""
                            <tr>
                                <td>
                                    <strong>{presentacion.producto_proveedor.producto.codigo}</strong><br>
                                    <small class="text-muted">{presentacion.producto_proveedor.producto.nombre}</small>
                                </td>
                                <td>{presentacion.producto_proveedor.proveedor.nombre}</td>
                                <td>{presentacion.presentacion_base.nombre}</td>
                                <td>{presentacion.codigo_proveedor or '-'}</td>
                                <td>${presentacion.precio_compra_presentacion:,.2f}</td>
                                <td>{disponible_badge}</td>
                                <td>{preferida_badge}</td>
                                <td>
                                    <div class="btn-group btn-group-sm">
                                        <a href="/admin/inventario/presentacionproveedorproducto/{presentacion.id}/change/" 
                                           class="btn btn-outline-primary" title="Editar">
                                            <i class="fas fa-edit"></i>
                                        </a>
                                        <button class="btn btn-outline-danger" title="Eliminar"
                                                onclick="confirmarEliminacion({presentacion.id})">
                                            <i class="fas fa-trash"></i>
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
            pagination_html += f'<li class="page-item"><a class="page-link" href="?page=1&search={search}&proveedor={proveedor_filter}&disponible={disponible_filter}">Primera</a></li>'
            pagination_html += f'<li class="page-item"><a class="page-link" href="?page={page_obj.previous_page_number()}&search={search}&proveedor={proveedor_filter}&disponible={disponible_filter}">Anterior</a></li>'
        
        # Páginas numéricas
        for num in page_obj.paginator.page_range:
            if num == page_obj.number:
                pagination_html += f'<li class="page-item active"><span class="page-link">{num}</span></li>'
            elif abs(num - page_obj.number) <= 2:
                pagination_html += f'<li class="page-item"><a class="page-link" href="?page={num}&search={search}&proveedor={proveedor_filter}&disponible={disponible_filter}">{num}</a></li>'
        
        if page_obj.has_next():
            pagination_html += f'<li class="page-item"><a class="page-link" href="?page={page_obj.next_page_number()}&search={search}&proveedor={proveedor_filter}&disponible={disponible_filter}">Siguiente</a></li>'
            pagination_html += f'<li class="page-item"><a class="page-link" href="?page={page_obj.paginator.num_pages}&search={search}&proveedor={proveedor_filter}&disponible={disponible_filter}">Última</a></li>'
        
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
            
            <!-- Información -->
            <div class="row mt-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h6 class="card-title">Estadísticas</h6>
                            <p class="card-text">
                                Total de presentaciones: <strong>{paginator.count}</strong><br>
                                Mostrando {page_obj.start_index()} - {page_obj.end_index()} de {paginator.count}
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h6 class="card-title">Enlaces Rápidos</h6>
                            <div class="d-flex flex-wrap gap-2">
                                <a href="/admin/inventario/presentacionproveedorproducto/" class="btn btn-outline-primary btn-sm">
                                    <i class="fas fa-cog"></i> Admin Django
                                </a>
                                <a href="/admin/inventario/productoproveedor/" class="btn btn-outline-secondary btn-sm">
                                    <i class="fas fa-link"></i> Productos-Proveedores
                                </a>
                                <a href="/compras/gestion/" class="btn btn-outline-info btn-sm">
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
            function confirmarEliminacion(id) {{
                if (confirm('¿Está seguro de que desea eliminar esta presentación?')) {{
                    window.location.href = '/admin/inventario/presentacionproveedorproducto/' + id + '/delete/';
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return HttpResponse(html)