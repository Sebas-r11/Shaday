from django.urls import path
from . import views
from .general_views import (
    dashboard_view, buscar_productos_api, obtener_precio_producto,
    verificar_stock_disponible, test_autocompletado, test_ajax_simple, test_syntax
)
from .clientes_views import (
    ClienteListView, ClienteCreateView, ClienteDetailView, ClienteUpdateView,
    buscar_clientes_api
)
from .cotizaciones_views import (
    CotizacionListView, CotizacionCreateView, CotizacionDetailView, CotizacionUpdateView,
    aprobar_cotizacion, rechazar_cotizacion, convertir_cotizacion_pedido,
    imprimir_cotizacion
)
from .pedidos_views import (
    PedidoListView, PedidoCreateView, PedidoDetailView, PedidoUpdateView,
    cancelar_pedido, convertir_pedido_factura,
    PedidosAlistamientoView, completar_alistamiento, obtener_pedidos_pendientes
    # cambiar_estado_pedido - Función comentada
)
from .facturas_views import (
    FacturaListView, FacturaCreateView, FacturaDetailView, FacturaUpdateView,
    marcar_factura_pagada, cancelar_factura, imprimir_factura,
    reporte_ventas_periodo, estadisticas_ventas_api
)
from .entregas_views import (
    EntregaListView, EntregaDetailView,
    EntregasRepartidorView, iniciar_entrega,
    completar_entrega, reportar_problema_entrega, completar_entrega_api,
    obtener_entregas_repartidor, actualizar_ubicacion_repartidor,
    reporte_entregas_periodo, estadisticas_entregas_api
    # EntregaCreateView, asignar_repartidor - Funciones comentadas
)

app_name = 'ventas'

urlpatterns = [
    # Dashboard
    path('', dashboard_view, name='dashboard'),
    
    # Clientes
    path('clientes/', ClienteListView.as_view(), name='cliente_list'),
    path('clientes/nuevo/', ClienteCreateView.as_view(), name='cliente_create'),
    path('clientes/<int:pk>/', ClienteDetailView.as_view(), name='cliente_detail'),
    path('clientes/<int:pk>/editar/', ClienteUpdateView.as_view(), name='cliente_update'),
    
    # Cotizaciones
    path('cotizaciones/', CotizacionListView.as_view(), name='cotizacion_list'),
    path('cotizaciones/nueva/', CotizacionCreateView.as_view(), name='cotizacion_create'),
    path('cotizaciones/<int:pk>/', CotizacionDetailView.as_view(), name='cotizacion_detail'),
    path('cotizaciones/<int:pk>/editar/', CotizacionUpdateView.as_view(), name='cotizacion_update'),
    path('cotizaciones/<int:pk>/imprimir/', imprimir_cotizacion, name='imprimir_cotizacion'),
    path('cotizaciones/<int:pk>/aprobar/', aprobar_cotizacion, name='aprobar_cotizacion'),
    path('cotizaciones/<int:pk>/rechazar/', rechazar_cotizacion, name='rechazar_cotizacion'),
    path('cotizaciones/<int:pk>/convertir-pedido/', convertir_cotizacion_pedido, name='convertir_a_pedido'),
    
    # Pedidos
    path('pedidos/', PedidoListView.as_view(), name='pedido_list'),
    path('pedidos/nuevo/', PedidoCreateView.as_view(), name='pedido_create'),
    path('pedidos/<int:pk>/', PedidoDetailView.as_view(), name='pedido_detail'),
    path('pedidos/<int:pk>/editar/', PedidoUpdateView.as_view(), name='pedido_update'),
    # path('pedidos/<int:pk>/cambiar-estado/', cambiar_estado_pedido, name='cambiar_estado_pedido'),  # Función comentada
    path('pedidos/<int:pk>/cancelar/', cancelar_pedido, name='cancelar_pedido'),
    path('pedidos/alistamiento/', PedidosAlistamientoView.as_view(), name='pedidos_alistamiento'),
    path('pedidos/<int:pk>/completar-alistamiento/', completar_alistamiento, name='completar_alistamiento'),
    
    # Facturas
    path('facturas/', FacturaListView.as_view(), name='factura_list'),
    path('facturas/nueva/', FacturaCreateView.as_view(), name='factura_create'),
    path('facturas/<int:pk>/', FacturaDetailView.as_view(), name='factura_detail'),
    path('facturas/<int:pk>/editar/', FacturaUpdateView.as_view(), name='factura_update'),
    path('facturas/<int:pk>/imprimir/', imprimir_factura, name='imprimir_factura'),
    path('facturas/<int:pk>/marcar-pagada/', marcar_factura_pagada, name='marcar_factura_pagada'),
    path('facturas/<int:pk>/cancelar/', cancelar_factura, name='cancelar_factura'),
    path('facturas/reportes/', reporte_ventas_periodo, name='reporte_facturas'),
    
    # Conversión de pedidos a facturas
    path('pedidos/<int:pk>/convertir-factura/', convertir_pedido_factura, name='convertir_a_factura'),
    
    # Entregas
    path('entregas/', EntregaListView.as_view(), name='entrega_list'),
    # path('entregas/nueva/', EntregaCreateView.as_view(), name='entrega_create'),  # Vista comentada
    path('entregas/<int:pk>/', EntregaDetailView.as_view(), name='entrega_detail'),
    path('entregas/repartidor/', EntregasRepartidorView.as_view(), name='entregas_repartidor'),
    # path('entregas/<int:pk>/asignar/', asignar_repartidor, name='asignar_repartidor'),  # Función comentada
    path('entregas/<int:pk>/iniciar/', iniciar_entrega, name='iniciar_entrega'),
    path('entregas/<int:pk>/completar/', completar_entrega, name='completar_entrega'),
    path('entregas/<int:pk>/problema/', reportar_problema_entrega, name='reportar_problema_entrega'),
    path('entregas/reportes/', reporte_entregas_periodo, name='reporte_entregas'),
    
    # APIs
    path('api/productos/', buscar_productos_api, name='api_productos'),
    path('api/productos/<int:producto_id>/precio/', obtener_precio_producto, name='api_precio_producto'),
    path('api/verificar-stock/', verificar_stock_disponible, name='api_verificar_stock'),
    path('api/clientes/', buscar_clientes_api, name='api_clientes'),
    path('api/pedidos/pendientes/', obtener_pedidos_pendientes, name='api_pedidos_pendientes'),
    path('api/estadisticas/ventas/', estadisticas_ventas_api, name='api_estadisticas_ventas'),
    path('api/estadisticas/entregas/', estadisticas_entregas_api, name='api_estadisticas_entregas'),
    
    # APIs Repartidor
    path('api/entregas/<int:pk>/completar/', completar_entrega_api, name='api_completar_entrega'),
    path('api/entregas/repartidor/', obtener_entregas_repartidor, name='api_entregas_repartidor'),
    path('api/repartidor/ubicacion/', actualizar_ubicacion_repartidor, name='api_ubicacion_repartidor'),
    
    # Vistas de prueba/desarrollo
    path('test-autocompletado/', test_autocompletado, name='test_autocompletado'),
    path('test-ajax/', test_ajax_simple, name='test_ajax_simple'),
    path('test-syntax/', test_syntax, name='test_syntax'),
]