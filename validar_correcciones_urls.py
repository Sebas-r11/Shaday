#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
sys.path.append('.')
django.setup()

from django.urls import reverse, NoReverseMatch

def validar_correcciones():
    """
    Valida las URLs que fueron corregidas para verificar que ahora funcionan
    """
    
    print("🔧 VALIDACIÓN DE CORRECCIONES APLICADAS")
    print("=" * 50)
    
    # URLs que fueron corregidas (nombres incorrectos)
    urls_corregidas = [
        'accounts:user_create',
        'accounts:user_detail',
        'accounts:user_update',
        'ventas:factura_list',
        'ventas:entregas_repartidor',
        'ventas:entrega_detail',
        'inventario:stock_list',
        'compras:proveedor_list',
        'compras:proveedor_update',
        'compras:orden_create',
        'compras:orden_detail',
    ]
    
    # URLs que fueron implementadas (faltantes)
    urls_implementadas = [
        'ventas:cambiar_estado_pedido',
        'ventas:completar_pedido_inmediato',
        'ventas:asignar_pedido_bodega',
        'ventas:reprogramar_entrega',
        'ventas:generar_pdf_cotizacion',
        'ventas:enviar_cotizacion',
        'ventas:anular_factura',
        'ventas:reporte_ventas',
        'ventas:imprimir_pedido',
        'inventario:bodega_delete',
        'inventario:producto_proveedores',
        'inventario:imprimir_devolucion',
    ]
    
    # URLs que necesitan argumentos (verificar si están bien)
    urls_con_argumentos = [
        ('accounts:user_detail', [1]),
        ('accounts:user_update', [1]),
        ('ventas:pedido_detail', [1]),
        ('ventas:factura_detail', [1]),
        ('ventas:cliente_detail', [1]),
        ('inventario:producto_detail', [1]),
        ('inventario:bodega_detail', [1]),
        ('compras:orden_detail', ['550e8400-e29b-41d4-a716-446655440000']),  # UUID de ejemplo
    ]
    
    print("\n1️⃣ VALIDANDO URLs CORREGIDAS (Nombres incorrectos):")
    print("-" * 50)
    exitosas_corregidas = 0
    for url_name in urls_corregidas:
        try:
            url_path = reverse(url_name)
            print(f"✅ {url_name:<35} → {url_path}")
            exitosas_corregidas += 1
        except NoReverseMatch as e:
            print(f"❌ {url_name:<35} → ERROR: {str(e)[:60]}...")
        except Exception as e:
            print(f"⚠️  {url_name:<35} → ERROR: {str(e)[:60]}...")
    
    print(f"\n✅ URLs corregidas exitosas: {exitosas_corregidas}/{len(urls_corregidas)}")
    
    print("\n2️⃣ VALIDANDO URLs IMPLEMENTADAS (Faltantes):")
    print("-" * 50)
    exitosas_implementadas = 0
    for url_name in urls_implementadas:
        try:
            # Para URLs que necesitan argumentos, usar valores de prueba
            if url_name in ['ventas:cambiar_estado_pedido', 'ventas:completar_pedido_inmediato', 
                          'ventas:asignar_pedido_bodega', 'ventas:reprogramar_entrega',
                          'ventas:generar_pdf_cotizacion', 'ventas:enviar_cotizacion',
                          'ventas:anular_factura', 'ventas:imprimir_pedido']:
                url_path = reverse(url_name, args=[1])
            elif url_name in ['inventario:bodega_delete', 'inventario:producto_proveedores', 
                            'inventario:imprimir_devolucion']:
                url_path = reverse(url_name, args=[1])
            else:
                url_path = reverse(url_name)
            
            print(f"✅ {url_name:<35} → {url_path}")
            exitosas_implementadas += 1
        except NoReverseMatch as e:
            print(f"❌ {url_name:<35} → ERROR: {str(e)[:60]}...")
        except Exception as e:
            print(f"⚠️  {url_name:<35} → ERROR: {str(e)[:60]}...")
    
    print(f"\n✅ URLs implementadas exitosas: {exitosas_implementadas}/{len(urls_implementadas)}")
    
    print("\n3️⃣ VALIDANDO URLs CON ARGUMENTOS (Verificación):")
    print("-" * 50)
    exitosas_argumentos = 0
    for url_name, args in urls_con_argumentos:
        try:
            url_path = reverse(url_name, args=args)
            print(f"✅ {url_name:<35} → {url_path}")
            exitosas_argumentos += 1
        except NoReverseMatch as e:
            print(f"❌ {url_name:<35} → ERROR: {str(e)[:60]}...")
        except Exception as e:
            print(f"⚠️  {url_name:<35} → ERROR: {str(e)[:60]}...")
    
    print(f"\n✅ URLs con argumentos exitosas: {exitosas_argumentos}/{len(urls_con_argumentos)}")
    
    # Resumen general
    total_corregidas = exitosas_corregidas + exitosas_implementadas + exitosas_argumentos
    total_verificadas = len(urls_corregidas) + len(urls_implementadas) + len(urls_con_argumentos)
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN GENERAL DE CORRECCIONES:")
    print(f"   URLs corregidas: {exitosas_corregidas}/{len(urls_corregidas)}")
    print(f"   URLs implementadas: {exitosas_implementadas}/{len(urls_implementadas)}")
    print(f"   URLs con argumentos: {exitosas_argumentos}/{len(urls_con_argumentos)}")
    print(f"   TOTAL EXITOSO: {total_corregidas}/{total_verificadas}")
    
    porcentaje_exito = (total_corregidas / total_verificadas) * 100 if total_verificadas > 0 else 0
    
    if porcentaje_exito >= 90:
        print(f"\n🎉 ¡EXCELENTE! {porcentaje_exito:.1f}% de las correcciones funcionan correctamente.")
        print("   El sistema debería tener muchos menos errores NoReverseMatch ahora.")
    elif porcentaje_exito >= 70:
        print(f"\n✅ BUENO: {porcentaje_exito:.1f}% de las correcciones funcionan.")
        print("   La mayoría de problemas han sido resueltos.")
    else:
        print(f"\n⚠️  NECESITA MEJORAS: Solo {porcentaje_exito:.1f}% de las correcciones funcionan.")
        print("   Aún hay problemas que requieren atención adicional.")
    
    return {
        'corregidas': exitosas_corregidas,
        'implementadas': exitosas_implementadas,
        'argumentos': exitosas_argumentos,
        'total': total_corregidas,
        'porcentaje': porcentaje_exito
    }

if __name__ == "__main__":
    resultados = validar_correcciones()
    
    print(f"\n📄 Correcciones completadas:")
    print(f"   - Nombres incorrectos corregidos: {resultados['corregidas']}")
    print(f"   - URLs faltantes implementadas: {resultados['implementadas']}")
    print(f"   - URLs con argumentos verificadas: {resultados['argumentos']}")
    print(f"   - Porcentaje de éxito: {resultados['porcentaje']:.1f}%")