from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count, Sum, Q
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta

from inventario.models import Producto, Stock, MovimientoInventario
from ventas.models import Pedido, Cotizacion, Cliente, Entrega
from .models import User
from .forms import UserCreateForm, UserUpdateForm, ChangePasswordForm

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/dashboard.html'
    
    def get_template_names(self):
        """Seleccionar template específico según el rol del usuario"""
        if self.request.user.role == 'repartidor':
            return ['accounts/dashboard_repartidor.html']
        return [self.template_name]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Configuración base de permisos
        context['user_role'] = user.role
        context['user_permissions'] = {
            'can_manage_users': user.can_manage_users(),
            'can_see_costs': user.can_see_costs(),
            'can_adjust_inventory': user.can_adjust_inventory(),
            'can_access_crm': user.can_access_crm(),
            'can_create_sales': user.can_create_sales(),
            'can_prepare_orders': user.can_prepare_orders(),
            'can_deliver_orders': user.can_deliver_orders(),
        }
        
        # Dashboard personalizado por rol
        if user.role == 'vendedor':
            # Dashboard para vendedores - solo sus ventas
            context.update(self.get_vendedor_dashboard_data(user))
        elif user.role == 'bodega':
            # Dashboard para bodegueros - inventario y pedidos asignados
            context.update(self.get_bodeguero_dashboard_data(user))
        elif user.role == 'repartidor':
            # Dashboard para repartidores - entregas y rutas
            context.update(self.get_repartidor_dashboard_data(user))
        else:
            # Dashboard para administradores - vista completa
            context.update(self.get_admin_dashboard_data(user))
        
        return context
    
    def get_vendedor_dashboard_data(self, user):
        """Dashboard personalizado para vendedores"""
        hoy = timezone.now().date()
        mes_actual = hoy.replace(day=1)
        
        # Como los modelos no tienen campo vendedor, mostramos todos los pedidos/cotizaciones
        # En el futuro se puede filtrar por cliente asignado al vendedor
        todos_pedidos = Pedido.objects.all()
        todas_cotizaciones = Cotizacion.objects.all()
        
        # Estadísticas de ventas del mes actual
        pedidos_mes = todos_pedidos.filter(fecha_creacion__gte=mes_actual)
        cotizaciones_mes = todas_cotizaciones.filter(fecha_creacion__gte=mes_actual)
        
        # Ventas del día
        pedidos_hoy = todos_pedidos.filter(fecha_creacion__date=hoy)
        ventas_hoy = sum(pedido.total for pedido in pedidos_hoy if pedido.total)
        
        # Ventas del mes
        ventas_mes = sum(pedido.total for pedido in pedidos_mes if pedido.total)
        
        # Pedidos por estado
        pedidos_por_estado = {
            'borrador': todos_pedidos.filter(estado='borrador').count(),
            'enviado': todos_pedidos.filter(estado='enviado').count(),
            'en_proceso': todos_pedidos.filter(estado='en_proceso').count(),
            'completado': todos_pedidos.filter(estado='completado').count(),
            'entregado': todos_pedidos.filter(estado='entregado').count(),
        }
        
        return {
            'total_productos': Producto.objects.filter(activo=True).count(),
            'mis_pedidos_total': todos_pedidos.count(),
            'mis_cotizaciones_total': todas_cotizaciones.count(),
            'ventas_hoy': ventas_hoy,
            'ventas_mes': ventas_mes,
            'pedidos_hoy': pedidos_hoy.count(),
            'pedidos_mes': pedidos_mes.count(),
            'cotizaciones_mes': cotizaciones_mes.count(),
            'pedidos_por_estado': pedidos_por_estado,
            'pedidos_recientes': todos_pedidos.order_by('-fecha_creacion')[:5],
            'cotizaciones_recientes': todas_cotizaciones.order_by('-fecha_creacion')[:5],
            # No mostrar productos bajo stock para vendedores
            'productos_bajo_stock': [],
            'is_vendedor_dashboard': True,
        }
    
    def get_bodeguero_dashboard_data(self, user):
        """Dashboard personalizado para bodegueros"""
        # Todos los pedidos que necesitan alistamiento
        pedidos_pendientes_alistamiento = Pedido.objects.filter(
            estado__in=['borrador', 'enviado']
        )
        
        # Todos los pedidos (sin asignación específica ya que el modelo no tiene este campo)
        todos_pedidos = Pedido.objects.all()
        
        return {
            'total_productos': Producto.objects.filter(activo=True).count(),
            'productos_bajo_stock': [],  # Los bodegueros no ven alertas de stock
            'pedidos_asignados': todos_pedidos.count(),
            'pedidos_pendientes_alistamiento': pedidos_pendientes_alistamiento.count(),
            'pedidos_recientes': pedidos_pendientes_alistamiento.order_by('-fecha_creacion')[:10],
            'movimientos_recientes': MovimientoInventario.objects.filter(
                usuario=user
            ).select_related('producto', 'bodega').order_by('-fecha_movimiento')[:10] if hasattr(MovimientoInventario, 'usuario') else [],
            'is_bodeguero_dashboard': True,
        }
    
    def get_repartidor_dashboard_data(self, user):
        """Dashboard especializado para repartidores - solo entregas y rutas"""
        hoy = timezone.now().date()
        
        # Entregas asignadas al repartidor
        entregas_asignadas = Entrega.objects.filter(repartidor=user)
        entregas_hoy = entregas_asignadas.filter(fecha_programada=hoy)
        entregas_pendientes = entregas_asignadas.filter(estado='programada')
        entregas_en_camino = entregas_asignadas.filter(estado='en_camino')
        
        # Entregas para generar ruta optimizada
        entregas_para_ruta = entregas_asignadas.filter(
            estado__in=['programada', 'en_camino'],
            fecha_programada=hoy
        ).select_related('pedido', 'pedido__cliente')
        
        # Estadísticas del repartidor
        total_entregas_realizadas = entregas_asignadas.filter(estado='entregado').count()
        entregas_fallidas = entregas_asignadas.filter(estado='fallido').count()
        
        return {
            'entregas_hoy': entregas_hoy.count(),
            'entregas_pendientes': entregas_pendientes.count(),
            'entregas_en_camino': entregas_en_camino.count(),
            'total_entregas_realizadas': total_entregas_realizadas,
            'entregas_fallidas': entregas_fallidas,
            'entregas_para_ruta': entregas_para_ruta,
            'entregas_recientes': entregas_asignadas.order_by('-fecha_programada')[:10],
            'is_repartidor_dashboard': True,
        }
    
    def get_admin_dashboard_data(self, user):
        """Dashboard completo para administradores"""
        hoy = timezone.now().date()
        
        # Ventas del día (todos los pedidos)
        pedidos_hoy = Pedido.objects.filter(fecha_creacion__date=hoy)
        ventas_hoy = sum(pedido.total for pedido in pedidos_hoy if pedido.total)
        
        return {
            'total_productos': Producto.objects.filter(activo=True).count(),
            'productos_bajo_stock': self.get_productos_bajo_stock(),
            'ventas_hoy': ventas_hoy,
            'pedidos_hoy': pedidos_hoy.count(),
            'total_clientes': Cliente.objects.filter(activo=True).count(),
            'movimientos_recientes': MovimientoInventario.objects.select_related(
                'producto', 'bodega', 'usuario'
            ).order_by('-fecha_movimiento')[:10] if user.can_see_costs() and hasattr(MovimientoInventario, 'usuario') else [],
            'pedidos_recientes': Pedido.objects.order_by('-fecha_creacion')[:10],
            'is_admin_dashboard': True,
        }
    
    def get_productos_bajo_stock(self):
        """Obtiene productos que están bajo el stock mínimo"""
        productos_bajo_stock = []
        
        for producto in Producto.objects.filter(activo=True):
            stock_total = Stock.objects.filter(producto=producto).aggregate(
                total=Sum('cantidad')
            )['total'] or 0
            
            if stock_total <= producto.stock_minimo:
                productos_bajo_stock.append({
                    'producto': producto,
                    'stock_actual': stock_total,
                    'stock_minimo': producto.stock_minimo
                })
        
        return productos_bajo_stock[:10]  # Máximo 10 para el dashboard


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


@login_required
def change_user_password(request, pk):
    """Cambiar contraseña de un usuario"""
    if not request.user.can_manage_users():
        messages.error(request, "No tienes permisos para cambiar contraseñas.")
        return redirect('accounts:dashboard')
    
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            form.save(user)
            messages.success(request, f'Contraseña actualizada para {user.username}.')
            return redirect('accounts:user_detail', pk=user.pk)
    else:
        form = ChangePasswordForm()
    
    return render(request, 'accounts/change_password.html', {
        'form': form,
        'usuario': user,
        'title': f'Cambiar Contraseña: {user.username}'
    })


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


# ============= VISTAS DE CONFIGURACIÓN =============

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


@login_required
def repartidor_gps_config(request):
    """Vista para que repartidores configuren su GPS y zona de cobertura"""
    
    # Solo repartidores pueden acceder
    if request.user.role != 'repartidor':
        messages.error(request, 'Solo los repartidores pueden acceder a esta página.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'actualizar_gps':
            try:
                latitud = request.POST.get('latitud')
                longitud = request.POST.get('longitud')
                
                if latitud and longitud:
                    request.user.actualizar_ubicacion_gps(float(latitud), float(longitud))
                    messages.success(request, 'Ubicación GPS actualizada correctamente.')
                else:
                    messages.error(request, 'Coordenadas GPS inválidas.')
                    
            except (ValueError, TypeError) as e:
                messages.error(request, f'Error al actualizar GPS: {str(e)}')
        
        elif accion == 'configurar_cobertura':
            try:
                radio_cobertura = request.POST.get('radio_cobertura')
                zona_cobertura = request.POST.get('zona_cobertura', '')
                disponible_entregas = request.POST.get('disponible_entregas') == 'on'
                
                # Validar radio
                if radio_cobertura:
                    radio_float = float(radio_cobertura)
                    if 1 <= radio_float <= 50:
                        request.user.radio_cobertura_km = radio_float
                    else:
                        messages.error(request, 'El radio de cobertura debe estar entre 1 y 50 km.')
                        return redirect('accounts:repartidor_gps')
                
                request.user.zona_cobertura = zona_cobertura
                request.user.disponible_entregas = disponible_entregas
                request.user.save(update_fields=['radio_cobertura_km', 'zona_cobertura', 'disponible_entregas'])
                
                messages.success(request, 'Configuración de cobertura actualizada correctamente.')
                
            except (ValueError, TypeError) as e:
                messages.error(request, f'Error al actualizar configuración: {str(e)}')
        
        return redirect('accounts:repartidor_gps')
    
    # Obtener estadísticas del repartidor
    from ventas.models import Entrega
    
    entregas_stats = {
        'total': Entrega.objects.filter(repartidor=request.user).count(),
        'entregadas': Entrega.objects.filter(repartidor=request.user, estado='entregado').count(),
        'pendientes': Entrega.objects.filter(repartidor=request.user, estado__in=['programada', 'en_camino']).count(),
    }
    
    # Clientes en cobertura
    clientes_cobertura = request.user.get_clientes_en_cobertura()
    
    context = {
        'user': request.user,
        'entregas_stats': entregas_stats,
        'clientes_cobertura_count': len(clientes_cobertura),
    }
    
    return render(request, 'accounts/repartidor_gps.html', context)


@login_required
def dashboard_repartidores(request):
    """Dashboard para administradores - ver todos los repartidores y su estado"""
    
    # Solo administradores pueden acceder
    if not request.user.can_manage_users():
        messages.error(request, 'No tienes permisos para ver esta página.')
        return redirect('accounts:dashboard')
    
    from ventas.models import Entrega
    from django.utils import timezone
    from datetime import date
    
    # Obtener repartidores
    repartidores = User.objects.filter(role='repartidor').select_related()
    
    # Agregar estadísticas de entregas de hoy a cada repartidor
    hoy = timezone.now().date()
    for repartidor in repartidores:
        repartidor.entregas_hoy = Entrega.objects.filter(
            repartidor=repartidor,
            fecha_programada__date=hoy
        ).count()
    
    # Estadísticas generales
    stats = {
        'total_repartidores': repartidores.count(),
        'disponibles': repartidores.filter(disponible_entregas=True, activo=True).count(),
        'en_entregas': Entrega.objects.filter(
            repartidor__in=repartidores,
            estado='en_camino',
            fecha_programada__date=hoy
        ).count(),
        'con_gps': repartidores.filter(
            latitud__isnull=False,
            longitud__isnull=False
        ).count(),
    }
    
    context = {
        'repartidores': repartidores,
        'stats': stats,
    }
    
    return render(request, 'accounts/dashboard_repartidores.html', context)


@login_required 
def toggle_repartidor_disponibilidad(request, repartidor_id):
    """Toggle de disponibilidad de un repartidor (solo administradores)"""
    
    if not request.user.can_manage_users():
        return JsonResponse({'success': False, 'message': 'Sin permisos'}, status=403)
    
    try:
        repartidor = User.objects.get(id=repartidor_id, role='repartidor')
        repartidor.disponible_entregas = not repartidor.disponible_entregas
        repartidor.save(update_fields=['disponible_entregas'])
        
        return JsonResponse({
            'success': True,
            'disponible': repartidor.disponible_entregas,
            'message': f'Repartidor {"disponible" if repartidor.disponible_entregas else "no disponible"}'
        })
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Repartidor no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
