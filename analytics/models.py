"""
Modelos para el sistema de analytics, IA y MRP
"""
from django.db import models
from django.contrib.auth import get_user_model
from inventario.models import Producto, Proveedor
from ventas.models import Cliente, Pedido
from decimal import Decimal
from datetime import datetime, timedelta
import json

User = get_user_model()


class AnalisisVentasCliente(models.Model):
    """Análisis detallado de patrones de ventas por cliente"""
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='analisis_ventas')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='analisis_por_cliente')
    
    # Estadísticas de compra
    total_pedidos = models.IntegerField(default=0)
    cantidad_total_comprada = models.IntegerField(default=0)
    valor_total_comprado = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Patrones temporales
    frecuencia_compra_dias = models.FloatField(default=0)  # Promedio de días entre compras
    mes_mayor_actividad = models.IntegerField(default=1)  # Mes del año con más compras
    dia_semana_preferido = models.IntegerField(default=1)  # Día de la semana preferido
    
    # Análisis de precio
    precio_promedio_pagado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sensibilidad_precio = models.FloatField(default=0)  # Qué tan sensible es al precio
    
    # Predicciones
    demanda_predicha_30dias = models.IntegerField(default=0)
    demanda_predicha_60dias = models.IntegerField(default=0)
    demanda_predicha_90dias = models.IntegerField(default=0)
    
    # Clasificación de cliente
    CATEGORIA_CLIENTE_CHOICES = [
        ('premium', 'Cliente Premium'),
        ('frecuente', 'Cliente Frecuente'), 
        ('ocasional', 'Cliente Ocasional'),
        ('nuevo', 'Cliente Nuevo'),
        ('inactivo', 'Cliente Inactivo'),
    ]
    categoria_cliente = models.CharField(max_length=20, choices=CATEGORIA_CLIENTE_CHOICES, default='nuevo')
    
    # Metadatos
    fecha_analisis = models.DateTimeField(auto_now=True)
    confiabilidad_prediccion = models.FloatField(default=0)  # 0-1, qué tan confiable es
    
    class Meta:
        unique_together = ['cliente', 'producto']
        verbose_name = "Análisis de Ventas por Cliente"
        verbose_name_plural = "Análisis de Ventas por Cliente"
    
    def __str__(self):
        return f"{self.cliente.nombre} - {self.producto.nombre}"


class PrediccionDemanda(models.Model):
    """Predicciones de demanda usando machine learning"""
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='predicciones')
    
    # Predicciones por período
    demanda_7dias = models.IntegerField(default=0)
    demanda_15dias = models.IntegerField(default=0)
    demanda_30dias = models.IntegerField(default=0)
    demanda_60dias = models.IntegerField(default=0)
    demanda_90dias = models.IntegerField(default=0)
    
    # Factores de influencia
    estacionalidad_factor = models.FloatField(default=1.0)
    tendencia_crecimiento = models.FloatField(default=0.0)  # % de crecimiento esperado
    
    # Confiabilidad del modelo
    precision_modelo = models.FloatField(default=0.0)  # R² del modelo
    error_promedio = models.FloatField(default=0.0)
    
    # Recomendaciones de compra
    cantidad_recomendada_compra = models.IntegerField(default=0)
    punto_reorden_sugerido = models.IntegerField(default=0)
    stock_seguridad_sugerido = models.IntegerField(default=0)
    
    # Análisis de riesgo
    RIESGO_CHOICES = [
        ('bajo', 'Riesgo Bajo'),
        ('medio', 'Riesgo Medio'),
        ('alto', 'Riesgo Alto'),
        ('critico', 'Riesgo Crítico'),
    ]
    riesgo_desabastecimiento = models.CharField(max_length=10, choices=RIESGO_CHOICES, default='medio')
    
    fecha_prediccion = models.DateTimeField(auto_now=True)
    
    class Meta:
        get_latest_by = 'fecha_prediccion'
        verbose_name = "Predicción de Demanda"
        verbose_name_plural = "Predicciones de Demanda"
    
    def __str__(self):
        return f"Predicción {self.producto.nombre} - {self.fecha_prediccion.strftime('%Y-%m-%d')}"


class AnalisisProveedores(models.Model):
    """Análisis de rendimiento y confiabilidad de proveedores"""
    
    proveedor = models.OneToOneField(Proveedor, on_delete=models.CASCADE, related_name='analisis')
    
    # Métricas de desempeño
    ordenes_totales = models.IntegerField(default=0)
    ordenes_a_tiempo = models.IntegerField(default=0)
    ordenes_completas = models.IntegerField(default=0)
    
    # Calidad del servicio
    puntualidad_promedio = models.FloatField(default=0.0)  # % órdenes a tiempo
    completitud_promedio = models.FloatField(default=0.0)  # % órdenes completas
    
    # Análisis de precios
    competitividad_precios = models.FloatField(default=0.0)  # Ranking vs otros proveedores
    estabilidad_precios = models.FloatField(default=0.0)  # Qué tan estables son sus precios
    
    # Capacidad y confiabilidad
    capacidad_estimada = models.IntegerField(default=0)  # Productos por mes
    tiempo_entrega_promedio = models.FloatField(default=0.0)  # Días promedio
    
    # Clasificación del proveedor
    CLASIFICACION_CHOICES = [
        ('estrategico', 'Proveedor Estratégico'),
        ('preferido', 'Proveedor Preferido'),
        ('aprobado', 'Proveedor Aprobado'),
        ('critico', 'Proveedor en Revisión'),
    ]
    clasificacion = models.CharField(max_length=20, choices=CLASIFICACION_CHOICES, default='aprobado')
    
    # Riesgo y recomendaciones
    nivel_riesgo = models.FloatField(default=0.5)  # 0-1, donde 1 es muy riesgoso
    
    fecha_analisis = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Análisis de Proveedor"
        verbose_name_plural = "Análisis de Proveedores"
    
    def __str__(self):
        return f"Análisis {self.proveedor.nombre}"


class ParametrosMRP(models.Model):
    """Parámetros de configuración del sistema MRP"""
    
    # Configuración general
    horizonte_planificacion_dias = models.IntegerField(default=90)
    factor_seguridad_stock = models.FloatField(default=1.2)
    
    # Parámetros de machine learning
    ventana_historica_dias = models.IntegerField(default=365)
    peso_tendencia_reciente = models.FloatField(default=0.7)
    
    # Umbrales de alerta
    umbral_stock_critico = models.FloatField(default=0.1)  # 10% del stock mínimo
    umbral_precision_minima = models.FloatField(default=0.7)  # 70% de precisión mínima
    
    # Configuración por defecto
    es_configuracion_activa = models.BooleanField(default=True)
    
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_actualizacion = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Parámetros MRP"
        verbose_name_plural = "Parámetros MRP"
    
    def __str__(self):
        return f"Configuración MRP - {self.fecha_actualizacion.strftime('%Y-%m-%d')}"


class ReporteAnalisis(models.Model):
    """Reportes generados por el sistema de análisis"""
    
    TIPO_REPORTE_CHOICES = [
        ('demanda', 'Análisis de Demanda'),
        ('clientes', 'Análisis de Clientes'), 
        ('proveedores', 'Análisis de Proveedores'),
        ('inventario', 'Optimización de Inventario'),
        ('mrp', 'Planificación MRP'),
    ]
    
    tipo_reporte = models.CharField(max_length=20, choices=TIPO_REPORTE_CHOICES)
    titulo = models.CharField(max_length=200)
    
    # Datos del reporte (JSON)
    datos_reporte = models.JSONField()  # Gráficos, tablas, métricas
    
    # Recomendaciones generadas
    recomendaciones = models.TextField()
    
    # Metadatos
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    usuario_generacion = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Estadísticas del reporte
    productos_analizados = models.IntegerField(default=0)
    clientes_analizados = models.IntegerField(default=0)
    precision_promedio = models.FloatField(default=0.0)
    
    class Meta:
        ordering = ['-fecha_generacion']
        verbose_name = "Reporte de Análisis"
        verbose_name_plural = "Reportes de Análisis"
    
    def __str__(self):
        return f"{self.titulo} - {self.fecha_generacion.strftime('%Y-%m-%d %H:%M')}"


class EventoInventario(models.Model):
    """Registro de todos los movimientos de inventario para análisis"""
    
    TIPO_EVENTO_CHOICES = [
        ('venta', 'Venta'),
        ('compra', 'Compra'),
        ('ajuste', 'Ajuste de Inventario'),
        ('devolucion', 'Devolución'),
        ('merma', 'Merma/Pérdida'),
    ]
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='eventos_inventario')
    tipo_evento = models.CharField(max_length=20, choices=TIPO_EVENTO_CHOICES)
    
    # Detalles del movimiento
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Contexto
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Stock después del evento
    stock_resultante = models.IntegerField()
    
    # Metadatos
    fecha_evento = models.DateTimeField(auto_now_add=True)
    usuario_responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    observaciones = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-fecha_evento']
        verbose_name = "Evento de Inventario"
        verbose_name_plural = "Eventos de Inventario"
        indexes = [
            models.Index(fields=['producto', 'fecha_evento']),
            models.Index(fields=['cliente', 'fecha_evento']),
            models.Index(fields=['tipo_evento', 'fecha_evento']),
        ]
    
    def __str__(self):
        return f"{self.tipo_evento.title()} - {self.producto.nombre} ({self.cantidad})"