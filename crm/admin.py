from django.contrib import admin
from .models import Oportunidad, Actividad, NotaOportunidad

@admin.register(Oportunidad)
class OportunidadAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'cliente', 'estado', 'valor_estimado', 'probabilidad', 'vendedor', 'fecha_creacion']
    list_filter = ['estado', 'prioridad', 'fuente', 'vendedor', 'fecha_creacion']
    search_fields = ['nombre', 'cliente__nombre', 'cliente__razon_social', 'descripcion']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion', 'usuario_creacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'cliente', 'vendedor')
        }),
        ('Información Comercial', {
            'fields': ('valor_estimado', 'probabilidad', 'estado', 'fecha_cierre_estimada', 'fecha_cierre_real')
        }),
        ('Clasificación', {
            'fields': ('prioridad', 'fuente')
        }),
        ('Detalles', {
            'fields': ('descripcion', 'productos_interes', 'competencia')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion', 'usuario_creacion'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_creacion = request.user
        super().save_model(request, obj, form, change)

@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ['asunto', 'oportunidad', 'tipo', 'fecha_actividad', 'responsable', 'completada']
    list_filter = ['tipo', 'completada', 'fecha_actividad', 'responsable']
    search_fields = ['asunto', 'descripcion', 'oportunidad__nombre']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion', 'usuario_creacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('oportunidad', 'tipo', 'asunto', 'descripcion')
        }),
        ('Programación', {
            'fields': ('fecha_actividad', 'duracion_minutos', 'responsable', 'completada')
        }),
        ('Resultados', {
            'fields': ('resultado', 'proxima_accion'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion', 'usuario_creacion'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_creacion = request.user
        super().save_model(request, obj, form, change)

@admin.register(NotaOportunidad)
class NotaOportunidadAdmin(admin.ModelAdmin):
    list_display = ['oportunidad', 'usuario_creacion', 'fecha_creacion', 'es_publica']
    list_filter = ['es_publica', 'fecha_creacion', 'usuario_creacion']
    search_fields = ['contenido', 'oportunidad__nombre']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
