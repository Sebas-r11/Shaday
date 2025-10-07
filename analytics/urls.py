"""
URLs del sistema de Analytics e IA
"""

from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard_analytics, name='dashboard'),
    
    # Predicción de demanda
    path('prediccion-demanda/', views.prediccion_demanda, name='prediccion_demanda'),
    path('api/prediccion/<int:producto_id>/', views.api_prediccion_producto, name='api_prediccion_producto'),
    
    # Análisis de clientes
    path('analisis-clientes/', views.analisis_clientes, name='analisis_clientes'),
    
    # Sistema MRP
    path('sistema-mrp/', views.sistema_mrp, name='sistema_mrp'),
    
    # Reportes
    path('reportes/', views.reportes_analytics, name='reportes'),
    path('reportes/<int:reporte_id>/', views.detalle_reporte, name='detalle_reporte'),
    
    # Estadísticas masivas
    path('estadisticas-masivas/', views.estadisticas_masivas, name='estadisticas_masivas'),
]