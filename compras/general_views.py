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
    
    # HTML directo sin template complejo para mejor rendimiento
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard de Compras - Sistema Reyes</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .dashboard-header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 2rem 0;
                margin-bottom: 2rem;
            }}
            .module-card {{
                border: none;
                border-radius: 15px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: transform 0.3s ease;
                height: 100%;
            }}
            .module-card:hover {{
                transform: translateY(-5px);
            }}
            .module-icon {{
                font-size: 3rem;
                margin-bottom: 1rem;
            }}
        </style>
    </head>
    <body>
        <div class="dashboard-header">
            <div class="container">
                <div class="row">
                    <div class="col-12 text-center">
                        <h1><i class="fas fa-truck"></i> Dashboard de Compras</h1>
                        <p class="lead">Sistema centralizado para gestión de proveedores y compras</p>
                        <nav aria-label="breadcrumb">
                            <ol class="breadcrumb justify-content-center" style="background: rgba(255,255,255,0.1);">
                                <li class="breadcrumb-item"><a href="/accounts/dashboard/" style="color: white;">Inicio</a></li>
                                <li class="breadcrumb-item active" aria-current="page" style="color: rgba(255,255,255,0.8);">Gestión de Compras</li>
                            </ol>
                        </nav>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="container">
            <div class="row g-4">
                <!-- Gestión de Proveedores -->
                <div class="col-md-6 col-lg-3">
                    <div class="card module-card">
                        <div class="card-body text-center">
                            <div class="module-icon text-primary">
                                <i class="fas fa-building"></i>
                            </div>
                            <h5 class="card-title">Gestión de Proveedores</h5>
                            <p class="card-text">Administrar proveedores y sus productos</p>
                            <a href="/compras/gestion/proveedores/" class="btn btn-primary">
                                <i class="fas fa-arrow-right"></i> Acceder
                            </a>
                        </div>
                    </div>
                </div>
                
                <!-- Presentaciones -->
                <div class="col-md-6 col-lg-3">
                    <div class="card module-card">
                        <div class="card-body text-center">
                            <div class="module-icon text-success">
                                <i class="fas fa-boxes"></i>
                            </div>
                            <h5 class="card-title">Presentaciones</h5>
                            <p class="card-text">Configurar presentaciones por proveedor</p>
                            <a href="/compras/gestion/presentaciones/" class="btn btn-success">
                                <i class="fas fa-arrow-right"></i> Acceder
                            </a>
                        </div>
                    </div>
                </div>
                
                <!-- Alertas de Stock -->
                <div class="col-md-6 col-lg-3">
                    <div class="card module-card">
                        <div class="card-body text-center">
                            <div class="module-icon text-warning">
                                <i class="fas fa-exclamation-triangle"></i>
                            </div>
                            <h5 class="card-title">Alertas de Stock</h5>
                            <p class="card-text">Monitorear niveles de inventario</p>
                            <a href="/compras/gestion/alertas-stock/" class="btn btn-warning">
                                <i class="fas fa-arrow-right"></i> Acceder
                            </a>
                        </div>
                    </div>
                </div>
                
                <!-- Órdenes de Compra -->
                <div class="col-md-6 col-lg-3">
                    <div class="card module-card">
                        <div class="card-body text-center">
                            <div class="module-icon text-info">
                                <i class="fas fa-file-invoice"></i>
                            </div>
                            <h5 class="card-title">Órdenes de Compra</h5>
                            <p class="card-text">Gestionar órdenes de compra</p>
                            <a href="/compras/ordenes/" class="btn btn-info">
                                <i class="fas fa-arrow-right"></i> Acceder
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Información del Sistema -->
            <div class="row mt-5">
                <div class="col-12">
                    <div class="card">
                        <div class="card-body text-center">
                            <h5 class="card-title">
                                <i class="fas fa-info-circle text-primary"></i> 
                                Información del Sistema
                            </h5>
                            <p class="card-text">
                                Este dashboard centraliza todas las funcionalidades relacionadas con compras y proveedores. 
                                Accede rápidamente a la gestión de proveedores, configuración de presentaciones, 
                                monitoreo de alertas de stock y administración de órdenes de compra.
                            </p>
                            <small class="text-muted">
                                <i class="fas fa-lightbulb"></i> 
                                Tip: Utiliza las presentaciones dinámicas para configurar diferentes formatos de venta por proveedor.
                            </small>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Links de navegación rápida -->
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-body">
                            <h6 class="card-title">Navegación Rápida</h6>
                            <div class="d-flex flex-wrap gap-2">
                                <a href="/admin/inventario/proveedor/" class="btn btn-outline-primary btn-sm">
                                    <i class="fas fa-cog"></i> Admin Proveedores
                                </a>
                                <a href="/admin/inventario/productoproveedor/" class="btn btn-outline-primary btn-sm">
                                    <i class="fas fa-link"></i> Admin Productos-Proveedores
                                </a>
                                <a href="/admin/inventario/presentacionproveedorproducto/" class="btn btn-outline-primary btn-sm">
                                    <i class="fas fa-boxes"></i> Admin Presentaciones
                                </a>
                                <a href="/inventario/alertas-stock/" class="btn btn-outline-warning btn-sm">
                                    <i class="fas fa-exclamation-triangle"></i> Alertas Stock
                                </a>
                                <a href="/compras/ordenes/" class="btn btn-outline-info btn-sm">
                                    <i class="fas fa-shopping-cart"></i> Lista Órdenes
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
                'descripcion': 'Reportes y estadísticas de compras',
                'url': 'compras:reporte_compras',
                'icono': 'fas fa-chart-bar',
                'color': 'secondary'
            }
        ]
    }
    
    return render(request, 'compras/home.html', context)


# ========================================
# FUNCIONES DE UTILIDAD Y VALIDACIÓN
# ========================================

def validar_permisos_compras(user):
    """Función auxiliar para validar permisos del módulo de compras"""
    if not user.is_authenticated:
        return False
    
    return (
        user.is_superuser or
        user.groups.filter(name__in=['Compras', 'Administradores']).exists() or
        user.role in ['administrador', 'compras']
    )


def obtener_estadisticas_compras():
    """Función auxiliar para obtener estadísticas rápidas del módulo"""
    from .models import Proveedor, OrdenCompra, RecepcionCompra
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import timedelta
    
    # Obtener datos del último mes
    fecha_limite = timezone.now() - timedelta(days=30)
    
    estadisticas = {
        'proveedores_activos': Proveedor.objects.filter(activo=True).count(),
        'ordenes_mes': OrdenCompra.objects.filter(
            fecha_orden__gte=fecha_limite
        ).count(),
        'valor_ordenes_mes': OrdenCompra.objects.filter(
            fecha_orden__gte=fecha_limite
        ).aggregate(total=Sum('total'))['total'] or 0,
        'recepciones_mes': RecepcionCompra.objects.filter(
            fecha_recepcion__gte=fecha_limite
        ).count(),
        'ordenes_pendientes': OrdenCompra.objects.filter(
            estado__in=['enviada', 'confirmada', 'recibida_parcial']
        ).count()
    }
    
    return estadisticas


@login_required 
def compras_ayuda(request):
    """Vista de ayuda para el módulo de compras"""
    context = {
        'titulo': 'Ayuda - Módulo de Compras',
        'secciones': [
            {
                'titulo': 'Gestión de Proveedores',
                'contenido': 'Aprende a crear y administrar la información de tus proveedores.',
                'enlaces': [
                    {'nombre': 'Crear Proveedor', 'url': 'compras:proveedor_create'},
                    {'nombre': 'Lista de Proveedores', 'url': 'compras:proveedor_list'},
                ]
            },
            {
                'titulo': 'Órdenes de Compra',
                'contenido': 'Gestiona el ciclo completo de órdenes de compra desde creación hasta recepción.',
                'enlaces': [
                    {'nombre': 'Nueva Orden', 'url': 'compras:orden_create'},
                    {'nombre': 'Lista de Órdenes', 'url': 'compras:orden_list'},
                ]
            },
            {
                'titulo': 'Recepciones',
                'contenido': 'Registra la recepción de mercancía y actualiza inventarios.',
                'enlaces': [
                    {'nombre': 'Nueva Recepción', 'url': 'compras:recepcion_create'},
                    {'nombre': 'Lista de Recepciones', 'url': 'compras:recepcion_list'},
                ]
            },
            {
                'titulo': 'Reportes',
                'contenido': 'Genera reportes detallados de compras y analiza tendencias.',
                'enlaces': [
                    {'nombre': 'Reporte de Compras', 'url': 'compras:reporte_compras'},
                ]
            }
        ]
    }
    
    return render(request, 'compras/ayuda.html', context)