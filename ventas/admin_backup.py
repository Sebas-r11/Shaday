from django.contrib import admin
from .models import (
    Cliente, Cotizacion, Pedido, Factura,
    ItemCotizacion, ItemPedido, ItemFactura,
    Entrega
)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['numero_documento', 'nombre_completo', 'tipo_cliente', 'vendedor_asignado', 'activo', 'fecha_creacion']
    list_filter = ['tipo_cliente', 'activo', 'ciudad', 'vendedor_asignado']
    search_fields = ['numero_documento', 'nombre_completo', 'nombre_comercial', 'telefono', 'email']
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('tipo_documento', 'numero_documento', 'nombre_completo', 'nombre_comercial')
        }),
        ('Contacto', {
            'fields': ('telefono', 'email', 'direccion', 'ciudad', 'departamento')
        }),
        ('Información Comercial', {
            'fields': ('tipo_cliente', 'vendedor_asignado', 'limite_credito', 'dias_credito')
        }),
        ('Control', {
            'fields': ('activo', 'fecha_creacion', 'fecha_modificacion')
        }),
    )

class ItemCotizacionInline(admin.TabularInline):
    model = ItemCotizacion
    extra = 1
    readonly_fields = ['total']

@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ['numero', 'cliente', 'vendedor', 'total', 'estado', 'fecha', 'convertida_a_pedido']
    list_filter = ['estado', 'convertida_a_pedido', 'fecha', 'vendedor']
    search_fields = ['numero', 'cliente__nombre_completo', 'cliente__numero_documento']
    readonly_fields = ['id', 'subtotal', 'descuento_valor', 'impuestos', 'total', 'fecha', 'fecha_modificacion']
    inlines = [ItemCotizacionInline]
    
    fieldsets = (
        ('Información General', {
            'fields': ('numero', 'cliente', 'vendedor', 'fecha_vencimiento')
        }),
        ('Totales', {
            'fields': ('subtotal', 'descuento_porcentaje', 'descuento_valor', 'impuestos', 'total')
        }),
        ('Estado', {
            'fields': ('estado', 'convertida_a_pedido', 'observaciones')
        }),
    )

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ['total']

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'cliente', 'vendedor', 'total', 'estado', 'fecha', 'bodega']
    list_filter = ['estado', 'fecha', 'vendedor', 'bodega']
    search_fields = ['numero', 'cliente__nombre_completo', 'cliente__numero_documento']
    readonly_fields = ['id', 'subtotal', 'descuento_valor', 'impuestos', 'total', 'fecha', 'fecha_modificacion']
    inlines = [ItemPedidoInline]

class ItemFacturaInline(admin.TabularInline):
    model = ItemFactura
    extra = 0
    readonly_fields = ['total']

@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ['numero_fiscal', 'cliente', 'vendedor', 'total', 'estado', 'fecha']
    list_filter = ['estado', 'fecha', 'vendedor']
    search_fields = ['numero', 'numero_fiscal', 'cliente__nombre_completo', 'cliente__numero_documento']
    readonly_fields = ['id', 'subtotal', 'descuento_valor', 'impuestos', 'total', 'fecha', 'fecha_modificacion', 'cufde', 'qr_code']
    inlines = [ItemFacturaInline]


@admin.register(Entrega)
class EntregaAdmin(admin.ModelAdmin):
    list_display = ['pedido', 'repartidor', 'estado', 'fecha_programada', 'fecha_entrega', 'persona_recibe']
    list_filter = ['estado', 'fecha_programada', 'repartidor']
    search_fields = ['pedido__numero', 'pedido__cliente__nombre_completo', 'persona_recibe']
    readonly_fields = ['id', 'fecha_creacion', 'fecha_modificacion']
    
    fieldsets = (
        ('Información General', {
            'fields': ('pedido', 'repartidor', 'estado')
        }),
        ('Programación', {
            'fields': ('fecha_programada', 'fecha_salida', 'fecha_entrega')
        }),
        ('Datos de Entrega', {
            'fields': ('direccion_entrega', 'telefono_contacto', 'persona_recibe')
        }),
        ('Evidencia', {
            'fields': ('firma_digital', 'foto_evidencia')
        }),
        ('Observaciones', {
            'fields': ('observaciones', 'motivo_fallo')
        }),
        ('Control', {
            'fields': ('fecha_creacion', 'fecha_modificacion')
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.estado in ['entregado', 'devuelto']:
            # No permitir modificar entregas completadas
            readonly.extend(['pedido', 'repartidor', 'fecha_programada'])
        return readonly
