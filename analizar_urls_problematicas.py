#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
sys.path.append('.')
django.setup()

def categorizar_urls_problematicas():
    """
    Categoriza las URLs problemáticas encontradas por tipo de error
    """
    
    # URLs que necesitan argumentos (ID/PK)
    urls_necesitan_argumentos = [
        'accounts:change_user_password',
        'accounts:toggle_user_status', 
        'accounts:user_detail',
        'accounts:user_update',
        'analytics:detalle_reporte',
        'compras:cambiar_estado_orden',
        'compras:orden_cancel',
        'compras:orden_detail',
        'compras:orden_print',
        'compras:orden_update',
        'compras:proveedor_detail',
        'compras:recepcion_detail',
        'crm:oportunidad_detail',
        'crm:oportunidad_update',
        'inventario:bodega_detail',
        'inventario:bodega_update',
        'inventario:detalle_devolucion',
        'inventario:orden_compra_pdf',
        'inventario:orden_compra_stock_detail',
        'inventario:producto_detail',
        'inventario:producto_update',
        'inventario:recomendacion_detail',
        'inventario:stock_detail',
        'inventario:subcategoria_delete',
        'inventario:subcategoria_update',
        'inventario:transferencia_pdf',
        'ventas:convertir_a_factura',
        'ventas:convertir_a_pedido',
        'ventas:cotizacion_detail',
        'ventas:entrega_detail',
        'ventas:cliente_detail',
        'ventas:cliente_update',
        'ventas:factura_detail',
        'ventas:imprimir_cotizacion',
        'ventas:imprimir_factura',
        'ventas:marcar_factura_pagada',
        'ventas:pedido_detail',
    ]
    
    # URLs con nombres incorrectos (guiones en lugar de underscores)
    urls_nombres_incorrectos = [
        'accounts:user-create',      # Debería ser user_create
        'accounts:user-detail',      # Debería ser user_detail  
        'accounts:user-update',      # Debería ser user_update
        'compras:orden-compra-create',   # Nombre incorrecto
        'compras:orden-compra-detail',   # Nombre incorrecto
        'compras:proveedor-list',    # Nombre incorrecto
        'compras:proveedor-update',  # Nombre incorrecto
        'inventario:stock-list',     # Debería ser stock_list
        'ventas:entrega-detail',     # Debería ser entrega_detail
        'ventas:entregas-repartidor', # Debería ser entregas_repartidor
        'ventas:factura-list',       # Debería ser factura_list
    ]
    
    # URLs que no existen (faltan implementar)
    urls_no_existen = [
        'inventario:bodega_delete',
        'inventario:producto_proveedores', 
        'inventario:imprimir_devolucion',
        'ventas:anular_factura',
        'ventas:asignar_pedido_bodega',
        'ventas:cambiar_estado_pedido',
        'ventas:completar_pedido_inmediato',
        'ventas:enviar_cotizacion',
        'ventas:generar_pdf_cotizacion',
        'ventas:imprimir_pedido',
        'ventas:reporte_ventas',
        'ventas:reprogramar_entrega',
    ]
    
    return {
        'necesitan_argumentos': urls_necesitan_argumentos,
        'nombres_incorrectos': urls_nombres_incorrectos,
        'no_existen': urls_no_existen
    }

def generar_reporte_categorizado():
    """
    Genera un reporte categorizado de los problemas encontrados
    """
    categorias = categorizar_urls_problematicas()
    
    print("🔍 ANÁLISIS DETALLADO DE URLs PROBLEMÁTICAS")
    print("=" * 60)
    
    print(f"\n📊 RESUMEN POR CATEGORÍAS:")
    print(f"   URLs que necesitan argumentos: {len(categorias['necesitan_argumentos'])}")
    print(f"   URLs con nombres incorrectos: {len(categorias['nombres_incorrectos'])}")
    print(f"   URLs que no existen: {len(categorias['no_existen'])}")
    print(f"   TOTAL PROBLEMÁTICAS: {sum(len(cat) for cat in categorias.values())}")
    
    print(f"\n1️⃣ URLs QUE NECESITAN ARGUMENTOS (ID/PK)")
    print("-" * 50)
    print("📝 SOLUCIÓN: Estas URLs necesitan un parámetro ID/PK para funcionar.")
    print("   En los templates, asegúrate de pasar el ID: {% url 'app:vista' objeto.pk %}")
    print()
    for url in sorted(categorias['necesitan_argumentos']):
        print(f"   • {url}")
    
    print(f"\n2️⃣ URLs CON NOMBRES INCORRECTOS")
    print("-" * 50)
    print("📝 SOLUCIÓN: Cambiar nombres en templates para usar underscores (_) en lugar de guiones (-).")
    print()
    nombre_correcciones = {
        'accounts:user-create': 'accounts:user_create',
        'accounts:user-detail': 'accounts:user_detail',
        'accounts:user-update': 'accounts:user_update',
        'inventario:stock-list': 'inventario:stock_list',
        'ventas:entrega-detail': 'ventas:entrega_detail',
        'ventas:entregas-repartidor': 'ventas:entregas_repartidor',
        'ventas:factura-list': 'ventas:factura_list',
    }
    
    for url_incorrecta in sorted(categorias['nombres_incorrectos']):
        correccion = nombre_correcciones.get(url_incorrecta, "⚠️  REVISAR MANUALMENTE")
        print(f"   • {url_incorrecta:<35} → {correccion}")
    
    print(f"\n3️⃣ URLs QUE NO EXISTEN (FALTAN IMPLEMENTAR)")
    print("-" * 50)
    print("📝 SOLUCIÓN: Estas vistas/URLs necesitan ser creadas en los archivos urls.py correspondientes.")
    print()
    for url in sorted(categorias['no_existen']):
        print(f"   • {url}")
    
    print(f"\n🚨 IMPACTO EN PRODUCCIÓN:")
    print("─" * 30)
    print("• Estas URLs problemáticas pueden causar errores NoReverseMatch")
    print("• Los errores impiden que las páginas se carguen correctamente")
    print("• Algunos enlaces en la interfaz pueden estar rotos")
    print("• Es importante corregir las URLs más críticas primero")
    
    print(f"\n⚡ RECOMENDACIONES DE PRIORIDAD:")
    print("─" * 35)
    print("1. ALTA: Corregir nombres incorrectos (cambios simples en templates)")
    print("2. MEDIA: Implementar URLs faltantes para funcionalidades críticas")
    print("3. BAJA: Revisar URLs que necesitan argumentos (pueden estar bien)")
    
    return categorias

if __name__ == "__main__":
    categorias = generar_reporte_categorizado()
    
    # Guardar reporte detallado
    with open('reporte_urls_categorizado.txt', 'w', encoding='utf-8') as f:
        f.write("REPORTE CATEGORIZADO - URLs PROBLEMÁTICAS\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Fecha: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("1. URLs QUE NECESITAN ARGUMENTOS:\n")
        f.write("-" * 35 + "\n")
        for url in sorted(categorias['necesitan_argumentos']):
            f.write(f"• {url}\n")
        
        f.write("\n2. URLs CON NOMBRES INCORRECTOS:\n")
        f.write("-" * 35 + "\n")
        for url in sorted(categorias['nombres_incorrectos']):
            f.write(f"• {url}\n")
        
        f.write("\n3. URLs QUE NO EXISTEN:\n")
        f.write("-" * 25 + "\n")
        for url in sorted(categorias['no_existen']):
            f.write(f"• {url}\n")
    
    print(f"\n📄 Reporte detallado guardado en: reporte_urls_categorizado.txt")