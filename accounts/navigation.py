"""
Configuración de navegación por roles - REORGANIZADA MODULARMENTE
Define qué elementos del navbar puede ver cada tipo de usuario
"""

# Configuración de navegación por rol - NUEVA ESTRUCTURA MODULAR
NAVIGATION_CONFIG = {
    'admin': {
        'name': 'Administrador',
        'modules': [
            {
                'name': 'Dashboard',
                'url': 'accounts:dashboard',
                'icon': 'fas fa-tachometer-alt',
                'active_namespace': 'accounts'
            },
            {
                'name': 'Inventario',
                'icon': 'fas fa-boxes',
                'main_url': 'inventario:producto_list',
                'active_namespace': 'inventario',
                'subitems': [
                    {
                        'name': 'Productos',
                        'url': 'inventario:producto_list',
                        'icon': 'fas fa-box',
                        'description': 'Gestionar catálogo de productos'
                    },
                    {
                        'name': 'Stock',
                        'url': 'inventario:stock_list',
                        'icon': 'fas fa-warehouse',
                        'description': 'Control de inventario y existencias'
                    },
                    {
                        'name': 'Ajustes de Inventario',
                        'url': 'inventario:ajuste_inventario',
                        'icon': 'fas fa-plus-minus',
                        'description': 'Ajustar niveles de stock'
                    },
                    {
                        'name': 'Movimientos',
                        'url': 'inventario:movimiento_list',
                        'icon': 'fas fa-exchange-alt',
                        'description': 'Historial de movimientos'
                    },
                    {
                        'name': 'Categorías',
                        'url': 'inventario:categoria_list',
                        'icon': 'fas fa-tags',
                        'description': 'Organizar productos por categorías'
                    }
                ]
            },
            {
                'name': 'Compras',
                'icon': 'fas fa-truck',
                'main_url': 'compras:gestion_dashboard',
                'active_namespace': 'compras',
                'subitems': [
                    {
                        'name': 'Dashboard Compras',
                        'url': 'compras:gestion_dashboard',
                        'icon': 'fas fa-tachometer-alt',
                        'description': 'Panel central de gestión de compras'
                    },
                    {
                        'name': 'Gestión Proveedores',
                        'url': 'compras:admin_proveedores',
                        'icon': 'fas fa-building',
                        'description': 'Administrar proveedores y productos'
                    },
                    {
                        'name': 'Presentaciones',
                        'url': 'compras:admin_presentaciones',
                        'icon': 'fas fa-boxes',
                        'description': 'Configurar presentaciones por proveedor'
                    },
                    {
                        'name': 'Presentaciones Simple',
                        'url': 'inventario:presentaciones_simple',
                        'icon': 'fas fa-cube',
                        'description': 'Vista simplificada de presentaciones'
                    },
                    {
                        'name': 'Alertas de Stock',
                        'url': 'compras:alertas_stock',
                        'icon': 'fas fa-exclamation-triangle',
                        'description': 'Monitorear niveles de inventario'
                    },
                    {
                        'name': 'Órdenes de Compra',
                        'url': 'compras:orden_list',
                        'icon': 'fas fa-file-invoice',
                        'description': 'Gestionar órdenes de compra'
                    },
                    {
                        'name': 'Solicitudes',
                        'url': 'compras:solicitud_list',
                        'icon': 'fas fa-clipboard-list',
                        'description': 'Administrar solicitudes de compra'
                    }
                ]
            },
            {
                'name': 'Ventas',
                'icon': 'fas fa-shopping-cart',
                'main_url': 'ventas:dashboard',
                'subitems': [
                    {
                        'name': 'Dashboard Ventas',
                        'url': 'ventas:dashboard',
                        'icon': 'fas fa-tachometer-alt'
                    },
                    {
                        'name': 'Clientes',
                        'url': 'ventas:cliente_list',
                        'icon': 'fas fa-users'
                    },
                    {
                        'name': 'Cotizaciones',
                        'url': 'ventas:cotizacion_list',
                        'icon': 'fas fa-file-alt'
                    },
                    {
                        'name': 'Pedidos',
                        'url': 'ventas:pedido_list',
                        'icon': 'fas fa-shopping-cart'
                    }
                ]
            },
            {
                'name': 'CRM',
                'icon': 'fas fa-handshake',
                'main_url': 'crm:dashboard',
                'subitems': [
                    {
                        'name': 'Dashboard CRM',
                        'url': 'crm:dashboard',
                        'icon': 'fas fa-tachometer-alt'
                    },
                    {
                        'name': 'Oportunidades',
                        'url': 'crm:oportunidad_list',
                        'icon': 'fas fa-bullseye'
                    },
                    {
                        'name': 'Nueva Oportunidad',
                        'url': 'crm:oportunidad_create',
                        'icon': 'fas fa-plus'
                    },
                    {
                        'name': 'Nueva Actividad',
                        'url': 'crm:actividad_create',
                        'icon': 'fas fa-calendar-plus'
                    }
                ]
            },
            {
                'name': 'Analytics e IA',
                'icon': 'fas fa-brain',
                'main_url': 'analytics:dashboard',
                'active_namespace': 'analytics',
                'subitems': [
                    {
                        'name': 'Dashboard IA',
                        'url': 'analytics:dashboard',
                        'icon': 'fas fa-tachometer-alt'
                    },
                    {
                        'name': 'Predicción Demanda',
                        'url': 'analytics:prediccion_demanda',
                        'icon': 'fas fa-chart-line'
                    },
                    {
                        'name': 'Análisis Clientes',
                        'url': 'analytics:analisis_clientes',
                        'icon': 'fas fa-users-cog'
                    },
                    {
                        'name': 'Sistema MRP',
                        'url': 'analytics:sistema_mrp',
                        'icon': 'fas fa-cogs'
                    },
                    {
                        'name': 'Estadísticas Masivas',
                        'url': 'analytics:estadisticas_masivas',
                        'icon': 'fas fa-chart-bar'
                    },
                    {
                        'name': 'Reportes',
                        'url': 'analytics:reportes',
                        'icon': 'fas fa-file-alt'
                    }
                ]
            },
            {
                'name': 'Usuarios',
                'url': 'accounts:user_list',
                'icon': 'fas fa-users-cog',
                'active_namespace': 'accounts'
            }
        ]
    },
    'vendedor': {
        'name': 'Vendedor',
        'modules': [
            {
                'name': 'Dashboard',
                'url': 'accounts:dashboard',
                'icon': 'fas fa-tachometer-alt',
                'active_namespace': 'accounts'
            },
            {
                'name': 'Inventario',
                'icon': 'fas fa-boxes',
                'main_url': 'inventario:producto_list',
                'active_namespace': 'inventario',
                'description': 'Consultar productos y disponibilidad',
                'subitems': [
                    {
                        'name': 'Productos',
                        'url': 'inventario:producto_list',
                        'icon': 'fas fa-box',
                        'description': 'Consultar catálogo de productos'
                    },
                    {
                        'name': 'Stock Disponible',
                        'url': 'inventario:stock_list',
                        'icon': 'fas fa-warehouse',
                        'description': 'Verificar disponibilidad'
                    }
                ]
            },
            {
                'name': 'Ventas',
                'icon': 'fas fa-shopping-cart',
                'main_url': 'ventas:dashboard',
                'subitems': [
                    {
                        'name': 'Dashboard Ventas',
                        'url': 'ventas:dashboard',
                        'icon': 'fas fa-tachometer-alt'
                    },
                    {
                        'name': 'Clientes',
                        'url': 'ventas:cliente_list',
                        'icon': 'fas fa-users'
                    },
                    {
                        'name': 'Cotizaciones',
                        'url': 'ventas:cotizacion_list',
                        'icon': 'fas fa-file-alt'
                    },
                    {
                        'name': 'Pedidos',
                        'url': 'ventas:pedido_list',
                        'icon': 'fas fa-shopping-cart'
                    }
                ]
            },
            {
                'name': 'CRM',
                'icon': 'fas fa-handshake',
                'main_url': 'crm:dashboard',
                'subitems': [
                    {
                        'name': 'Dashboard CRM',
                        'url': 'crm:dashboard',
                        'icon': 'fas fa-tachometer-alt'
                    },
                    {
                        'name': 'Oportunidades',
                        'url': 'crm:oportunidad_list',
                        'icon': 'fas fa-bullseye'
                    },
                    {
                        'name': 'Nueva Oportunidad',
                        'url': 'crm:oportunidad_create',
                        'icon': 'fas fa-plus'
                    },
                    {
                        'name': 'Nueva Actividad',
                        'url': 'crm:actividad_create',
                        'icon': 'fas fa-calendar-plus'
                    }
                ]
            }
        ]
    },
    'bodega': {
        'name': 'Bodeguero',
        'modules': [
            {
                'name': 'Dashboard',
                'url': 'accounts:dashboard',
                'icon': 'fas fa-tachometer-alt',
                'active_namespace': 'accounts'
            },
            {
                'name': 'Inventario',
                'icon': 'fas fa-boxes',
                'main_url': 'inventario:producto_list',
                'active_namespace': 'inventario',
                'description': 'Gestionar stock y productos',
                'subitems': [
                    {
                        'name': 'Productos',
                        'url': 'inventario:producto_list',
                        'icon': 'fas fa-box',
                        'description': 'Consultar catálogo de productos'
                    },
                    {
                        'name': 'Stock',
                        'url': 'inventario:stock_list',
                        'icon': 'fas fa-warehouse',
                        'description': 'Verificar existencias en bodega'
                    },
                    {
                        'name': 'Ajustes de Stock',
                        'url': 'inventario:ajuste_inventario',
                        'icon': 'fas fa-plus-minus',
                        'description': 'Realizar ajustes de inventario'
                    },
                    {
                        'name': 'Movimientos',
                        'url': 'inventario:movimiento_list',
                        'icon': 'fas fa-exchange-alt',
                        'description': 'Ver historial de movimientos'
                    }
                ]
            },
            {
                'name': 'Alertas de Stock',
                'url': 'compras:alertas_stock',
                'icon': 'fas fa-exclamation-triangle',
                'active_namespace': 'compras',
                'description': 'Monitorear niveles críticos de inventario'
            },
            {
                'name': 'Alistamiento',
                'url': 'ventas:pedidos_alistamiento',
                'icon': 'fas fa-clipboard-list',
                'active_namespace': 'alistamiento',
                'description': 'Preparar pedidos para entrega'
            }
        ]
    },
    'repartidor': {
        'name': 'Repartidor',
        'modules': [
            {
                'name': 'Dashboard',
                'url': 'accounts:dashboard',
                'icon': 'fas fa-tachometer-alt',
                'active_namespace': 'accounts'
            },
            {
                'name': 'Entregas',
                'icon': 'fas fa-truck',
                'main_url': 'ventas:entregas_repartidor',
                'subitems': [
                    {
                        'name': 'Mis Entregas',
                        'url': 'ventas:entregas_repartidor',
                        'icon': 'fas fa-list'
                    },
                    {
                        'name': 'Optimizar Ruta',
                        'url': 'ventas:optimizar_ruta',
                        'icon': 'fas fa-route'
                    },
                    {
                        'name': 'Pedidos Disponibles',
                        'url': 'ventas:pedido_list',
                        'icon': 'fas fa-boxes'
                    }
                ]
            }
        ]
    }
}

def get_user_navigation(user):
    """
    Retorna la configuración de navegación para un usuario específico
    """
    if not user.is_authenticated:
        return []
    
    # Si es superuser, mostrar todo (admin) - tiene prioridad sobre role
    if user.is_superuser:
        return NAVIGATION_CONFIG.get('admin', {}).get('modules', [])
    
    # Obtener configuración según el rol
    user_role = getattr(user, 'role', 'vendedor')  # Default a vendedor si no tiene role
    
    return NAVIGATION_CONFIG.get(user_role, {}).get('modules', [])

def get_user_role_name(user):
    """
    Retorna el nombre descriptivo del rol del usuario
    """
    if not user.is_authenticated:
        return 'Invitado'
    
    # Superuser tiene prioridad sobre role
    if user.is_superuser:
        return 'Administrador'
    
    user_role = getattr(user, 'role', 'vendedor')
    return NAVIGATION_CONFIG.get(user_role, {}).get('name', 'Usuario')