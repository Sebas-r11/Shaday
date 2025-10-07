from django.contrib import admin
from .models import Cliente, Cotizacion, Pedido, Factura, Entrega, ItemRechazado

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['numero_documento', 'nombre_completo', 'tipo_cliente', 'ciudad', 'activo', 'fecha_creacion']
    list_filter = ['tipo_cliente', 'activo', 'ciudad']
    search_fields = ['numero_documento', 'nombre_completo', 'telefono']
    readonly_fields = ['fecha_creacion']

@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ['numero', 'cliente', 'estado', 'total', 'fecha_creacion']
    list_filter = ['estado', 'fecha_creacion']
    search_fields = ['numero', 'cliente__nombre_completo']
    readonly_fields = ['fecha_creacion']

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'cliente', 'estado', 'total', 'fecha_creacion']
    list_filter = ['estado', 'fecha_creacion']
    search_fields = ['numero', 'cliente__nombre_completo']
    readonly_fields = ['fecha_creacion']

@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ['numero', 'cliente', 'estado', 'total', 'fecha_creacion']
    list_filter = ['estado', 'fecha_creacion']
    search_fields = ['numero', 'cliente__nombre_completo']
    readonly_fields = ['fecha_creacion']

@admin.register(Entrega)
class EntregaAdmin(admin.ModelAdmin):
    list_display = ['numero', 'pedido', 'repartidor', 'estado', 'fecha_programada']
    list_filter = ['estado', 'fecha_programada']
    search_fields = ['numero', 'pedido__numero']
    readonly_fields = ['numero']

@admin.register(ItemRechazado)
class ItemRechazadoAdmin(admin.ModelAdmin):
    list_display = ['entrega', 'item_pedido', 'cantidad_rechazada', 'motivo', 'fecha_rechazo']
    list_filter = ['motivo', 'fecha_rechazo']
    search_fields = ['entrega__numero', 'item_pedido__producto__nombre']
    readonly_fields = ['fecha_rechazo', 'valor_rechazado']
    
    def valor_rechazado(self, obj):
        return f"${obj.valor_rechazado:,.2f}"
    valor_rechazado.short_description = "Valor Rechazado"
