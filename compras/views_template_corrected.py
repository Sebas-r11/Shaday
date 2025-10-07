# Funciones corregidas para usar templates en lugar de HTML directo

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.db.models import Q, Count, F
from django.core.paginator import Paginator
from inventario.models import Proveedor, ProductoProveedor, PresentacionProveedorProducto
from decimal import Decimal

@login_required
def gestion_proveedores_simple_template(request):
    """Vista simple para gestionar proveedores usando template system"""
    
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
    
    context = {
        'breadcrumbs': [
            {'title': 'Inicio', 'url': '/accounts/dashboard/'},
            {'title': 'Compras', 'url': '/compras/gestion/'},
            {'title': 'Gestión de Proveedores', 'url': None},
        ],
        'title': 'Gestión de Proveedores',
        'proveedores': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'search': search,
        'activo_filter': activo_filter,
        'total_proveedores': total_proveedores,
        'proveedores_activos': proveedores_activos,
        'filtros_aplicados': bool(search or activo_filter)
    }
    
    return render(request, 'compras/gestion_proveedores.html', context)

@login_required
def gestion_alertas_stock_simple_template(request):
    """Vista simple para alertas de stock usando template system"""
    
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
    
    context = {
        'breadcrumbs': [
            {'title': 'Inicio', 'url': '/accounts/dashboard/'},
            {'title': 'Compras', 'url': '/compras/gestion/'},
            {'title': 'Alertas de Stock', 'url': None},
        ],
        'title': 'Alertas de Stock',
        'stocks': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'search': search,
        'categoria_filter': categoria_filter,
        'categorias': categorias,
        'total_alertas': total_alertas,
        'alertas_criticas': alertas_criticas,
        'filtros_aplicados': bool(search or categoria_filter)
    }
    
    return render(request, 'compras/gestion_alertas_stock.html', context)