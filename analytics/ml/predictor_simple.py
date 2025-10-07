"""
Predictor de demanda simplificado sin ML externas
"""

import statistics
from datetime import datetime, timedelta
from django.db.models import Q, Avg, Sum, Count
from django.utils import timezone


class PredictorDemandaSimple:
    """
    Sistema de predicción de demanda usando estadísticas simples
    """
    
    def __init__(self):
        self.precision_modelo = 0.0
    
    def extraer_datos_historicos(self, producto_id, dias_historicos=365):
        """
        Extrae datos históricos de ventas del producto
        """
        from analytics.models import EventoInventario
        
        fecha_inicio = timezone.now() - timedelta(days=dias_historicos)
        
        # Obtener eventos de ventas del producto
        eventos = EventoInventario.objects.filter(
            producto_id=producto_id,
            tipo_evento='venta',
            fecha_evento__gte=fecha_inicio
        ).order_by('fecha_evento')
        
        if not eventos.exists():
            return None
        
        # Extraer datos diarios
        ventas_por_dia = {}
        for evento in eventos:
            fecha = evento.fecha_evento.date()
            if fecha not in ventas_por_dia:
                ventas_por_dia[fecha] = 0
            ventas_por_dia[fecha] += evento.cantidad
        
        return ventas_por_dia
    
    def predecir_demanda(self, producto_id, dias_futuros=[7, 15, 30, 60, 90]):
        """
        Predice la demanda para períodos específicos usando estadísticas
        """
        ventas_historicas = self.extraer_datos_historicos(producto_id)
        
        if not ventas_historicas:
            return None
        
        # Calcular estadísticas básicas
        valores_ventas = list(ventas_historicas.values())
        
        if len(valores_ventas) < 7:  # Mínimo 7 días de datos
            return None
        
        # Estadísticas simples
        promedio_diario = statistics.mean(valores_ventas)
        mediana_diaria = statistics.median(valores_ventas)
        
        # Detectar tendencia (últimos 30 días vs anteriores)
        fechas_ordenadas = sorted(ventas_historicas.keys())
        
        if len(fechas_ordenadas) >= 60:  # Suficientes datos para tendencia
            punto_medio = len(fechas_ordenadas) // 2
            
            ventas_primeras = [ventas_historicas[fecha] for fecha in fechas_ordenadas[:punto_medio]]
            ventas_ultimas = [ventas_historicas[fecha] for fecha in fechas_ordenadas[punto_medio:]]
            
            promedio_primeras = statistics.mean(ventas_primeras)
            promedio_ultimas = statistics.mean(ventas_ultimas)
            
            if promedio_primeras > 0:
                factor_tendencia = promedio_ultimas / promedio_primeras
            else:
                factor_tendencia = 1.0
        else:
            factor_tendencia = 1.0
        
        # Análisis estacional (por día de la semana)
        ventas_por_dia_semana = {}
        for fecha, ventas in ventas_historicas.items():
            dia_semana = fecha.weekday()
            if dia_semana not in ventas_por_dia_semana:
                ventas_por_dia_semana[dia_semana] = []
            ventas_por_dia_semana[dia_semana].append(ventas)
        
        # Promedio por día de la semana
        promedio_por_dia_semana = {}
        for dia, ventas_lista in ventas_por_dia_semana.items():
            promedio_por_dia_semana[dia] = statistics.mean(ventas_lista)
        
        # Calcular predicciones
        predicciones = {}
        fecha_base = timezone.now().date()
        
        for dias in dias_futuros:
            demanda_total = 0
            
            # Predecir día por día considerando estacionalidad
            for i in range(dias):
                fecha_futura = fecha_base + timedelta(days=i)
                dia_semana = fecha_futura.weekday()
                
                # Usar promedio del día de la semana si está disponible, sino promedio general
                if dia_semana in promedio_por_dia_semana:
                    demanda_dia = promedio_por_dia_semana[dia_semana]
                else:
                    demanda_dia = promedio_diario
                
                # Aplicar factor de tendencia
                demanda_dia *= factor_tendencia
                
                demanda_total += demanda_dia
            
            predicciones[f'demanda_{dias}dias'] = max(0, int(demanda_total))
        
        # Calcular precisión simple basada en variabilidad
        if len(valores_ventas) > 1:
            desviacion = statistics.stdev(valores_ventas)
            coef_variacion = desviacion / (promedio_diario + 0.01)
            self.precision_modelo = max(0.1, min(0.9, 1 - coef_variacion))
        else:
            self.precision_modelo = 0.5
        
        return predicciones
    
    def calcular_metricas_estacionalidad(self, producto_id):
        """
        Calcula métricas de estacionalidad simples
        """
        from analytics.models import EventoInventario
        
        fecha_inicio = timezone.now() - timedelta(days=365)
        eventos = EventoInventario.objects.filter(
            producto_id=producto_id,
            tipo_evento='venta',
            fecha_evento__gte=fecha_inicio
        )
        
        if not eventos.exists():
            return {'factor_estacionalidad': 1.0, 'mes_mayor_demanda': 1}
        
        # Agrupar por mes
        ventas_por_mes = {}
        for evento in eventos:
            mes = evento.fecha_evento.month
            if mes not in ventas_por_mes:
                ventas_por_mes[mes] = 0
            ventas_por_mes[mes] += evento.cantidad
        
        if not ventas_por_mes:
            return {'factor_estacionalidad': 1.0, 'mes_mayor_demanda': 1}
        
        promedio_mensual = statistics.mean(ventas_por_mes.values())
        mes_mayor_demanda = max(ventas_por_mes, key=ventas_por_mes.get)
        factor_estacionalidad = ventas_por_mes.get(mes_mayor_demanda, promedio_mensual) / (promedio_mensual + 0.01)
        
        return {
            'factor_estacionalidad': factor_estacionalidad,
            'mes_mayor_demanda': mes_mayor_demanda,
            'ventas_por_mes': ventas_por_mes
        }