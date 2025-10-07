#!/usr/bin/env python
"""
Verificar que todas las URLs en el dashboard funcionan correctamente
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

def verificar_urls_dashboard():
    """Verifica todas las URLs usadas en el dashboard"""
    print("🔗 VERIFICANDO URLs DEL DASHBOARD")
    print("=" * 50)
    
    from django.urls import reverse
    
    # URLs encontradas en el dashboard
    urls_dashboard = [
        'inventario:categoria_list',
        'inventario:categoria_create',
        'inventario:subcategoria_list', 
        'inventario:subcategoria_create',
        'inventario:producto_list',
        'inventario:producto_create',
        'accounts:user_list',
        'accounts:user_create',
        'accounts:login',
        'inventario:exportar_productos_excel',
        'analytics:dashboard',
        'ventas:pedido_list',
        'inventario:alertas_stock',
        'ventas:pedido_create',
        'ventas:cliente_create'
    ]
    
    errores = []
    exitosas = []
    
    for url_name in urls_dashboard:
        try:
            url = reverse(url_name)
            print(f"   ✅ {url_name}: {url}")
            exitosas.append(url_name)
        except Exception as e:
            print(f"   ❌ {url_name}: {e}")
            errores.append((url_name, str(e)))
    
    print(f"\n📊 RESUMEN:")
    print(f"   ✅ URLs funcionando: {len(exitosas)}")
    print(f"   ❌ URLs con errores: {len(errores)}")
    
    if errores:
        print(f"\n🚨 ERRORES ENCONTRADOS:")
        for url_name, error in errores:
            print(f"   • {url_name}: {error}")
        return False
    else:
        print(f"\n🎉 ¡TODAS LAS URLs DEL DASHBOARD FUNCIONAN CORRECTAMENTE!")
        return True

if __name__ == "__main__":
    success = verificar_urls_dashboard()
    if success:
        print(f"\n✅ El dashboard ahora debería cargar sin errores NoReverseMatch")
    else:
        print(f"\n⚠️  Aún hay URLs que necesitan corrección")