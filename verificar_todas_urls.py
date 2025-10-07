#!/usr/bin/env python
import os
import sys
import django
import re
from collections import defaultdict

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
sys.path.append('.')
django.setup()

from django.urls import reverse, NoReverseMatch

def extract_urls_from_grep_output():
    """
    Extrae URLs únicas de la salida de grep que obtuvimos anteriormente.
    """
    # URLs encontradas en el grep anterior (las más comunes)
    urls_encontradas = [
        # From templates
        'ventas:pedido_list',
        'ventas:factura_list',
        'ventas:cliente_list',
        'ventas:cotizacion_list',
        'ventas:entregas_repartidor',
        'ventas:pedido_create',
        'ventas:cotizacion_create',
        'ventas:cliente_create',
        'ventas:pedido_detail',
        'ventas:factura_detail',
        'ventas:cliente_detail',
        'ventas:cotizacion_detail',
        'ventas:entrega_detail',
        'ventas:convertir_a_factura',
        'ventas:imprimir_pedido',
        'ventas:imprimir_factura',
        'ventas:imprimir_cotizacion',
        'ventas:reprogramar_entrega',
        'ventas:cambiar_estado_pedido',
        'ventas:completar_pedido_inmediato',
        'ventas:pedidos_alistamiento',
        'ventas:asignar_pedido_bodega',
        'ventas:convertir_a_pedido',
        'ventas:generar_pdf_cotizacion',
        'ventas:enviar_cotizacion',
        'ventas:marcar_factura_pagada',
        'ventas:anular_factura',
        'ventas:api_clientes',
        'ventas:api_productos',
        'ventas:factura_create',
        'ventas:reporte_facturas',
        'ventas:cliente_update',
        'ventas:dashboard',
        'ventas:factura-list',  # Posible error (guion en lugar de underscore)
        'ventas:entregas-repartidor',  # Posible error
        'ventas:entrega-detail',  # Posible error
        'ventas:reporte_ventas',
        
        # Inventario URLs
        'inventario:categoria_list',
        'inventario:categoria_create',
        'inventario:subcategoria_list',
        'inventario:subcategoria_create',
        'inventario:producto_list',
        'inventario:producto_create',
        'inventario:producto_detail',
        'inventario:producto_update',
        'inventario:producto_proveedores',
        'inventario:bodega_list',
        'inventario:bodega_create',
        'inventario:bodega_detail',
        'inventario:bodega_update',
        'inventario:bodega_delete',
        'inventario:stock_list',
        'inventario:stock_detail',
        'inventario:movimiento_list',
        'inventario:transferencia_create',
        'inventario:transferencia_pdf',
        'inventario:alertas_stock',
        'inventario:exportar_productos_excel',
        'inventario:subcategoria_update',
        'inventario:subcategoria_delete',
        'inventario:orden_compra_stock_list',
        'inventario:generar_orden_compra',
        'inventario:orden_compra_stock_detail',
        'inventario:orden_compra_pdf',
        'inventario:stock_api',
        'inventario:crear_ajuste_inventario',
        'inventario:recomendaciones_list',
        'inventario:dashboard_recomendaciones',
        'inventario:recomendacion_detail',
        'inventario:generar_recomendaciones_ajax',
        'inventario:detalle_devolucion',
        'inventario:lista_devoluciones',
        'inventario:reporte_devoluciones',
        'inventario:imprimir_devolucion',
        'inventario:stock-list',  # Posible error (guion)
        
        # CRM URLs
        'crm:dashboard',
        'crm:oportunidad_list',
        'crm:oportunidad_create',
        'crm:oportunidad_update',
        'crm:oportunidad_detail',
        'crm:actividad_create',
        
        # Analytics URLs
        'analytics:dashboard',
        'analytics:prediccion_demanda',
        'analytics:analisis_clientes',
        'analytics:sistema_mrp',
        'analytics:estadisticas_masivas',
        'analytics:reportes',
        'analytics:detalle_reporte',
        
        # Accounts URLs
        'accounts:dashboard',
        'accounts:user_list',
        'accounts:user_create',
        'accounts:user_detail',
        'accounts:user_update',
        'accounts:login',
        'accounts:logout',
        'accounts:change_user_password',
        'accounts:toggle_user_status',
        'accounts:user-create',  # Posible error (guion)
        'accounts:user-detail',  # Posible error
        'accounts:user-update',  # Posible error
        
        # Compras URLs
        'compras:orden_list',
        'compras:orden_create',
        'compras:orden_detail',
        'compras:orden_update',
        'compras:orden_print',
        'compras:orden_cancel',
        'compras:recepcion_create',
        'compras:recepcion_detail',
        'compras:proveedor_detail',
        'compras:cambiar_estado_orden',
        'compras:proveedor_create',
        'compras:proveedor-list',  # Posible error
        'compras:proveedor-update',  # Posible error
        'compras:orden-compra-create',  # Posible error
        'compras:orden-compra-detail',  # Posible error
    ]
    
    return list(set(urls_encontradas))  # Eliminar duplicados

def validate_urls(urls_list):
    """
    Valida cada URL contra la configuración de Django
    """
    print("🔍 VERIFICACIÓN COMPLETA DE TODAS LAS URLs DEL SISTEMA")
    print("=" * 60)
    
    urls_exitosas = []
    urls_fallidas = []
    
    for url_name in sorted(urls_list):
        try:
            url_path = reverse(url_name)
            print(f"✅ {url_name:<45} → {url_path}")
            urls_exitosas.append(url_name)
        except NoReverseMatch as e:
            print(f"❌ {url_name:<45} → ERROR: {str(e)[:80]}...")
            urls_fallidas.append((url_name, str(e)))
        except Exception as e:
            print(f"⚠️  {url_name:<45} → ERROR INESPERADO: {str(e)[:60]}...")
            urls_fallidas.append((url_name, str(e)))
    
    print("\n" + "=" * 60)
    print(f"📊 RESUMEN GENERAL:")
    print(f"   URLs exitosas: {len(urls_exitosas)}")
    print(f"   URLs fallidas: {len(urls_fallidas)}")
    print(f"   Total verificadas: {len(urls_list)}")
    
    if urls_fallidas:
        print(f"\n❌ URLs PROBLEMÁTICAS ENCONTRADAS:")
        print("-" * 60)
        for url_name, error in urls_fallidas:
            print(f"   • {url_name}")
            print(f"     Error: {error[:80]}...")
            print()
    else:
        print("\n🎉 ¡TODAS LAS URLs ESTÁN FUNCIONANDO CORRECTAMENTE!")
        print("   El sistema debería funcionar sin errores NoReverseMatch.")
    
    return urls_exitosas, urls_fallidas

if __name__ == "__main__":
    urls_encontradas = extract_urls_from_grep_output()
    print(f"Total de URLs únicas encontradas: {len(urls_encontradas)}\n")
    
    urls_exitosas, urls_fallidas = validate_urls(urls_encontradas)
    
    # Crear archivo de reporte
    with open('reporte_urls_completo.txt', 'w', encoding='utf-8') as f:
        f.write("REPORTE COMPLETO DE URLs DEL SISTEMA ERP\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Fecha: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"URLs exitosas: {len(urls_exitosas)}\n")
        f.write(f"URLs fallidas: {len(urls_fallidas)}\n")
        f.write(f"Total verificadas: {len(urls_encontradas)}\n\n")
        
        f.write("URLs EXITOSAS:\n")
        f.write("-" * 20 + "\n")
        for url in urls_exitosas:
            f.write(f"✅ {url}\n")
        
        f.write("\nURLs PROBLEMÁTICAS:\n")
        f.write("-" * 20 + "\n")
        for url_name, error in urls_fallidas:
            f.write(f"❌ {url_name}\n")
            f.write(f"   Error: {error}\n\n")
    
    print(f"\n📄 Reporte guardado en: reporte_urls_completo.txt")