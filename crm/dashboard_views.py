"""
Vistas especializadas para dashboard y reportes del CRM
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count, Avg, Case, When, Value, F
from datetime import datetime, timedelta, date
from django.utils import timezone
from django.db.models import DecimalField

from .models import Oportunidad, Actividad, NotaOportunidad, EstadoOportunidad
from ventas.models import Cliente

# ============= DASHBOARD CRM =============

@login_required
def crm_dashboard(request):
    """Dashboard principal del CRM"""
    
    # Filtros de fecha - último trimestre por defecto
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=90)
    
    # KPIs principales
    total_oportunidades = Oportunidad.objects.count()
    oportunidades_abiertas = Oportunidad.objects.exclude(
        estado__in=['cerrado_ganado', 'cerrado_perdido']
    ).count()
    
    # Valor del pipeline
    pipeline_value = Oportunidad.objects.exclude(
        estado__in=['cerrado_ganado', 'cerrado_perdido']
    ).aggregate(
        total=Sum('valor_estimado'),
        ponderado=Sum(
            Case(
                When(valor_estimado__isnull=False, then=F('valor_estimado') * F('probabilidad') / 100),
                default=Value(0),
                output_field=DecimalField(max_digits=15, decimal_places=2)
            )
        )
    )
    
    # Oportunidades por estado
    oportunidades_por_estado = Oportunidad.objects.values('estado').annotate(
        count=Count('id'),
        valor=Sum('valor_estimado')
    ).order_by('estado')
    
    # Actividades pendientes del usuario
    actividades_pendientes = Actividad.objects.filter(
        responsable=request.user,
        completada=False,
        fecha_actividad__gte=timezone.now()
    ).order_by('fecha_actividad')[:5]
    
    # Actividades vencidas
    actividades_vencidas = Actividad.objects.filter(
        responsable=request.user,
        completada=False,
        fecha_actividad__lt=timezone.now()
    ).count()
    
    # Oportunidades recientes
    oportunidades_recientes = Oportunidad.objects.select_related(
        'cliente', 'vendedor'
    ).order_by('-fecha_creacion')[:5]
    
    # Conversiones del mes
    mes_actual = timezone.now().replace(day=1)
    oportunidades_ganadas = Oportunidad.objects.filter(
        estado='cerrado_ganado',
        fecha_cierre_real__gte=mes_actual
    ).count()
    
    oportunidades_cerradas_mes = Oportunidad.objects.filter(
        fecha_cierre_real__gte=mes_actual,
        estado__in=['cerrado_ganado', 'cerrado_perdido']
    ).count()
    
    tasa_conversion = 0
    if oportunidades_cerradas_mes > 0:
        tasa_conversion = (oportunidades_ganadas / oportunidades_cerradas_mes) * 100
    
    # Top vendedores
    top_vendedores = Oportunidad.objects.filter(
        estado='cerrado_ganado',
        fecha_cierre_real__gte=mes_actual
    ).values('vendedor__first_name', 'vendedor__last_name').annotate(
        total_valor=Sum('valor_estimado'),
        count=Count('id')
    ).order_by('-total_valor')[:5]
    
    context = {
        'total_oportunidades': total_oportunidades,
        'oportunidades_abiertas': oportunidades_abiertas,
        'pipeline_total': pipeline_value['total'] or 0,
        'pipeline_ponderado': pipeline_value['ponderado'] or 0,
        'oportunidades_por_estado': oportunidades_por_estado,
        'actividades_pendientes': actividades_pendientes,
        'actividades_vencidas': actividades_vencidas,
        'oportunidades_recientes': oportunidades_recientes,
        'tasa_conversion': round(tasa_conversion, 1),
        'top_vendedores': top_vendedores,
        'estados_oportunidad': EstadoOportunidad.choices,
    }
    
    return render(request, 'crm/dashboard.html', context)

# ============= REPORTES =============

@login_required
def reporte_pipeline(request):
    """Reporte del pipeline de ventas"""
    
    # Datos por estado
    pipeline_data = []
    for estado_value, estado_label in EstadoOportunidad.choices:
        oportunidades = Oportunidad.objects.filter(estado=estado_value)
        valor_total = oportunidades.aggregate(Sum('valor_estimado'))['valor_estimado__sum'] or 0
        
        pipeline_data.append({
            'estado': estado_label,
            'count': oportunidades.count(),
            'valor': valor_total
        })
    
    context = {
        'pipeline_data': pipeline_data,
    }
    
    return render(request, 'crm/reporte_pipeline.html', context)