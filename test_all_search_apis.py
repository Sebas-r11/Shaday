#!/usr/bin/env python
"""
Script completo para probar TODAS las APIs de búsqueda del sistema
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

# Importar todas las APIs de búsqueda
from ventas.general_views import buscar_productos_api as ventas_productos_api
from ventas.clientes_views import buscar_clientes_api as ventas_clientes_api
from inventario.productos_views import buscar_productos_api as inventario_productos_api
from inventario.api_views import buscar_productos_api as inventario_api_productos_api
from api.views import api_buscar_productos, api_buscar_clientes

def test_all_search_apis():
    print("=== PROBANDO TODAS LAS APIs DE BÚSQUEDA ===\n")
    
    factory = RequestFactory()
    User = get_user_model()
    user = User.objects.first()
    
    if not user:
        print("❌ No hay usuarios en la base de datos")
        return
    
    # APIs a probar
    apis_to_test = [
        {
            'name': 'Ventas - Productos (general_views)',
            'function': ventas_productos_api,
            'url': '/ventas/api/productos/',
            'test_terms': ['iPhone', 'Test', 'PROD']
        },
        {
            'name': 'Ventas - Clientes (clientes_views)',
            'function': ventas_clientes_api,
            'url': '/ventas/api/clientes/',
            'test_terms': ['Test', 'Cliente', 'Demo']
        },
        {
            'name': 'Inventario - Productos (productos_views)',
            'function': inventario_productos_api,
            'url': '/inventario/api/productos/',
            'test_terms': ['iPhone', 'Test']
        },
        {
            'name': 'Inventario - Productos (api_views)',
            'function': inventario_api_productos_api,
            'url': '/inventario/api/productos/buscar/',
            'test_terms': ['iPhone', 'Test']
        },
        {
            'name': 'API General - Productos',
            'function': api_buscar_productos,
            'url': '/api/productos/buscar/',
            'test_terms': ['iPhone', 'Test']
        },
        {
            'name': 'API General - Clientes',
            'function': api_buscar_clientes,
            'url': '/api/clientes/buscar/',
            'test_terms': ['Test', 'Cliente']
        }
    ]
    
    for api_config in apis_to_test:
        print(f"🔍 PROBANDO: {api_config['name']}")
        print(f"   URL: {api_config['url']}")
        
        for term in api_config['test_terms']:
            try:
                request = factory.get(api_config['url'], {'q': term})
                request.user = user
                response = api_config['function'](request)
                
                if response.status_code == 200:
                    try:
                        data = json.loads(response.content.decode())
                        
                        # Diferentes formatos de respuesta
                        if 'productos' in data:
                            count = len(data.get('productos', []))
                        elif 'clientes' in data:
                            count = len(data.get('clientes', []))
                        elif 'results' in data:
                            count = len(data.get('results', []))
                        elif isinstance(data, list):
                            count = len(data)
                        else:
                            count = "?"
                            
                        print(f"   ✅ '{term}' → {count} resultados")
                        
                    except json.JSONDecodeError as e:
                        print(f"   ❌ '{term}' → Error JSON: {e}")
                        
                else:
                    print(f"   ❌ '{term}' → Status {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ '{term}' → Error: {e}")
        
        print()

if __name__ == '__main__':
    test_all_search_apis()