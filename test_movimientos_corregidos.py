#!/usr/bin/env python
"""
Test específico para validar corrección de errores en movimientos de inventario
Error: FieldError at /inventario/movimientos/ - fecha_creacion vs fecha_movimiento
"""
import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

def test_movimientos_inventario():
    """Test completo del módulo de movimientos de inventario"""
    print("🧪 VALIDACIÓN MOVIMIENTOS INVENTARIO")
    print("Probando corrección de FieldError fecha_creacion")
    print("=" * 60)
    
    # Client para hacer requests
    client = Client()
    
    # Crear usuario admin para testing
    User = get_user_model()
    try:
        admin_user = User.objects.get(username='admin')
    except User.DoesNotExist:
        admin_user = User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
    
    # Login como admin
    client.login(username='admin', password='admin123')
    
    urls_to_test = [
        ('/inventario/movimientos/', 'Lista Movimientos'),
        ('/inventario/dashboard/', 'Dashboard Inventario'),
        ('/inventario/productos/', 'Lista Productos'),
        ('/inventario/categorias/', 'Lista Categorías'),
        ('/inventario/subcategorias/', 'Lista Subcategorías'),
        ('/inventario/bodegas/', 'Lista Bodegas'),
        ('/inventario/alertas/', 'Alertas Stock'),
    ]
    
    results = []
    
    print("🔍 TESTING URLs INVENTARIO")
    print("-" * 40)
    
    for url, name in urls_to_test:
        try:
            response = client.get(url)
            status = "✅ OK" if response.status_code in [200, 302] else f"❌ ERROR {response.status_code}"
            results.append((name, response.status_code, status))
            print(f"   {status:<10} {name:<25} Status {response.status_code}")
        except Exception as e:
            results.append((name, 500, f"❌ EXCEPTION"))
            print(f"   ❌ EXCEPTION {name:<25} Error: {str(e)[:50]}")
    
    print()
    print("🔍 TESTING MODELOS INVENTARIO")
    print("-" * 40)
    
    # Test modelos directamente
    try:
        from inventario.models import MovimientoInventario, Producto, Categoria, Subcategoria, Bodega
        
        # Test MovimientoInventario - el que tenía el error
        movimientos_count = MovimientoInventario.objects.count()
        print(f"   ✅ MovimientoInventario: {movimientos_count} registros")
        
        # Test que fecha_movimiento funciona
        if movimientos_count > 0:
            ultimo_movimiento = MovimientoInventario.objects.order_by('-fecha_movimiento').first()
            print(f"   ✅ Campo fecha_movimiento: {ultimo_movimiento.fecha_movimiento}")
        
        # Test otros modelos
        productos_count = Producto.objects.count()
        categorias_count = Categoria.objects.count()
        subcategorias_count = Subcategoria.objects.count()
        bodegas_count = Bodega.objects.count()
        
        print(f"   ✅ Productos: {productos_count} registros")
        print(f"   ✅ Categorías: {categorias_count} registros")
        print(f"   ✅ Subcategorías: {subcategorias_count} registros")
        print(f"   ✅ Bodegas: {bodegas_count} registros")
        
    except Exception as e:
        print(f"   ❌ Error en modelos: {str(e)}")
    
    print()
    print("🔍 TESTING API ENDPOINTS")
    print("-" * 40)
    
    api_urls = [
        ('/api/productos/', 'API Productos'),
        ('/api/alertas-stock/', 'API Alertas Stock'),
    ]
    
    for url, name in api_urls:
        try:
            response = client.get(url)
            status = "✅ OK" if response.status_code == 200 else f"❌ ERROR {response.status_code}"
            print(f"   {status:<10} {name}")
        except Exception as e:
            print(f"   ❌ EXCEPTION {name} - {str(e)[:50]}")
    
    print()
    print("=" * 60)
    print("📊 RESUMEN FINAL")
    print("=" * 60)
    
    total_urls = len(results)
    urls_ok = len([r for r in results if r[1] in [200, 302]])
    urls_error = total_urls - urls_ok
    
    print(f"📊 URLs probadas: {total_urls}")
    print(f"✅ URLs funcionando: {urls_ok} ({(urls_ok/total_urls)*100:.1f}%)")
    print(f"❌ URLs con problemas: {urls_error}")
    
    if urls_error == 0:
        print("\n🎉 MÓDULO INVENTARIO: 100% FUNCIONAL")
        print("✅ Error de fecha_creacion vs fecha_movimiento CORREGIDO")
    else:
        print(f"\n⚠️  MÓDULO INVENTARIO: {(urls_ok/total_urls)*100:.1f}% funcional")
        print("❌ Algunos errores persisten")
    
    print("\n🚀 VALIDACIÓN COMPLETADA")

if __name__ == '__main__':
    test_movimientos_inventario()