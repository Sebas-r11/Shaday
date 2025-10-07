from django.urls import path
from django.contrib.auth import views as auth_views

# Importaciones especializadas después de la refactorización
from .general_views import DashboardView
from .usuarios_views import (
    UserListView, UserCreateView, UserDetailView, UserUpdateView,
    toggle_user_status, user_management_dashboard
)
from .autenticacion_views import change_user_password
from .navegacion_views import (
    repartidor_gps_config, dashboard_repartidores, toggle_repartidor_disponibilidad
)

app_name = 'accounts'

urlpatterns = [
    # Autenticación
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Dashboard
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    
    # Gestión de Usuarios (solo administradores)
    path('usuarios/', UserListView.as_view(), name='user_list'),
    path('usuarios/crear/', UserCreateView.as_view(), name='user_create'),
    path('usuarios/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    path('usuarios/<int:pk>/editar/', UserUpdateView.as_view(), name='user_update'),
    path('usuarios/<int:pk>/cambiar-password/', change_user_password, name='change_user_password'),
    path('usuarios/<int:pk>/toggle-status/', toggle_user_status, name='toggle_user_status'),
    
    # Dashboard de gestión de usuarios
    path('gestion-usuarios/', user_management_dashboard, name='user_management_dashboard'),
    
    # Configuración GPS para repartidores
    path('repartidor/gps/', repartidor_gps_config, name='repartidor_gps'),
    
    # Dashboard de seguimiento de repartidores (administradores)
    path('repartidores/dashboard/', dashboard_repartidores, name='dashboard_repartidores'),
    path('repartidor/<int:repartidor_id>/toggle-disponibilidad/', toggle_repartidor_disponibilidad, name='toggle_repartidor_disponibilidad'),
]