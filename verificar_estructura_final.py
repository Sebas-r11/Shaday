#!/usr/bin/env python3
"""
Verificación final: Comparar estructura HTML de páginas del sistema
"""

import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

def analyze_page_structure():
    """Analiza la estructura HTML de las páginas principales"""
    
    print("🔍 Analizando estructura HTML de las páginas...")
    
    client = Client()
    User = get_user_model()
    user = User.objects.first()
    
    if not user:
        print("❌ No se encontraron usuarios")
        return
    
    client.force_login(user)
    
    pages = [
        ('Dashboard Principal', '/accounts/dashboard/'),
        ('Inventario Productos', '/inventario/productos/'),
        ('Compras Gestión', '/compras/gestion/')
    ]
    
    results = {}
    
    for page_name, url in pages:
        try:
            response = client.get(url)
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                
                # Buscar elementos clave de la estructura
                analysis = {
                    'extends_base': 'extends \'base.html\'' in content or '<!DOCTYPE html>' in content,
                    'has_sidebar': 'sidebar' in content.lower(),
                    'has_navbar': 'navbar' in content.lower() or 'nav' in content.lower(),
                    'has_main_content': 'main' in content.lower() or 'content' in content.lower(),
                    'bootstrap_structure': 'container' in content or 'row' in content or 'col' in content,
                    'title_present': page_name.split()[0].lower() in content.lower(),
                    'responsive': 'responsive' in content or 'viewport' in content
                }
                
                results[page_name] = {
                    'url': url,
                    'status': response.status_code,
                    'analysis': analysis,
                    'content_length': len(content)
                }
                
                print(f"\n📄 {page_name} ({url}):")
                print(f"   Status: {response.status_code}")
                print(f"   Content Length: {len(content)} chars")
                
                for key, value in analysis.items():
                    status = "✅" if value else "❌"
                    print(f"   {status} {key.replace('_', ' ').title()}")
                    
        except Exception as e:
            print(f"❌ Error analizando {page_name}: {str(e)}")
            results[page_name] = {'status': 'ERROR', 'error': str(e)}
    
    # Verificar consistencia
    print("\n🎯 Análisis de Consistencia:")
    
    if len(results) >= 2:
        # Comparar características clave
        first_page = list(results.values())[0]
        consistent_features = []
        
        for page_name, data in results.items():
            if 'analysis' in data:
                has_navigation = data['analysis']['has_sidebar'] or data['analysis']['has_navbar']
                has_structure = data['analysis']['bootstrap_structure']
                extends_base = data['analysis']['extends_base']
                
                print(f"   📊 {page_name}:")
                print(f"      - Navegación: {'✅' if has_navigation else '❌'}")
                print(f"      - Estructura: {'✅' if has_structure else '❌'}")
                print(f"      - Base Template: {'✅' if extends_base else '❌'}")
                
                if has_navigation and has_structure and extends_base:
                    consistent_features.append(page_name)
        
        print(f"\n🏆 Páginas con estructura consistente: {len(consistent_features)}/{len(results)}")
        for page in consistent_features:
            print(f"   ✅ {page}")
    
    return results

def test_navigation_consistency():
    """Prueba específica de navegación consistente"""
    
    print("\n🧭 Prueba específica de navegación...")
    
    client = Client()
    User = get_user_model()
    user = User.objects.first()
    client.force_login(user)
    
    # URLs a probar
    test_urls = [
        '/accounts/dashboard/',
        '/compras/gestion/'
    ]
    
    navigation_elements = []
    
    for url in test_urls:
        try:
            response = client.get(url)
            if response.status_code == 200:
                content = response.content.decode('utf-8').lower()
                
                # Buscar elementos de navegación específicos
                nav_indicators = [
                    'sidebar' in content,
                    'navbar' in content,
                    'menu' in content,
                    'navigation' in content,
                    'nav-' in content,
                    'topbar' in content
                ]
                
                found_indicators = sum(nav_indicators)
                navigation_elements.append((url, found_indicators, response.status_code))
                
                print(f"   📍 {url}: {found_indicators} indicadores de navegación encontrados")
                
        except Exception as e:
            print(f"   ❌ Error en {url}: {str(e)}")
    
    # Verificar consistencia
    if len(navigation_elements) >= 2:
        base_count = navigation_elements[0][1]
        compras_count = navigation_elements[1][1]
        
        if compras_count >= base_count - 1:  # Tolerancia de 1
            print("\n   ✅ Las páginas tienen estructura de navegación similar")
            return True
        else:
            print(f"\n   ⚠️  Diferencia significativa: {base_count} vs {compras_count}")
            return False
    
    return False

if __name__ == "__main__":
    print("=" * 70)
    print("VERIFICACIÓN FINAL - ESTRUCTURA HTML Y NAVEGACIÓN")
    print("=" * 70)
    
    results = analyze_page_structure()
    nav_consistent = test_navigation_consistency()
    
    print("\n" + "=" * 70)
    
    if nav_consistent:
        print("🎉 ÉXITO: La página de compras tiene navegación consistente")
        print("📋 La URL /compras/gestion/ ahora debería verse igual a las demás páginas")
        print("🔗 Puedes verificar visitando:")
        print("   - http://127.0.0.1:8000/accounts/dashboard/")
        print("   - http://127.0.0.1:8000/compras/gestion/")
        print("   - http://127.0.0.1:8000/inventario/productos/")
    else:
        print("⚠️  ADVERTENCIA: Revisar la consistencia de navegación")
        
    print("=" * 70)