from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import AsignacionCliente, VisitaCliente, ConfiguracionRutas


@admin.register(AsignacionCliente)
class AsignacionClienteAdmin(admin.ModelAdmin):
    list_display = [
        'cliente', 'vendedor', 'frecuencia_visita', 
        'ultima_visita_display', 'proxima_visita_display',
        'estado_visita', 'activa'
    ]
    list_filter = [
        'frecuencia_visita', 'activa', 'vendedor',
        'fecha_asignacion', 'proxima_visita'
    ]
    search_fields = [
        'cliente__nombre', 'cliente__email', 
        'vendedor__username', 'vendedor__first_name', 'vendedor__last_name'
    ]
    ordering = ['proxima_visita', 'cliente__nombre']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('vendedor', 'cliente', 'frecuencia_visita', 'activa')
        }),
        ('Fechas', {
            'fields': ('ultima_visita', 'proxima_visita')
        }),
        ('Notas', {
            'fields': ('notas',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['fecha_asignacion']
    
    def ultima_visita_display(self, obj):
        if obj.ultima_visita:
            return obj.ultima_visita.strftime('%d/%m/%Y')
        return '-'
    ultima_visita_display.short_description = 'Última Visita'
    
    def proxima_visita_display(self, obj):
        if obj.proxima_visita:
            fecha = obj.proxima_visita.strftime('%d/%m/%Y')
            if obj.visita_vencida:
                return format_html('<span style="color: red; font-weight: bold;">{}</span>', fecha)
            elif obj.dias_para_proxima_visita and obj.dias_para_proxima_visita <= 3:
                return format_html('<span style="color: orange; font-weight: bold;">{}</span>', fecha)
            return fecha
        return '-'
    proxima_visita_display.short_description = 'Próxima Visita'
    
    def estado_visita(self, obj):
        if obj.visita_vencida:
            return format_html('<span style="color: red;">⚠️ Vencida</span>')
        elif obj.dias_para_proxima_visita and obj.dias_para_proxima_visita <= 3:
            return format_html('<span style="color: orange;">🔔 Próxima</span>')
        elif obj.dias_para_proxima_visita and obj.dias_para_proxima_visita <= 7:
            return format_html('<span style="color: blue;">📅 Esta semana</span>')
        return format_html('<span style="color: green;">✅ Al día</span>')
    estado_visita.short_description = 'Estado'


@admin.register(VisitaCliente)
class VisitaClienteAdmin(admin.ModelAdmin):
    list_display = [
        'cliente_display', 'vendedor_display', 'fecha_programada_display',
        'estado', 'resultado', 'fecha_realizada_display'
    ]
    list_filter = [
        'estado', 'resultado', 'requiere_seguimiento',
        'fecha_programada', 'fecha_realizada',
        'asignacion__vendedor'
    ]
    search_fields = [
        'asignacion__cliente__nombre', 'asignacion__vendedor__username',
        'observaciones', 'productos_mostrados'
    ]
    ordering = ['-fecha_programada']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('asignacion', 'fecha_programada', 'estado')
        }),
        ('Resultado de la Visita', {
            'fields': ('fecha_realizada', 'resultado', 'pedido_generado')
        }),
        ('Detalles', {
            'fields': ('observaciones', 'productos_mostrados'),
            'classes': ('collapse',)
        }),
        ('Seguimiento', {
            'fields': ('requiere_seguimiento', 'fecha_seguimiento'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['creada_por', 'fecha_creacion', 'fecha_modificacion']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Solo al crear
            obj.creada_por = request.user
        super().save_model(request, obj, form, change)
    
    def cliente_display(self, obj):
        return obj.cliente.nombre_completo
    cliente_display.short_description = 'Cliente'
    
    def vendedor_display(self, obj):
        return obj.vendedor.get_full_name() or obj.vendedor.username
    vendedor_display.short_description = 'Vendedor'
    
    def fecha_programada_display(self, obj):
        fecha = obj.fecha_programada.strftime('%d/%m/%Y %H:%M')
        if obj.esta_vencida:
            return format_html('<span style="color: red;">{}</span>', fecha)
        return fecha
    fecha_programada_display.short_description = 'Fecha Programada'
    
    def fecha_realizada_display(self, obj):
        if obj.fecha_realizada:
            return obj.fecha_realizada.strftime('%d/%m/%Y %H:%M')
        return '-'
    fecha_realizada_display.short_description = 'Fecha Realizada'


@admin.register(ConfiguracionRutas)
class ConfiguracionRutasAdmin(admin.ModelAdmin):
    list_display = [
        'frecuencia_default', 'dias_alerta_vencimiento',
        'max_clientes_por_vendedor', 'auto_reprogramar'
    ]
    
    fieldsets = (
        ('Configuración General', {
            'fields': ('frecuencia_default', 'dias_alerta_vencimiento')
        }),
        ('Límites', {
            'fields': ('max_clientes_por_vendedor',)
        }),
        ('Automatización', {
            'fields': ('auto_reprogramar',)
        }),
    )
    
    def has_add_permission(self, request):
        # Solo permitir una configuración
        return not ConfiguracionRutas.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # No permitir eliminar la configuración
        return False


# Personalización del admin site
admin.site.site_header = "Administración de Rutas - DistribucioneShaddai"
admin.site.site_title = "Rutas Admin"
admin.site.index_title = "Gestión de Rutas de Vendedores"