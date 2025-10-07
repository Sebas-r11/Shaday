#!/usr/bin/env python3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

client = Client()
User = get_user_model()
user = User.objects.first()
client.force_login(user)

print("🧪 Probando página de compras...")
response = client.get('/compras/gestion/')
print(f"Status: {response.status_code}")

if response.status_code == 200:
    content = response.content.decode('utf-8')
    print(f"Content length: {len(content)} chars")
    print(f"Has sidebar: {'sidebar' in content.lower()}")
    print(f"Has nav: {'nav' in content.lower()}")
    print(f"Has base template: {'<!DOCTYPE html>' in content}")
    print(f"Has title: {'Gestión de Compras' in content}")
    
    # Comparar con dashboard principal
    print("\n🔄 Comparando con dashboard principal...")
    response2 = client.get('/accounts/dashboard/')
    print(f"Dashboard status: {response2.status_code}")
    
    if response2.status_code == 200:
        content2 = response2.content.decode('utf-8')
        print(f"Dashboard content length: {len(content2)} chars")
        
        # Verificar elementos comunes
        compras_has_nav = 'sidebar' in content.lower() or 'nav' in content.lower()
        dashboard_has_nav = 'sidebar' in content2.lower() or 'nav' in content2.lower()
        
        print(f"\nCompras tiene navegación: {compras_has_nav}")
        print(f"Dashboard tiene navegación: {dashboard_has_nav}")
        
        if compras_has_nav == dashboard_has_nav:
            print("✅ ¡Éxito! Ambas páginas tienen estructura similar")
        else:
            print("⚠️ Las páginas tienen diferente estructura de navegación")
else:
    print("❌ Error cargando la página de compras")