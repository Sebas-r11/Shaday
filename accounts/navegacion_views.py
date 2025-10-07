"""
Vistas especializadas para navegación y funciones de repartidores
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count

from ventas.models import Entrega
from .models import User

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