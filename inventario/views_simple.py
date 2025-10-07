from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from inventario.models import PresentacionProveedorProducto


# Vistas simplificadas de inventario

@login_required
def presentaciones_proveedor_simple(request):
    """Vista simple para gestionar presentaciones proveedor-producto usando template system"""
    
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
    
    # Estadísticas
    total_presentaciones = queryset.count()
    presentaciones_disponibles = queryset.filter(disponible=True).count()
    
    context = {
        'breadcrumbs': [
            {'title': 'Inicio', 'url': '/accounts/dashboard/'},
            {'title': 'Inventario', 'url': '/inventario/'},
            {'title': 'Presentaciones Proveedor', 'url': None},
        ],
        'title': 'Presentaciones Proveedor-Producto',
        'presentaciones': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'search': search,
        'proveedor_filter': proveedor_filter,
        'disponible_filter': disponible_filter,
        'proveedores': proveedores,
        'total_presentaciones': total_presentaciones,
        'presentaciones_disponibles': presentaciones_disponibles,
        'filtros_aplicados': bool(search or proveedor_filter or disponible_filter)
    }
    
    return render(request, 'inventario/presentaciones_simple.html', context)