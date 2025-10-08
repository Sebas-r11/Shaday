#!/usr/bin/env python
"""
Script para probar las APIs de búsqueda de productos y clientes
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from ventas.general_views import buscar_productos_api
from ventas.clientes_views import buscar_clientes_api

def test_search_apis():
    print("=== PROBANDO APIs DE BÚSQUEDA ===\n")
    
    # Crear un factory para requests
    factory = RequestFactory()
    
    # Obtener un usuario para las pruebas
    User = get_user_model()
    try:
        user = User.objects.first()
        if not user:
            print("❌ No hay usuarios en la base de datos")
            return
    except Exception as e:
        print(f"❌ Error obteniendo usuario: {e}")
        return
    
    # Probar API de productos
    print("🔍 Probando API de productos...")
    try:
        request = factory.get('/ventas/api/productos/', {'q': 'cuad'})
        request.user = user
        response = buscar_productos_api(request)
        
        if response.status_code == 200:
            print(f"✅ API de productos funciona - Status: {response.status_code}")
            print(f"   Contenido: {response.content.decode()[:200]}...")
        else:
            print(f"❌ API de productos falló - Status: {response.status_code}")
            print(f"   Contenido: {response.content.decode()}")
            
    except Exception as e:
        print(f"❌ Error en API de productos: {e}")
    
    print()
    
    # Probar API de clientes
    print("🔍 Probando API de clientes...")
    try:
        request = factory.get('/ventas/api/clientes/', {'q': 'test'})
        request.user = user
        response = buscar_clientes_api(request)
        
        if response.status_code == 200:
            print(f"✅ API de clientes funciona - Status: {response.status_code}")
            print(f"   Contenido: {response.content.decode()[:200]}...")
        else:
            print(f"❌ API de clientes falló - Status: {response.status_code}")
            print(f"   Contenido: {response.content.decode()}")
            
    except Exception as e:
        print(f"❌ Error en API de clientes: {e}")

if __name__ == '__main__':
    test_search_apis()