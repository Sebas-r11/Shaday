"""
Vistas especializadas para gestión de usuarios y perfiles
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count, Sum, Q
from django.http import JsonResponse
from django.utils import timezone

from inventario.models import MovimientoInventario
from ventas.models import Entrega
from .models import User
from .forms import UserCreateForm, UserUpdateForm

# ============= MIXINS PARA CONTROL DE ACCESO =============

class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin que requiere permisos de administrador"""
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_superuser or 
            self.request.user.can_manage_users()
        )
    
    def handle_no_permission(self):
        messages.error(self.request, "No tienes permisos para gestionar usuarios.")
        return redirect('accounts:dashboard')

# ============= VISTAS DE GESTIÓN DE USUARIOS =============

class UserListView(AdminRequiredMixin, ListView):
    """Lista de usuarios del sistema"""
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'usuarios'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.select_related().order_by('-date_joined')
        
        # Filtros de búsqueda
        search = self.request.GET.get('search')
        role = self.request.GET.get('role')
        activo = self.request.GET.get('activo')
        
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(documento__icontains=search)
            )
        
        if role and role != 'all':
            queryset = queryset.filter(role=role)
        
        if activo == 'true':
            queryset = queryset.filter(activo=True)
        elif activo == 'false':
            queryset = queryset.filter(activo=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = {
            'search': self.request.GET.get('search', ''),
            'role': self.request.GET.get('role', 'all'),
            'activo': self.request.GET.get('activo', 'all'),
        }
        context['roles'] = User.ROLE_CHOICES
        return context

class UserCreateView(AdminRequiredMixin, CreateView):
    """Crear nuevo usuario"""
    model = User
    form_class = UserCreateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Usuario {form.cleaned_data["username"]} creado exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Nuevo Usuario'
        context['subtitle'] = 'Registrar usuario en el sistema'
        return context

class UserDetailView(AdminRequiredMixin, DetailView):
    """Detalle de usuario"""
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'usuario'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas del usuario si es necesario
        user = self.object
        
        # Actividad reciente (últimos movimientos de inventario si es almacenista)
        if user.can_adjust_inventory():
            context['movimientos_recientes'] = MovimientoInventario.objects.filter(
                usuario=user
            ).select_related('producto', 'bodega').order_by('-fecha_movimiento')[:10]
        
        return context

class UserUpdateView(AdminRequiredMixin, UpdateView):
    """Actualizar usuario existente"""
    model = User
    form_class = UserUpdateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, f'Usuario {form.cleaned_data["username"]} actualizado exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Usuario: {self.object.username}'
        context['subtitle'] = 'Actualizar información del usuario'
        return context

# ============= FUNCIONES DE GESTIÓN =============

@login_required
def toggle_user_status(request, pk):
    """Activar/desactivar usuario via AJAX"""
    if not request.user.can_manage_users():
        return JsonResponse({'success': False, 'message': 'No tienes permisos'})
    
    if request.method == 'POST':
        user = get_object_or_404(User, pk=pk)
        
        # No permitir desactivar superusuarios
        if user.is_superuser and not request.user.is_superuser:
            return JsonResponse({
                'success': False, 
                'message': 'No puedes desactivar un superusuario'
            })
        
        # No permitir auto-desactivación
        if user == request.user:
            return JsonResponse({
                'success': False, 
                'message': 'No puedes desactivarte a ti mismo'
            })
        
        user.activo = not user.activo
        user.save()
        
        status = 'activado' if user.activo else 'desactivado'
        return JsonResponse({
            'success': True,
            'message': f'Usuario {status} exitosamente',
            'new_status': user.activo
        })
    
    return JsonResponse({'success': False})

@login_required
def user_management_dashboard(request):
    """Dashboard específico para gestión de usuarios"""
    if not request.user.can_manage_users():
        messages.error(request, "No tienes permisos para gestionar usuarios.")
        return redirect('accounts:dashboard')
    
    # Estadísticas de usuarios
    total_users = User.objects.count()
    active_users = User.objects.filter(activo=True).count()
    inactive_users = total_users - active_users
    
    # Usuarios por rol
    users_by_role = User.objects.values('role').annotate(count=Count('id')).order_by('role')
    
    # Usuarios recientes (últimos 10)
    recent_users = User.objects.order_by('-date_joined')[:10]
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'users_by_role': users_by_role,
        'recent_users': recent_users,
        'roles': User.ROLE_CHOICES,
    }
    
    return render(request, 'accounts/user_management_dashboard.html', context)