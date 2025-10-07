#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
sys.path.append('.')
django.setup()

from django.urls import reverse, NoReverseMatch

# Lista de URLs críticas que aparecen en producto_list.html
urls_criticas = [
    'inventario:exportar_productos_excel',
    'inventario:producto_create',
    'inventario:categoria_list',
    'inventario:subcategoria_list',
    'inventario:bodega_list',
    'inventario:stock_list',
    'inventario:movimiento_list',
    'inventario:transferencia_create',
    'inventario:producto_list',
    'inventario:alertas_stock',  # Del dashboard
]

print("🔍 VERIFICACIÓN COMPLETA DE URLs CRÍTICAS")
print("=" * 50)

urls_exitosas = 0
urls_fallidas = 0

for url_name in urls_criticas:
    try:
        url_path = reverse(url_name)
        print(f"✅ {url_name} → {url_path}")
        urls_exitosas += 1
    except NoReverseMatch as e:
        print(f"❌ {url_name} → ERROR: {e}")
        urls_fallidas += 1
    except Exception as e:
        print(f"⚠️  {url_name} → ERROR INESPERADO: {e}")
        urls_fallidas += 1

print("\n" + "=" * 50)
print(f"📊 RESUMEN:")
print(f"   URLs exitosas: {urls_exitosas}")
print(f"   URLs fallidas: {urls_fallidas}")
print(f"   Total verificadas: {len(urls_criticas)}")

if urls_fallidas == 0:
    print("\n🎉 ¡TODAS LAS URLs CRÍTICAS ESTÁN FUNCIONANDO CORRECTAMENTE!")
    print("   El sistema debería funcionar sin errores NoReverseMatch.")
else:
    print(f"\n⚠️  Se encontraron {urls_fallidas} URLs con problemas.")
    print("   Es necesario revisar y corregir estas URLs.")