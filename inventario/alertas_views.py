from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count
from django.utils import timezone
from .models import AlertaStock, Producto


@login_required
def dashboard_alertas(request):
    """Vista para el dashboard de alertas de stock"""
    
    # Obtener alertas activas
    alertas_activas = AlertaStock.objects.filter(activa=True).select_related(
        'producto', 'producto__categoria'
    ).order_by('-nivel', '-fecha_creacion')
    
    # Estadísticas de alertas
    stats = {
        'total_activas': alertas_activas.count(),
        'criticas': alertas_activas.filter(nivel='critico').count(),
        'advertencias': alertas_activas.filter(nivel='advertencia').count(),
        'no_vistas': alertas_activas.filter(vista=False).count(),
    }
    
    # Alertas por categoría
    alertas_por_categoria = alertas_activas.values(
        'producto__categoria__nombre'
    ).annotate(
        total=Count('id')
    ).order_by('-total')
    
    context = {
        'alertas': alertas_activas[:20],  # Mostrar solo las primeras 20
        'stats': stats,
        'alertas_por_categoria': alertas_por_categoria,
    }
    
    return render(request, 'inventario/alertas/dashboard.html', context)


@login_required
def lista_alertas(request):
    """Vista completa de alertas con filtros"""
    
    alertas = AlertaStock.objects.select_related(
        'producto', 'producto__categoria'
    ).order_by('-fecha_creacion')
    
    # Filtros
    nivel_filtro = request.GET.get('nivel', '')
    tipo_filtro = request.GET.get('tipo', '')
    activa_filtro = request.GET.get('activa', '')
    categoria_filtro = request.GET.get('categoria', '')
    
    if nivel_filtro:
        alertas = alertas.filter(nivel=nivel_filtro)
    if tipo_filtro:
        alertas = alertas.filter(tipo_alerta=tipo_filtro)
    if activa_filtro:
        alertas = alertas.filter(activa=activa_filtro == 'true')
    if categoria_filtro:
        alertas = alertas.filter(producto__categoria_id=categoria_filtro)
    
    context = {
        'alertas': alertas[:50],  # Limitar a 50 para performance
        'nivel_filtro': nivel_filtro,
        'tipo_filtro': tipo_filtro,
        'activa_filtro': activa_filtro,
        'categoria_filtro': categoria_filtro,
    }
    
    return render(request, 'inventario/alertas/lista.html', context)


@login_required
def resolver_alerta(request, alerta_id):
    """Resolver una alerta específica"""
    
    alerta = get_object_or_404(AlertaStock, id=alerta_id)
    
    if request.method == 'POST':
        alerta.resolver_alerta(request.user)
        messages.success(request, f'Alerta resuelta para {alerta.producto.nombre}')
        
        # Verificar si es una solicitud AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        return redirect('inventario:dashboard_alertas')
    
    return redirect('inventario:dashboard_alertas')


@login_required
def marcar_vista_alerta(request, alerta_id):
    """Marcar una alerta como vista"""
    
    alerta = get_object_or_404(AlertaStock, id=alerta_id)
    alerta.marcar_como_vista(request.user)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('inventario:dashboard_alertas')


@login_required
def api_alertas_dashboard(request):
    """API para obtener alertas para el dashboard"""
    
    alertas = AlertaStock.obtener_alertas_dashboard(request.user, limit=10)
    
    data = []
    for alerta in alertas:
        data.append({
            'id': alerta.id,
            'producto': {
                'codigo': alerta.producto.codigo,
                'nombre': alerta.producto.nombre,
                'categoria': alerta.producto.categoria.nombre if alerta.producto.categoria else None
            },
            'tipo_alerta': alerta.get_tipo_alerta_display(),
            'nivel': alerta.nivel,
            'mensaje': alerta.mensaje,
            'stock_actual': alerta.stock_actual,
            'stock_minimo': alerta.stock_minimo,
            'fecha_creacion': alerta.fecha_creacion.isoformat(),
            'dias_desde_creacion': alerta.dias_desde_creacion,
            'requiere_atencion_urgente': alerta.requiere_atencion_urgente,
            'vista': alerta.vista,
        })
    
    return JsonResponse({
        'success': True,
        'alertas': data,
        'total': len(data)
    })


@login_required 
def generar_alertas_manuales(request):
    """Generar alertas manualmente para todos los productos"""
    
    if request.method == 'POST':
        # Ejecutar verificación de stock
        from django.core.management import call_command
        from io import StringIO
        
        output = StringIO()
        try:
            call_command('verificar_stock_bajo', '--crear-alertas', '--simular-stock', stdout=output)
            resultado = output.getvalue()
            
            messages.success(
                request, 
                'Verificación de stock completada. Se han actualizado las alertas automáticamente.'
            )
            
            # Para debugging, mostrar parte del resultado
            lines = resultado.split('\n')
            resumen_lines = [line for line in lines if 'RESUMEN' in line or '🆕' in line or '🔄' in line or '✅' in line]
            if resumen_lines:
                messages.info(request, ' | '.join(resumen_lines[:3]))
            
        except Exception as e:
            messages.error(request, f'Error al generar alertas: {str(e)}')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        return redirect('inventario:dashboard_alertas')
    
    return redirect('inventario:dashboard_alertas')