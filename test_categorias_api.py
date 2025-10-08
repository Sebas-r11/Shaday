#!/usr/bin/env python
"""
Prueba adicional para la API de búsqueda de categorías
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
from inventario.categorias_views import buscar_categorias_api

def test_categorias_api():
    print("=== PROBANDO API DE BÚSQUEDA DE CATEGORÍAS ===\n")
    
    factory = RequestFactory()
    User = get_user_model()
    user = User.objects.first()
    
    # Términos de búsqueda para categorías
    search_terms = ['elect', 'prod', 'test', 'cat']
    
    for term in search_terms:
        try:
            request = factory.get('/inventario/api/categorias/', {'q': term})
            request.user = user
            response = buscar_categorias_api(request)
            
            if response.status_code == 200:
                data = json.loads(response.content.decode())
                count = len(data) if isinstance(data, list) else "?"
                print(f"✅ '{term}' → {count} categorías encontradas")
                
                if isinstance(data, list) and len(data) > 0:
                    print(f"   Ejemplo: {data[0]['label']}")
            else:
                print(f"❌ '{term}' → Status {response.status_code}")
                
        except Exception as e:
            print(f"❌ '{term}' → Error: {e}")

if __name__ == '__main__':
    test_categorias_api()