# compras/general_views.py
# Vistas generales, utilidades y funciones de apoyo para el módulo de compras

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages

# ========================================
# DASHBOARD PRINCIPAL DE GESTIÓN
# ========================================

@login_required
def gestion_compras_dashboard(request):
    """Dashboard centralizado simplificado para gestión de compras y proveedores"""
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    
    context = {
        'breadcrumbs': [
            {'title': 'Inicio', 'url': '/accounts/dashboard/'},
            {'title': 'Gestión de Compras', 'url': None},
        ],
        'title': 'Gestión de Compras',
        'user': request.user,
        'modules': [
            {
                'title': 'Gestión de Proveedores',
                'description': 'Administrar proveedores y sus productos',
                'icon': 'fas fa-users-cog',
                'color': 'blue',
                'url': '/admin/inventario/proveedor/'
            },
            {
                'title': 'Productos por Proveedor',
                'description': 'Gestionar relación productos-proveedores',
                'icon': 'fas fa-link',
                'color': 'green',
                'url': '/admin/inventario/productoproveedor/'
            },
            {
                'title': 'Presentaciones',
                'description': 'Configurar presentaciones por proveedor',
                'icon': 'fas fa-boxes',
                'color': 'green',
                'url': '/admin/inventario/presentacionproveedorproducto/'
            },
            {
                'title': 'Alertas de Stock',
                'description': 'Monitorear niveles de inventario',
                'icon': 'fas fa-exclamation-triangle',
                'color': 'yellow',
                'url': '/inventario/alertas-stock/'
            },
            {
                'title': 'Órdenes de Compra',
                'description': 'Gestionar órdenes de compra',
                'icon': 'fas fa-file-invoice',
                'color': 'purple',
                'url': '/compras/ordenes/'
            }
        ],
        'quick_links': [
            {
                'title': 'Admin Proveedores',
                'icon': 'fas fa-cog',
                'url': '/admin/inventario/proveedor/',
                'color': 'blue'
            },
            {
                'title': 'Admin Productos-Proveedores', 
                'icon': 'fas fa-link',
                'url': '/admin/inventario/productoproveedor/',
                'color': 'blue'
            },
            {
                'title': 'Admin Presentaciones',
                'icon': 'fas fa-boxes',
                'url': '/admin/inventario/presentacionproveedorproducto/',
                'color': 'blue'
            },
            {
                'title': 'Alertas Stock',
                'icon': 'fas fa-exclamation-triangle',
                'url': '/inventario/alertas-stock/',
                'color': 'yellow'
            },
            {
                'title': 'Lista Órdenes',
                'icon': 'fas fa-shopping-cart',
                'url': '/compras/ordenes/',
                'color': 'purple'
            }
        ]
    }
    
    return render(request, 'compras/gestion_dashboard.html', context)


@login_required
def compras_ayuda(request):
    """Vista de ayuda para el módulo de compras"""
    context = {
        'titulo': 'Ayuda - Módulo de Compras',
        'breadcrumbs': [
            {'title': 'Inicio', 'url': '/accounts/dashboard/'},
            {'title': 'Compras', 'url': '/compras/'},
            {'title': 'Ayuda', 'url': None},
        ],
        'secciones': [
            {
                'titulo': 'Gestión de Proveedores',
                'contenido': 'Aprende a administrar el catálogo de proveedores...',
                'icono': 'fas fa-users'
            },
            {
                'titulo': 'Órdenes de Compra',
                'contenido': 'Cómo crear y gestionar órdenes de compra...',
                'icono': 'fas fa-file-invoice'
            }
        ]
    }
    return render(request, 'compras/ayuda.html', context)


# ========================================
# FUNCIONES DE REDIRECCIÓN Y NAVEGACIÓN
# ========================================

@login_required
def redirigir_admin_proveedores(request):
    """Redirección al admin de proveedores de inventario"""
    return redirect('/admin/inventario/productoproveedor/')


@login_required
def redirigir_admin_presentaciones(request):
    """Redirección al admin de presentaciones proveedor-producto"""
    return redirect('/admin/inventario/presentacionproveedorproducto/')


@login_required
def redirigir_alertas_stock(request):
    """Redirección a alertas de stock de inventario"""
    return redirect('/inventario/alertas-stock/')


@login_required
def compras_home(request):
    """Vista principal del módulo de compras"""
    context = {
        'titulo': 'Módulo de Compras',
        'descripcion': 'Gestión integral de compras, proveedores y recepciones',
        'modulos': [
            {
                'nombre': 'Proveedores',
                'descripcion': 'Gestión de proveedores y contactos',
                'url': 'compras:proveedor_list',
                'icono': 'fas fa-building',
                'color': 'primary'
            },
            {
                'nombre': 'Órdenes de Compra',
                'descripcion': 'Crear y gestionar órdenes de compra',
                'url': 'compras:orden_list',
                'icono': 'fas fa-file-invoice',
                'color': 'success'
            },
            {
                'nombre': 'Recepciones',
                'descripcion': 'Recibir y validar mercancía',
                'url': 'compras:recepcion_list',
                'icono': 'fas fa-truck-loading',
                'color': 'info'
            },
            {
                'nombre': 'Solicitudes',
                'descripción': 'Gestión de solicitudes de compra',
                'url': 'compras:solicitud_list',
                'icono': 'fas fa-clipboard-list',
                'color': 'warning'
            },
            {
                'nombre': 'Reportes',
                'descripcion': 'Análisis y reportes de compras',
                'url': 'compras:reportes',
                'icono': 'fas fa-chart-bar',
                'color': 'info'
            }
        ]
    }
    return render(request, 'compras/home.html', context)