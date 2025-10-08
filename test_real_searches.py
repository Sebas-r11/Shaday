#!/usr/bin/env python
"""
Script para probar búsquedas reales con datos que existen
"""
import os
import sys
import django
import json

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from ventas.general_views import buscar_productos_api
from ventas.clientes_views import buscar_clientes_api

def test_real_searches():
    print("=== PROBANDO BÚSQUEDAS REALES ===\n")
    
    factory = RequestFactory()
    User = get_user_model()
    user = User.objects.first()
    
    # Búsquedas de productos
    search_terms_products = ['iPhone', 'Test', 'PROD', '000', 'jabon']
    print("🔍 PROBANDO BÚSQUEDAS DE PRODUCTOS:")
    
    for term in search_terms_products:
        try:
            request = factory.get('/ventas/api/productos/', {'q': term})
            request.user = user
            response = buscar_productos_api(request)
            
            if response.status_code == 200:
                data = json.loads(response.content.decode())
                productos_count = len(data.get('productos', []))
                print(f"  ✅ '{term}' → {productos_count} productos encontrados")
                
                if productos_count > 0:
                    # Mostrar el primer producto encontrado
                    primer_producto = data['productos'][0]
                    print(f"      Ejemplo: {primer_producto['codigo']} - {primer_producto['nombre']}")
            else:
                print(f"  ❌ '{term}' → Error {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ '{term}' → Error: {e}")
    
    print()
    
    # Búsquedas de clientes
    search_terms_clients = ['Test', 'Cliente', 'Demo', '123', '900']
    print("🔍 PROBANDO BÚSQUEDAS DE CLIENTES:")
    
    for term in search_terms_clients:
        try:
            request = factory.get('/ventas/api/clientes/', {'q': term})
            request.user = user
            response = buscar_clientes_api(request)
            
            if response.status_code == 200:
                data = json.loads(response.content.decode())
                clientes_count = len(data.get('clientes', []))
                print(f"  ✅ '{term}' → {clientes_count} clientes encontrados")
                
                if clientes_count > 0:
                    # Mostrar el primer cliente encontrado
                    primer_cliente = data['clientes'][0]
                    print(f"      Ejemplo: {primer_cliente['numero_documento']} - {primer_cliente['nombre_completo']}")
            else:
                print(f"  ❌ '{term}' → Error {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ '{term}' → Error: {e}")

if __name__ == '__main__':
    test_real_searches()