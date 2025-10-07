from django.contrib import admin
from .models import (
    AnalisisVentasCliente, PrediccionDemanda, AnalisisProveedores,
    ParametrosMRP, ReporteAnalisis, EventoInventario
)


@admin.register(AnalisisVentasCliente)
class AnalisisVentasClienteAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'producto', 'total_pedidos', 'valor_total_comprado', 'categoria_cliente', 'fecha_analisis']
    list_filter = ['categoria_cliente', 'fecha_analisis']
    search_fields = ['cliente__nombre', 'producto__nombre']
    readonly_fields = ['fecha_analisis', 'confiabilidad_prediccion']


@admin.register(PrediccionDemanda)
class PrediccionDemandaAdmin(admin.ModelAdmin):
    list_display = ['producto', 'demanda_30dias', 'demanda_60dias', 'demanda_90dias', 'precision_modelo', 'fecha_prediccion']
    list_filter = ['riesgo_desabastecimiento', 'fecha_prediccion']
    search_fields = ['producto__nombre']
    readonly_fields = ['fecha_prediccion']


@admin.register(AnalisisProveedores)
class AnalisisProveedoresAdmin(admin.ModelAdmin):
    list_display = ['proveedor', 'clasificacion', 'puntualidad_promedio', 'completitud_promedio', 'fecha_analisis']
    list_filter = ['clasificacion', 'fecha_analisis']
    search_fields = ['proveedor__nombre']
    readonly_fields = ['fecha_analisis']


@admin.register(ParametrosMRP)
class ParametrosMRPAdmin(admin.ModelAdmin):
    list_display = ['horizonte_planificacion_dias', 'factor_seguridad_stock', 'es_configuracion_activa', 'fecha_actualizacion']
    list_filter = ['es_configuracion_activa', 'fecha_actualizacion']


@admin.register(ReporteAnalisis)
class ReporteAnalisisAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo_reporte', 'productos_analizados', 'precision_promedio', 'fecha_generacion']
    list_filter = ['tipo_reporte', 'fecha_generacion']
    search_fields = ['titulo', 'recomendaciones']
    readonly_fields = ['fecha_generacion', 'datos_reporte']


@admin.register(EventoInventario)
class EventoInventarioAdmin(admin.ModelAdmin):
    list_display = ['producto', 'tipo_evento', 'cantidad', 'precio_unitario', 'cliente', 'fecha_evento']
    list_filter = ['tipo_evento', 'fecha_evento']
    search_fields = ['producto__nombre', 'cliente__nombre', 'proveedor__nombre']
    readonly_fields = ['fecha_evento']