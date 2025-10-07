#!/usr/bin/env python
"""
Script para validar que todos los templates referenciados en las vistas existan
"""
import os
import re
import glob
from pathlib import Path

# Lista de templates encontrados en las vistas
templates_referenciados = [
    # Ventas
    'ventas/cliente_list.html',
    'ventas/cliente_form.html', 
    'ventas/cliente_detail.html',
    'ventas/cotizacion_list.html',
    'ventas/cotizacion_form.html',
    'ventas/cotizacion_detail.html',
    'ventas/cotizacion_print.html',
    'ventas/pedido_list.html',
    'ventas/pedido_form.html',
    'ventas/pedido_detail.html',
    'ventas/pedido_print.html',
    'ventas/factura_list.html',
    'ventas/factura_form.html',
    'ventas/factura_detail.html',
    'ventas/factura_print.html',
    'ventas/factura_reporte.html',
    'ventas/dashboard.html',
    'ventas/pedidos_alistamiento.html',
    'ventas/entregas_repartidor.html',
    'ventas/entrega_detail.html',
    'ventas/entrega_form.html',
    'ventas/error_stock_insuficiente.html',
    'ventas/reporte_items_rechazados.html',
    'ventas/reprogramar_entrega.html',
    'ventas/ruta_optimizada.html',
    'ventas/optimizar_ruta.html',
    'ventas/reporte_ventas.html',
    'ventas/completar_entrega.html',
    'ventas/reporte_entregas.html',
    'ventas/test_autocompletado.html',
    'ventas/test_ajax.html',
    
    # Compras
    'compras/proveedor_list.html',
    'compras/proveedor_form.html',
    'compras/proveedor_detail.html',
    'compras/orden_compra_list.html',
    'compras/orden_compra_form.html',
    'compras/orden_compra_detail_fixed.html',
    'compras/orden_compra_cancel.html',
    'compras/orden_compra_print.html',
    'compras/recepcion_form.html',
    'compras/recepcion_detail.html',
    'compras/solicitud_list.html',
    'compras/solicitud_form.html',
    'compras/solicitud_detail.html',
    'compras/dashboard.html',
    'compras/reporte_compras.html',
    'compras/home.html',
    'compras/ayuda.html',
    
    # Inventario
    'inventario/producto_list.html',
    'inventario/producto_form.html',
    'inventario/producto_detail.html',
    'inventario/categoria_list.html',
    'inventario/categoria_form.html',
    'inventario/subcategoria_list.html',
    'inventario/subcategoria_form.html',
    'inventario/subcategoria_confirm_delete.html',
    'inventario/bodega_list.html',
    'inventario/bodega_form.html',
    'inventario/bodega_detail.html',
    'inventario/bodega_confirm_delete.html',
    'inventario/stock_list.html',
    'inventario/stock_detail.html',
    'inventario/movimiento_list.html',
    'inventario/producto_detail_proveedores.html',
    'inventario/producto_proveedores_form.html',
    'inventario/transferencia_form.html',
    'inventario/ajuste_form.html',
    'inventario/ajuste_masivo_form.html',
    'inventario/reporte_integracion.html',
    'inventario/consolidar_categorias.html',
    'inventario/ayuda.html',
    
    # Accounts
    'accounts/change_password.html',
    'accounts/user_management_dashboard.html',
    'accounts/repartidor_gps.html',
    'accounts/dashboard_repartidores.html',
    
    # Analytics
    'analytics/dashboard.html',
    'analytics/prediccion_demanda.html',
    'analytics/analisis_clientes.html',
    'analytics/sistema_mrp.html',
    'analytics/reportes.html',
    'analytics/detalle_reporte.html',
    'analytics/estadisticas_masivas.html',
    
    # CRM
    'crm/dashboard.html',
    'crm/reporte_pipeline.html',
    
    # Test
    'test_autocompletado.html',
]

def verificar_templates():
    """Verifica la existencia de todos los templates"""
    print("🔍 VALIDACIÓN DE TEMPLATES")
    print("=" * 50)
    
    # Buscar directorio templates
    base_dir = Path(__file__).parent
    templates_dirs = [
        base_dir / 'templates',
        base_dir / 'static' / 'templates',
    ]
    
    # También buscar templates en cada app
    for app_dir in ['ventas', 'compras', 'inventario', 'accounts', 'analytics', 'crm']:
        app_path = base_dir / app_dir
        if app_path.exists():
            templates_dirs.append(app_path / 'templates')
    
    print(f"📁 Directorios de templates encontrados:")
    existing_dirs = []
    for dir_path in templates_dirs:
        if dir_path.exists():
            existing_dirs.append(dir_path)
            print(f"   ✅ {dir_path}")
        else:
            print(f"   ❌ {dir_path} (no existe)")
    
    print(f"\n📋 Verificando {len(templates_referenciados)} templates...")
    
    encontrados = 0
    faltantes = []
    
    for template in templates_referenciados:
        encontrado = False
        
        # Buscar en todos los directorios de templates
        for templates_dir in existing_dirs:
            template_path = templates_dir / template
            if template_path.exists():
                print(f"   ✅ {template}")
                encontrado = True
                encontrados += 1
                break
        
        if not encontrado:
            print(f"   ❌ {template}")
            faltantes.append(template)
    
    print(f"\n📊 RESUMEN:")
    print(f"   ✅ Templates encontrados: {encontrados}")
    print(f"   ❌ Templates faltantes: {len(faltantes)}")
    print(f"   📈 Porcentaje de éxito: {(encontrados/len(templates_referenciados)*100):.1f}%")
    
    if faltantes:
        print(f"\n🚨 TEMPLATES FALTANTES:")
        for template in faltantes:
            print(f"   - {template}")
    
    return len(faltantes) == 0

if __name__ == "__main__":
    exito = verificar_templates()
    if exito:
        print("\n🎉 ¡Todos los templates están presentes!")
    else:
        print("\n⚠️  Algunos templates faltan y deben ser creados.")