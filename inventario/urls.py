from django.urls import path

# Importaciones especializadas después de la refactorización
from .productos_views import (
    ProductoListView, ProductoCreateView, ProductoDetailView, ProductoUpdateView, ProductoDeleteView,
    exportar_productos_excel, duplicar_producto, buscar_productos_api,
    verificar_codigo_producto, obtener_precios_producto
)
from .categorias_views import (
    CategoriaListView, CategoriaCreateView, CategoriaUpdateView, CategoriaDeleteView,
    SubcategoriaListView, SubcategoriaCreateView, SubcategoriaUpdateView, SubcategoriaDeleteView
)
from .stock_views import (
    BodegaListView, BodegaCreateView, BodegaDetailView, BodegaUpdateView,
    StockListView, StockDetailView
    # BodegaDeleteView - No existe en stock_views
    # AlertasStockView - Existe en views.py principal
)
from .movimientos_views import (
    MovimientoInventarioListView, MovimientoInventarioDetailView,
    generar_pdf_transferencia, ajuste_inventario, generar_pdf_ajuste
    # transferencia_producto - No existe en movimientos_views
)
from .reportes_views import (
    DashboardRecomendacionesView, generar_recomendaciones_ajax
)
from .api_views import (
    subcategorias_api, stock_api, obtener_presentaciones_proveedor
)
from .general_views import (
    exportar_productos_excel, InventarioHomeView, InventarioMenuView
)

# Importaciones para vistas que no fueron refactorizadas aún
from . import views  # Para vistas que no se movieron aún
from .reporte_views import reporte_integracion_ventas_inventario
from . import views_devoluciones
from . import views_simple
from . import alertas_views

app_name = 'inventario'

urlpatterns = [
    # Página principal del inventario
    path('', InventarioHomeView.as_view(), name='home'),
    path('dashboard/', InventarioHomeView.as_view(), name='dashboard'),  # Alias para dashboard
    path('menu/', InventarioMenuView.as_view(), name='menu'),
    
    # Productos
    path('productos/', ProductoListView.as_view(), name='producto_list'),
    path('productos/crear/', ProductoCreateView.as_view(), name='producto_create'),
    path('productos/<int:pk>/', ProductoDetailView.as_view(), name='producto_detail'),
    path('productos/<int:pk>/editar/', ProductoUpdateView.as_view(), name='producto_update'),
    path('productos/<int:pk>/eliminar/', ProductoDeleteView.as_view(), name='producto_delete'),
    path('productos/exportar-excel/', exportar_productos_excel, name='exportar_productos_excel'),
    
    # Categorías
    path('categorias/', CategoriaListView.as_view(), name='categoria_list'),
    path('categorias/crear/', CategoriaCreateView.as_view(), name='categoria_create'),
    path('categorias/<int:pk>/editar/', CategoriaUpdateView.as_view(), name='categoria_update'),
    path('categorias/<int:pk>/eliminar/', CategoriaDeleteView.as_view(), name='categoria_delete'),
    
    # Subcategorías
    path('subcategorias/', SubcategoriaListView.as_view(), name='subcategoria_list'),
    path('subcategorias/crear/', SubcategoriaCreateView.as_view(), name='subcategoria_create'),
    path('subcategorias/<int:pk>/editar/', SubcategoriaUpdateView.as_view(), name='subcategoria_update'),
    path('subcategorias/<int:pk>/eliminar/', SubcategoriaDeleteView.as_view(), name='subcategoria_delete'),
    
    # Bodegas
    path('bodegas/', BodegaListView.as_view(), name='bodega_list'),
    path('bodegas/crear/', BodegaCreateView.as_view(), name='bodega_create'),
    path('bodegas/<int:pk>/', BodegaDetailView.as_view(), name='bodega_detail'),
    path('bodegas/<int:pk>/editar/', BodegaUpdateView.as_view(), name='bodega_update'),
    # path('bodegas/<int:pk>/eliminar/', BodegaDeleteView.as_view(), name='bodega_delete'),  # BodegaDeleteView no existe
    path('bodegas/<int:pk>/eliminar/', views.bodega_delete_simple, name='bodega_delete'),
    
    # Stock
    path('stock/', StockListView.as_view(), name='stock_list'),
    path('stock/<int:pk>/', StockDetailView.as_view(), name='stock_detail'),
    path('alertas-stock/', views.AlertasStockView.as_view(), name='alertas_stock'),
    
    # Movimientos
    path('movimientos/', MovimientoInventarioListView.as_view(), name='movimiento_list'),
    path('movimientos/<uuid:movimiento_id>/', MovimientoInventarioDetailView.as_view(), name='movimiento_detail'),
    
    # Ajustes de inventario
    path('ajustes/', views.AjusteInventarioView.as_view(), name='ajuste_inventario'),
    path('ajustes/crear/', views.crear_ajuste_inventario, name='crear_ajuste_inventario'),
    path('ajustes/<uuid:movimiento_id>/pdf/', generar_pdf_ajuste, name='ajuste_pdf'),
    
    # Transferencias
    path('transferencias/', views.transferencia_producto, name='transferencia_create'),
    path('transferencias/<uuid:movimiento_id>/pdf/', generar_pdf_transferencia, name='transferencia_pdf'),
    
    # Reportes y dashboards
    path('reportes/integracion-ventas/', reporte_integracion_ventas_inventario, name='reporte_integracion'),
    path('dashboard/recomendaciones/', DashboardRecomendacionesView.as_view(), name='dashboard_recomendaciones'),
    
    # Gestión de proveedores por producto (temporalmente comentado - requiere implementación)
    # path('productos/<int:pk>/proveedores/', ProductoProveedoresView.as_view(), name='producto_proveedores'),
    path('productos/<int:pk>/proveedores/', views.producto_proveedores_simple, name='producto_proveedores'),
    # path('productos/<int:pk>/detalle-proveedores/', ProductoDetailViewConProveedores.as_view(), name='producto_detail_proveedores'),
    
    # Órdenes de compra (vistas que aún no se han refactorizado)
    path('generar-orden-compra/', views.GenerarOrdenCompraView.as_view(), name='generar_orden_compra'),
    path('ordenes-compra-stock/', views.OrdenCompraStockListView.as_view(), name='orden_compra_stock_list'),
    path('ordenes-compra-stock/<int:pk>/', views.OrdenCompraStockDetailView.as_view(), name='orden_compra_stock_detail'),
    path('ordenes-compra-stock/<int:pk>/cambiar-estado/', views.CambiarEstadoOrdenCompraView.as_view(), name='cambiar_estado_orden_compra'),
    path('ordenes-compra-stock/<int:orden_id>/pdf/', views.generar_pdf_orden_compra, name='orden_compra_pdf'),
    
    # Devoluciones
    path('devoluciones/', views_devoluciones.lista_devoluciones, name='lista_devoluciones'),
    path('devoluciones/<int:devolucion_id>/', views_devoluciones.detalle_devolucion, name='detalle_devolucion'),
    path('devoluciones/<int:devolucion_id>/recibir/', views_devoluciones.recibir_devolucion, name='recibir_devolucion'),
    path('devoluciones/<int:devolucion_id>/rechazar/', views_devoluciones.rechazar_devolucion, name='rechazar_devolucion'),
    path('devoluciones/crear-desde-entrega/', views_devoluciones.crear_devolucion_desde_entrega, name='crear_devolucion_desde_entrega'),
    path('devoluciones/reportes/', views_devoluciones.reporte_devoluciones, name='reporte_devoluciones'),
    path('devoluciones/<int:devolucion_id>/imprimir/', views_devoluciones.imprimir_devolucion, name='imprimir_devolucion'),
    
    # Recomendaciones Inteligentes (vistas que aún no se han refactorizado)
    path('recomendaciones/', views.RecomendacionesListView.as_view(), name='recomendaciones_list'),
    path('recomendaciones/<int:pk>/', views.RecomendacionDetailView.as_view(), name='recomendacion_detail'),
    path('recomendaciones/<int:pk>/procesar/', views.procesar_recomendacion, name='procesar_recomendacion'),
    
    # API AJAX
    path('api/generar-recomendaciones/', generar_recomendaciones_ajax, name='generar_recomendaciones_ajax'),
    path('api/subcategorias/', subcategorias_api, name='subcategorias_api'),
    path('api/stock/', stock_api, name='stock_api'),
    path('api/presentaciones-proveedor/<int:proveedor_id>/<int:producto_id>/', obtener_presentaciones_proveedor, name='presentaciones_proveedor_api'),
    
    # Vistas simples (sin templates complejos)
    path('presentaciones-simple/', views_simple.presentaciones_proveedor_simple, name='presentaciones_simple'),
    
    # Alertas de Stock
    path('alertas/', alertas_views.dashboard_alertas, name='dashboard_alertas'),
    path('alertas/lista/', alertas_views.lista_alertas, name='lista_alertas'),
    path('alertas/<int:alerta_id>/resolver/', alertas_views.resolver_alerta, name='resolver_alerta'),
    path('alertas/<int:alerta_id>/marcar-vista/', alertas_views.marcar_vista_alerta, name='marcar_vista_alerta'),
    path('alertas/generar/', alertas_views.generar_alertas_manuales, name='generar_alertas'),
    path('api/alertas/', alertas_views.api_alertas_dashboard, name='api_alertas'),
]