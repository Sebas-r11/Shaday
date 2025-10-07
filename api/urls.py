from django.urls import path, include
from . import views

app_name = 'api'

urlpatterns = [
    # APIs Geográficas
    path('ciudades/', views.api_ciudades, name='ciudades'),
    path('departamentos/', views.api_departamentos, name='departamentos'),
    path('ciudades/<int:departamento_id>/', views.api_ciudades_por_departamento, name='ciudades_por_departamento'),
    
    # APIs de Productos
    path('productos/', views.api_productos, name='productos'),
    path('productos/<int:producto_id>/', views.api_producto_detalle, name='producto_detalle'),
    path('productos/buscar/', views.api_buscar_productos, name='buscar_productos'),
    path('categorias/', views.api_categorias, name='categorias'),
    
    # APIs de CRM/Clientes
    path('clientes/', views.api_clientes, name='clientes'),
    path('clientes/<int:cliente_id>/', views.api_cliente_detalle, name='cliente_detalle'),
    path('clientes/buscar/', views.api_buscar_clientes, name='buscar_clientes'),
    
    # APIs de Estadísticas Públicas
    path('estadisticas/productos-populares/', views.api_productos_populares, name='productos_populares'),
    path('estadisticas/categorias-activas/', views.api_categorias_activas, name='categorias_activas'),
    path('estadisticas/dashboard/', views.api_estadisticas_dashboard, name='estadisticas_dashboard'),
    path('estadisticas/ventas-mes/', views.api_ventas_por_mes, name='ventas_mes'),
    path('estadisticas/productos-vendidos/', views.api_productos_mas_vendidos, name='productos_vendidos'),
    path('estadisticas/estados-pedidos/', views.api_estados_pedidos, name='estados_pedidos'),
    path('estadisticas/ventas-vendedor/', views.api_ventas_por_vendedor, name='ventas_vendedor'),
    
    # API de Información del Sistema
    path('info/', views.api_info_sistema, name='info_sistema'),
    path('version/', views.api_version, name='version'),
]