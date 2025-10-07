from django.urls import path

# Importaciones especializadas después de la refactorización
from .oportunidades_views import (
    OportunidadListView, OportunidadCreateView, OportunidadDetailView, 
    OportunidadUpdateView, agregar_nota_oportunidad
)
from .dashboard_views import crm_dashboard, reporte_pipeline
from .general_views import (
    ActividadCreateView, ActividadUpdateView, marcar_actividad_completada
)

app_name = 'crm'

urlpatterns = [
    # Dashboard CRM
    path('', crm_dashboard, name='dashboard'),
    
    # Oportunidades
    path('oportunidades/', OportunidadListView.as_view(), name='oportunidad_list'),
    path('oportunidades/nueva/', OportunidadCreateView.as_view(), name='oportunidad_create'),
    path('oportunidades/<uuid:pk>/', OportunidadDetailView.as_view(), name='oportunidad_detail'),
    path('oportunidades/<uuid:pk>/editar/', OportunidadUpdateView.as_view(), name='oportunidad_update'),
    
    # Actividades
    path('actividades/nueva/', ActividadCreateView.as_view(), name='actividad_create'),
    path('actividades/<uuid:pk>/editar/', ActividadUpdateView.as_view(), name='actividad_update'),
    path('actividades/<uuid:pk>/completar/', marcar_actividad_completada, name='marcar_actividad_completada'),
    
    # Notas
    path('oportunidades/<uuid:pk>/agregar-nota/', agregar_nota_oportunidad, name='agregar_nota_oportunidad'),
    
    # Reportes
    path('reportes/pipeline/', reporte_pipeline, name='reporte_pipeline'),
]