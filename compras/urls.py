from django.urls import path

# Importaciones especializadas después de la refactorización
from .proveedores_views import (
    ProveedorListView, ProveedorCreateView, ProveedorDetailView, ProveedorUpdateView,
    redirigir_admin_proveedores
)
from .ordenes_views import (
    compras_dashboard, OrdenCompraListView, OrdenCompraCreateView, OrdenCompraDetailView,
    OrdenCompraUpdateView, OrdenCompraCancelView, OrdenCompraPrintView,
    RecepcionCompraCreateView, RecepcionCompraDetailView,
    SolicitudCompraListView, SolicitudCompraCreateView, SolicitudCompraDetailView, 
    SolicitudCompraUpdateView, aprobar_solicitud, rechazar_solicitud, 
    enviar_solicitud, crear_orden_desde_solicitud, agregar_item_solicitud,
    eliminar_item_solicitud, agregar_item_orden, cambiar_estado_orden, reporte_compras
)
from .general_views import (
    gestion_compras_dashboard, compras_home, compras_ayuda,
    redirigir_admin_presentaciones, redirigir_alertas_stock
)

# Importaciones para vistas que aún no fueron refactorizadas
from . import views_simple

app_name = 'compras'

urlpatterns = [
    # Dashboard principal
    path('', compras_dashboard, name='dashboard'),
    path('home/', compras_home, name='home'),
    
    # Gestión Rápida - Vistas simples sin templates complejos
    path('gestion/', gestion_compras_dashboard, name='gestion_dashboard'),
    path('gestion/proveedores/', views_simple.gestion_proveedores_simple, name='admin_proveedores'),
    path('gestion/presentaciones/', views_simple.gestion_presentaciones_simple, name='admin_presentaciones'),
    path('gestion/alertas-stock/', views_simple.gestion_alertas_stock_simple, name='alertas_stock'),
    
    # Solicitudes de Compra
    path('solicitudes/', SolicitudCompraListView.as_view(), name='solicitud_list'),
    path('solicitudes/crear/', SolicitudCompraCreateView.as_view(), name='solicitud_create'),
    path('solicitudes/<uuid:pk>/', SolicitudCompraDetailView.as_view(), name='solicitud_detail'),
    path('solicitudes/<uuid:pk>/editar/', SolicitudCompraUpdateView.as_view(), name='solicitud_update'),
    path('solicitudes/<uuid:pk>/enviar/', enviar_solicitud, name='enviar_solicitud'),
    path('solicitudes/<uuid:pk>/aprobar/', aprobar_solicitud, name='aprobar_solicitud'),
    path('solicitudes/<uuid:pk>/rechazar/', rechazar_solicitud, name='rechazar_solicitud'),
    path('solicitudes/<uuid:pk>/crear-orden/', crear_orden_desde_solicitud, name='crear_orden_desde_solicitud'),
    path('solicitudes/<uuid:pk>/agregar-item/', agregar_item_solicitud, name='agregar_item_solicitud'),
    path('solicitudes/<uuid:pk>/items/<uuid:item_pk>/eliminar/', eliminar_item_solicitud, name='eliminar_item_solicitud'),

    # Proveedores
    path('proveedores/', ProveedorListView.as_view(), name='proveedor_list'),
    path('proveedores/crear/', ProveedorCreateView.as_view(), name='proveedor_create'),
    path('proveedores/<uuid:pk>/', ProveedorDetailView.as_view(), name='proveedor_detail'),
    path('proveedores/<uuid:pk>/editar/', ProveedorUpdateView.as_view(), name='proveedor_update'),
    
    # Órdenes de Compra
    path('ordenes/', OrdenCompraListView.as_view(), name='orden_list'),
    path('ordenes/crear/', OrdenCompraCreateView.as_view(), name='orden_create'),
    path('ordenes/<uuid:pk>/', OrdenCompraDetailView.as_view(), name='orden_detail'),
    path('ordenes/<uuid:pk>/editar/', OrdenCompraUpdateView.as_view(), name='orden_update'),
    path('ordenes/<uuid:pk>/cancelar/', OrdenCompraCancelView.as_view(), name='orden_cancel'),
    path('ordenes/<uuid:pk>/imprimir/', OrdenCompraPrintView.as_view(), name='orden_print'),
    
    # Recepciones
    path('recepciones/crear/', RecepcionCompraCreateView.as_view(), name='recepcion_create'),
    path('recepciones/<uuid:pk>/', RecepcionCompraDetailView.as_view(), name='recepcion_detail'),
    
    # AJAX endpoints
    path('ordenes/<uuid:pk>/agregar-item/', agregar_item_orden, name='agregar_item_orden'),
    path('ordenes/<uuid:pk>/cambiar-estado/', cambiar_estado_orden, name='cambiar_estado_orden'),
    
    # Reportes
    path('reportes/', reporte_compras, name='reporte_compras'),
    
    # Utilidades y redirecciones
    path('admin/proveedores/', redirigir_admin_proveedores, name='redirigir_admin_proveedores'),
    path('admin/presentaciones/', redirigir_admin_presentaciones, name='redirigir_admin_presentaciones'),
    path('alertas-stock/', redirigir_alertas_stock, name='redirigir_alertas_stock'),
    
    # Ayuda
    path('ayuda/', compras_ayuda, name='ayuda'),
]