from django.urls import path
from . import views

app_name = 'rutas'

urlpatterns = [
    # Dashboard principal de rutas
    path('', views.RutasDashboardView.as_view(), name='dashboard'),
    
    # Gestión de asignaciones (para administradores)
    path('asignaciones/', views.AsignacionListView.as_view(), name='asignaciones'),
    path('asignaciones/crear/', views.AsignacionCreateView.as_view(), name='asignacion_create'),
    path('asignaciones/<int:pk>/editar/', views.AsignacionUpdateView.as_view(), name='asignacion_update'),
    path('asignaciones/<int:pk>/eliminar/', views.AsignacionDeleteView.as_view(), name='asignacion_delete'),
    
    # Vista para vendedores - sus clientes asignados
    path('mis-clientes/', views.MisClientesView.as_view(), name='mis_clientes'),
    path('cliente/<int:cliente_id>/', views.ClienteDetailView.as_view(), name='cliente_detail'),
    
    # Gestión de visitas
    path('visitas/crear/', views.VisitaCreateView.as_view(), name='visita_create'),
    path('visitas/<int:pk>/completar/', views.CompletarVisitaView.as_view(), name='completar_visita'),
]