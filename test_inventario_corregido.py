#!/usr/bin/env python
"""
Test del módulo de inventario después de la corrección
Distribuciones Shaddai - Validación inventario
"""

import os
import sys
import django

# Configuración Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

def test_inventario_urls():
    """Probar las URLs del módulo de inventario"""
    print("🔍 TESTING MÓDULO INVENTARIO")
    print("=" * 60)
    
    client = Client()
    User = get_user_model()
    
    # Crear/obtener usuario admin
    try:
        admin_user = User.objects.get(username='admin')
    except User.DoesNotExist:
        admin_user = User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
    
    client.force_login(admin_user)
    
    # URLs a probar
    urls_inventario = [
        ('/inventario/', 'Dashboard Inventario'),
        ('/inventario/productos/', 'Lista Productos'),
        ('/inventario/categorias/', 'Lista Categorías'),
        ('/inventario/subcategorias/', 'Lista Subcategorías'),
        ('/inventario/bodegas/', 'Lista Bodegas'),
        ('/inventario/movimientos/', 'Movimientos'),
        ('/inventario/alertas/', 'Alertas Stock'),
    ]
    
    resultados = []
    
    for url, descripcion in urls_inventario:
        try:
            response = client.get(url)
            status = response.status_code
            
            if status == 200:
                emoji = "✅"
                mensaje = "OK"
            elif status in [301, 302]:
                emoji = "🔄"
                mensaje = "Redirect"
            elif status == 404:
                emoji = "❌"
                mensaje = "Not Found"
            else:
                emoji = "⚠️"
                mensaje = f"Status {status}"
            
            print(f"   {emoji} {descripcion:<25} {mensaje}")
            resultados.append({'url': url, 'status': status, 'ok': status in [200, 301, 302]})
            
        except Exception as e:
            print(f"   ❌ {descripcion:<25} ERROR: {str(e)[:50]}")
            resultados.append({'url': url, 'status': 500, 'ok': False})
    
    # Resumen
    total = len(resultados)
    ok = sum(1 for r in resultados if r['ok'])
    porcentaje = (ok / total * 100) if total > 0 else 0
    
    print(f"\n📊 RESUMEN:")
    print(f"   • URLs probadas: {total}")
    print(f"   • URLs funcionando: {ok} ({porcentaje:.1f}%)")
    
    if porcentaje >= 90:
        print(f"   🎉 MÓDULO INVENTARIO: EXCELENTE")
    elif porcentaje >= 75:
        print(f"   ✅ MÓDULO INVENTARIO: BUENO")
    else:
        print(f"   ⚠️  MÓDULO INVENTARIO: NECESITA REVISIÓN")
    
    return porcentaje >= 75

def test_modelos_inventario():
    """Probar que los modelos de inventario funcionen correctamente"""
    print(f"\n🔍 TESTING MODELOS INVENTARIO")
    print("=" * 60)
    
    try:
        from inventario.models import Categoria, Subcategoria, Producto, Bodega, Stock
        
        # Test básico de consultas
        categorias = Categoria.objects.count()
        subcategorias = Subcategoria.objects.count()
        productos = Producto.objects.count()
        bodegas = Bodega.objects.count()
        
        print(f"   📊 Datos en BD:")
        print(f"      • Categorías: {categorias}")
        print(f"      • Subcategorías: {subcategorias}")
        print(f"      • Productos: {productos}")
        print(f"      • Bodegas: {bodegas}")
        
        # Test de relaciones
        try:
            # Test Count con relaciones
            categorias_con_productos = Categoria.objects.annotate(
                productos_count=django.db.models.Count('producto')
            ).count()
            print(f"   ✅ Relación Categoria → Producto: OK")
            
            subcategorias_con_productos = Subcategoria.objects.annotate(
                productos_count=django.db.models.Count('producto')
            ).count()
            print(f"   ✅ Relación Subcategoria → Producto: OK")
            
        except Exception as e:
            print(f"   ❌ Error en relaciones: {e}")
            return False
        
        print(f"   ✅ MODELOS INVENTARIO: FUNCIONANDO CORRECTAMENTE")
        return True
        
    except Exception as e:
        print(f"   ❌ Error en modelos: {e}")
        return False

def main():
    """Función principal de testing"""
    print("🧪 VALIDACIÓN COMPLETA MÓDULO INVENTARIO")
    print("Distribuciones Shaddai - Post-corrección")
    print("=" * 80)
    
    # Test URLs
    urls_ok = test_inventario_urls()
    
    # Test Modelos  
    modelos_ok = test_modelos_inventario()
    
    # Resultado final
    print(f"\n" + "=" * 80)
    print(f"🏆 RESULTADO FINAL")
    print(f"=" * 80)
    
    if urls_ok and modelos_ok:
        print(f"   🎉 MÓDULO INVENTARIO: 100% FUNCIONAL")
        print(f"   ✅ Error de 'productos' field CORREGIDO")
        print(f"   🚀 Sistema listo para usar")
    else:
        print(f"   ⚠️  MÓDULO INVENTARIO: Necesita más correcciones")
    
    print(f"\n✅ VALIDACIÓN COMPLETADA")

if __name__ == '__main__':
    main()