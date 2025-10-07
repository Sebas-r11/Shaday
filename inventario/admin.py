from django.contrib import admin
from .models import (
    Proveedor, Categoria, Subcategoria, Producto, ProductoProveedor, PresentacionProducto, PresentacionProveedorProducto, VarianteProducto, 
    Bodega, Stock, MovimientoInventario
)

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'nit', 'telefono', 'email', 'calificacion', 'activo', 'fecha_creacion']
    list_filter = ['activo', 'calificacion', 'confiable', 'fecha_creacion']
    search_fields = ['codigo', 'nombre', 'nit', 'email', 'telefono']
    ordering = ['nombre']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'nit', 'direccion', 'ciudad')
        }),
        ('Contacto', {
            'fields': ('telefono', 'email', 'contacto_principal', 'telefono_contacto')
        }),
        ('Calificación', {
            'fields': ('calificacion', 'confiable')
        }),
        ('Términos Comerciales', {
            'fields': ('dias_credito', 'descuento_pronto_pago')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activa', 'fecha_creacion']
    list_filter = ['activa']
    search_fields = ['nombre']

@admin.register(Subcategoria)
class SubcategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'activa', 'fecha_creacion']
    list_filter = ['activa', 'categoria']
    search_fields = ['nombre', 'categoria__nombre']

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'categoria', 'subcategoria', 'costo_promedio', 'precio_minorista', 'activo']
    list_filter = ['activo', 'categoria', 'subcategoria', 'maneja_variantes']
    search_fields = ['codigo', 'nombre']
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion', 'categoria', 'subcategoria', 'imagen')
        }),
        ('Precios', {
            'fields': ('costo_promedio', 'precio_minorista', 'precio_mayorista')
        }),
        ('Inventario', {
            'fields': ('stock_minimo', 'maneja_variantes')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )

@admin.register(ProductoProveedor)
class ProductoProveedorAdmin(admin.ModelAdmin):
    list_display = ['producto', 'proveedor', 'precio_compra', 'cantidad_minima_pedido', 'tiempo_entrega_dias', 'proveedor_preferido', 'disponible']
    list_filter = ['proveedor_preferido', 'disponible', 'proveedor', 'producto__categoria']
    search_fields = ['producto__codigo', 'producto__nombre', 'proveedor__nombre']
    ordering = ['producto__codigo', 'proveedor__nombre']
    
    fieldsets = (
        ('Relación Básica', {
            'fields': ('producto', 'proveedor')
        }),
        ('Precios', {
            'fields': ('precio_compra', 'precio_compra_anterior')
        }),
        ('Términos Comerciales', {
            'fields': ('cantidad_minima_pedido', 'tiempo_entrega_dias', 'descuento_volumen', 'cantidad_descuento')
        }),
        ('Estado', {
            'fields': ('disponible', 'proveedor_preferido', 'activo')
        }),
        ('Información Adicional', {
            'fields': ('notas',)
        }),
    )
    
    readonly_fields = ['fecha_ultimo_precio']

@admin.register(PresentacionProducto)
class PresentacionProductoAdmin(admin.ModelAdmin):
    list_display = ['producto', 'nombre', 'unidades_por_presentacion', 'precio_minorista_presentacion', 'es_presentacion_principal', 'activa', 'orden']
    list_filter = ['es_presentacion_principal', 'activa', 'producto__categoria']
    search_fields = ['producto__codigo', 'producto__nombre', 'nombre']
    ordering = ['producto__codigo', 'orden', 'nombre']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('producto', 'nombre', 'descripcion', 'unidades_por_presentacion')
        }),
        ('Precios', {
            'fields': ('costo_presentacion', 'precio_minorista_presentacion', 'precio_mayorista_presentacion')
        }),
        ('Control', {
            'fields': ('es_presentacion_principal', 'activa', 'orden')
        }),
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']
    
    def get_readonly_fields(self, request, obj=None):
        # Mostrar campos calculados en el admin
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj:  # Si está editando un objeto existente
            readonly_fields.extend(['fecha_creacion', 'fecha_modificacion'])
        return readonly_fields

@admin.register(PresentacionProveedorProducto)
class PresentacionProveedorProductoAdmin(admin.ModelAdmin):
    list_display = ['producto_proveedor', 'presentacion_base', 'precio_compra_presentacion', 'es_presentacion_preferida', 'disponible']
    list_filter = ['es_presentacion_preferida', 'disponible', 'producto_proveedor__proveedor', 'presentacion_base__nombre']
    search_fields = ['producto_proveedor__producto__codigo', 'producto_proveedor__producto__nombre', 'producto_proveedor__proveedor__nombre', 'codigo_proveedor']
    ordering = ['producto_proveedor__producto__codigo', 'producto_proveedor__proveedor__nombre', 'es_presentacion_preferida']
    
    fieldsets = (
        ('Relación Básica', {
            'fields': ('producto_proveedor', 'presentacion_base', 'codigo_proveedor')
        }),
        ('Precios', {
            'fields': ('precio_compra_presentacion', 'precio_compra_anterior')
        }),
        ('Términos Comerciales', {
            'fields': ('cantidad_minima_pedido', 'tiempo_entrega_dias', 'descuento_volumen', 'cantidad_descuento')
        }),
        ('Estado', {
            'fields': ('disponible', 'es_presentacion_preferida')
        }),
        ('Notas', {
            'fields': ('notas',)
        }),
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_modificacion', 'fecha_ultimo_precio']

@admin.register(VarianteProducto)
class VarianteProductoAdmin(admin.ModelAdmin):
    list_display = ['codigo_variante', 'producto', 'tipo_variante', 'valor', 'activa']
    list_filter = ['tipo_variante', 'activa']
    search_fields = ['codigo_variante', 'producto__codigo', 'producto__nombre', 'valor']

@admin.register(Bodega)
class BodegaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activa', 'es_principal', 'fecha_creacion']
    list_filter = ['activa', 'es_principal']
    search_fields = ['nombre']

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['producto', 'variante', 'bodega', 'cantidad', 'cantidad_reservada', 'cantidad_disponible']
    list_filter = ['bodega']
    search_fields = ['producto__codigo', 'producto__nombre']
    readonly_fields = ['cantidad_disponible']

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ['fecha_movimiento', 'tipo_movimiento', 'producto', 'cantidad', 'bodega', 'usuario']
    list_filter = ['tipo_movimiento', 'motivo', 'bodega', 'fecha_movimiento']
    search_fields = ['producto__codigo', 'producto__nombre', 'documento_referencia']
    readonly_fields = ['id', 'fecha_movimiento']
    date_hierarchy = 'fecha_movimiento'
