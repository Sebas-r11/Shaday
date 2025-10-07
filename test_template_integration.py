#!/usr/bin/env python3
"""
Prueba del dashboard de gestión de compras con template integrado
Verifica que la página ahora use base.html y tenga la navbar unificada
"""

import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

def test_compras_dashboard_template():
    """Prueba que el dashboard de compras use el template base.html"""
    
    print("🧪 Probando dashboard de gestión de compras con template...")
    
    # Crear cliente de prueba
    client = Client()
    
    # Obtener un usuario (asumiendo que existe al menos uno)
    User = get_user_model()
    try:
        user = User.objects.first()
        if not user:
            print("❌ No se encontraron usuarios en la base de datos")
            return False
            
        # Hacer login del usuario
        client.force_login(user)
        print(f"✅ Login exitoso como: {user.username}")
        
        # Realizar petición GET al dashboard
        response = client.get('/compras/gestion/')
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Verificar elementos clave del template base
            checks = [
                ('navbar unificado', 'class="sidebar"' in content or 'sidebar' in content),
                ('template base', '<!DOCTYPE html>' in content),
                ('título correcto', 'Gestión de Compras' in content),
                ('breadcrumbs', 'breadcrumb' in content),
                ('módulos de gestión', 'Módulos de Gestión' in content),
                ('navegación rápida', 'Navegación Rápida' in content),
                ('sin HTML directo', 'HttpResponse' not in content)
            ]
            
            print("\n🔍 Verificando elementos del template:")
            all_passed = True
            for check_name, result in checks:
                status = "✅" if result else "❌"
                print(f"  {status} {check_name}")
                if not result:
                    all_passed = False
            
            if all_passed:
                print("\n🎉 ¡Éxito! El dashboard ahora usa el template unificado")
                print("📝 La página debería tener la misma navbar que otras páginas del sistema")
                return True
            else:
                print("\n⚠️  Algunos elementos no se encontraron en el template")
                return False
                
        else:
            print(f"❌ Error en la respuesta: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error durante la prueba: {str(e)}")
        return False

def compare_with_other_pages():
    """Compara el dashboard de compras con otras páginas del sistema"""
    
    print("\n🔄 Comparando con otras páginas del sistema...")
    
    client = Client()
    User = get_user_model()
    user = User.objects.first()
    
    if not user:
        print("❌ No se puede hacer la comparación sin usuarios")
        return
        
    client.force_login(user)
    
    # Páginas a comparar
    pages = {
        'Dashboard Principal': '/accounts/dashboard/',
        'Inventario Productos': '/inventario/productos/',
        'Compras Gestión': '/compras/gestion/'
    }
    
    results = {}
    
    for page_name, url in pages.items():
        try:
            response = client.get(url)
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                has_sidebar = 'sidebar' in content.lower()
                has_navbar = 'navbar' in content.lower() or 'nav' in content.lower()
                results[page_name] = {
                    'status': response.status_code,
                    'has_sidebar': has_sidebar,
                    'has_navbar': has_navbar,
                    'unified': has_sidebar or has_navbar
                }
            else:
                results[page_name] = {
                    'status': response.status_code,
                    'has_sidebar': False,
                    'has_navbar': False,
                    'unified': False
                }
        except Exception as e:
            print(f"❌ Error probando {page_name}: {str(e)}")
            results[page_name] = {'status': 'ERROR', 'unified': False}
    
    print("\n📊 Resultados de comparación:")
    for page_name, result in results.items():
        status = "✅" if result.get('unified', False) else "❌"
        print(f"  {status} {page_name}: Status {result.get('status', 'N/A')}")
        if result.get('has_sidebar') or result.get('has_navbar'):
            print(f"      - Tiene navegación unificada")
        else:
            print(f"      - Sin navegación unificada")

if __name__ == "__main__":
    print("=" * 60)
    print("PRUEBA DE INTEGRACIÓN - DASHBOARD COMPRAS")
    print("=" * 60)
    
    success = test_compras_dashboard_template()
    compare_with_other_pages()
    
    print("\n" + "=" * 60)
    if success:
        print("🎯 RESULTADO: Template integrado correctamente")
        print("📋 La página /compras/gestion/ ahora debería tener la misma navbar")
        print("   que las demás páginas del sistema como /accounts/dashboard/")
    else:
        print("⚠️  RESULTADO: Revisar la integración del template")
    print("=" * 60)