#!/usr/bin/env python
"""
Verificar qué vista está siendo utilizada por la URL /compras/gestion/
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from django.test import Client
from django.urls import reverse

def verificar_dashboard_compras():
    """Verificar la respuesta del dashboard de compras"""
    
    print("🔍 VERIFICANDO DASHBOARD DE COMPRAS")
    print("=" * 50)
    
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    client = Client()
    
    # Crear usuario temporal para testing
    try:
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(
                username='testuser', 
                email='test@test.com', 
                password='testpass123'
            )
    except Exception as e:
        print(f"❌ Error creando usuario: {e}")
        return
    
    # Autenticar usuario
    client.force_login(user)
    
    # Verificar la URL directa
    try:
        response = client.get('/compras/gestion/')
        print(f"✅ URL '/compras/gestion/' - Status: {response.status_code}")
        
        if response.status_code == 200:
            # Verificar si contiene Tailwind
            content = response.content.decode('utf-8')
            tiene_tailwind = 'tailwindcss' in content
            tiene_bootstrap = 'bootstrap' in content
            tiene_gradiente = 'linear-gradient' in content
            
            print(f"📄 Análisis del contenido:")
            print(f"   - Tailwind CSS: {'✅ SÍ' if tiene_tailwind else '❌ NO'}")
            print(f"   - Bootstrap: {'❌ SÍ' if tiene_bootstrap else '✅ NO'}")
            print(f"   - Gradiente púrpura: {'❌ SÍ' if tiene_gradiente else '✅ NO'}")
            
            # Buscar texto característico del nuevo diseño
            titulo_unificado = 'Dashboard de Compras' in content and 'text-3xl font-bold' in content
            header_unificado = 'bg-gray-50' in content
            print(f"   - Título unificado: {'✅ SÍ' if titulo_unificado else '❌ NO'}")
            print(f"   - Header unificado: {'✅ SÍ' if header_unificado else '❌ NO'}")
            
            if tiene_tailwind and not tiene_bootstrap and not tiene_gradiente and titulo_unificado:
                print(f"\n🎉 ¡DASHBOARD COMPLETAMENTE UNIFICADO!")
            else:
                print(f"\n⚠️  Dashboard necesita correcciones")
                
            # Mostrar fragmento del HTML para debug
            print(f"\n📝 Fragmento del HTML (líneas 10-25):")
            lines = content.split('\n')[10:25]
            for i, line in enumerate(lines, 11):
                print(f"   {i:2d}: {line.strip()}")
                
        else:
            print(f"❌ Status inesperado: {response.status_code}")
            print(f"Response: {response.content.decode('utf-8')[:200]}...")
            
    except Exception as e:
        print(f"❌ Error al acceder a /compras/gestion/: {e}")
    
    # Verificar con reverse
    try:
        url = reverse('compras:gestion_dashboard')
        print(f"\n🔗 URL reverse 'compras:gestion_dashboard': {url}")
        response = client.get(url)
        print(f"✅ Status con reverse: {response.status_code}")
    except Exception as e:
        print(f"❌ Error con reverse: {e}")

if __name__ == '__main__':
    verificar_dashboard_compras()