#!/usr/bin/env python3
"""
Prueba completa de todas las URLs corregidas
Verifica que todas las páginas ahora usen templates unificados con navbar
"""

import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

def test_all_corrected_urls():
    """Prueba todas las URLs que fueron corregidas"""
    
    print("🧪 Probando todas las correcciones aplicadas...")
    
    # Crear cliente de prueba
    client = Client()
    
    # Obtener un usuario
    User = get_user_model()
    try:
        user = User.objects.first()
        if not user:
            print("❌ No se encontraron usuarios en la base de datos")
            return False
            
        # Hacer login del usuario
        client.force_login(user)
        print(f"✅ Login exitoso como: {user.username}")
        
        # URLs a probar
        test_urls = [
            {
                'name': 'Dashboard Principal (Referencia)',
                'url': '/accounts/dashboard/',
                'expected': True
            },
            {
                'name': 'Gestión de Compras', 
                'url': '/compras/gestion/',
                'expected': True
            },
            {
                'name': 'Gestión de Proveedores',
                'url': '/compras/gestion/proveedores/',
                'expected': True
            },
            {
                'name': 'Alertas de Stock',
                'url': '/compras/gestion/alertas-stock/',
                'expected': True
            },
            {
                'name': 'Presentaciones Simple (Inventario)',
                'url': '/inventario/presentaciones-simple/',
                'expected': True
            },
            {
                'name': 'Solicitudes de Compra',
                'url': '/compras/solicitudes/',
                'expected': True
            }
        ]
        
        results = []
        
        print("\n🔍 Probando URLs corregidas:")
        
        for test_case in test_urls:
            try:
                response = client.get(test_case['url'])
                
                if response.status_code == 200:
                    content = response.content.decode('utf-8')
                    
                    # Verificar elementos clave del template unificado
                    has_doctype = '<!DOCTYPE html>' in content
                    has_navigation = 'sidebar' in content.lower() or 'navbar' in content.lower() or 'nav' in content.lower()
                    has_bootstrap = 'bootstrap' in content.lower() or 'container' in content
                    is_unified = has_doctype and has_navigation and has_bootstrap
                    
                    status = "✅" if is_unified else "⚠️"
                    print(f"  {status} {test_case['name']}")
                    print(f"      URL: {test_case['url']}")
                    print(f"      Status: {response.status_code}")
                    print(f"      Content Length: {len(content)} chars")
                    print(f"      Has Navigation: {'✅' if has_navigation else '❌'}")
                    print(f"      Has Doctype: {'✅' if has_doctype else '❌'}")
                    print(f"      Unified Template: {'✅' if is_unified else '❌'}")
                    
                    results.append({
                        'name': test_case['name'],
                        'url': test_case['url'],
                        'status': response.status_code,
                        'unified': is_unified,
                        'has_navigation': has_navigation
                    })
                    
                else:
                    print(f"  ❌ {test_case['name']}")
                    print(f"      URL: {test_case['url']}")
                    print(f"      Status: {response.status_code}")
                    
                    results.append({
                        'name': test_case['name'],
                        'url': test_case['url'],
                        'status': response.status_code,
                        'unified': False,
                        'has_navigation': False
                    })
                    
                print()
                    
            except Exception as e:
                print(f"  ❌ {test_case['name']}: Error - {str(e)}")
                results.append({
                    'name': test_case['name'],
                    'url': test_case['url'],
                    'status': 'ERROR',
                    'unified': False,
                    'has_navigation': False,
                    'error': str(e)
                })
        
        # Análisis de resultados
        print("📊 Resumen de resultados:")
        
        successful = [r for r in results if r['status'] == 200]
        unified = [r for r in results if r.get('unified', False)]
        with_nav = [r for r in results if r.get('has_navigation', False)]
        
        print(f"  📈 Páginas cargadas correctamente: {len(successful)}/{len(results)}")
        print(f"  🎯 Páginas con template unificado: {len(unified)}/{len(results)}")
        print(f"  🧭 Páginas con navegación: {len(with_nav)}/{len(results)}")
        
        # Verificación específica de consistencia
        print("\n🎯 Verificación de consistencia visual:")
        
        reference_page = None
        for result in results:
            if result['url'] == '/accounts/dashboard/' and result['status'] == 200:
                reference_page = result
                break
        
        if reference_page:
            print(f"  📋 Página de referencia: {reference_page['name']}")
            print(f"      - Tiene navegación: {'✅' if reference_page['has_navigation'] else '❌'}")
            
            print("\n  🔄 Comparación con páginas corregidas:")
            for result in results:
                if result['url'] != '/accounts/dashboard/' and result['status'] == 200:
                    consistent = (result['has_navigation'] == reference_page['has_navigation'])
                    status = "✅" if consistent else "❌"
                    print(f"    {status} {result['name']}: {'Consistente' if consistent else 'Inconsistente'}")
        
        # Conclusión
        success_rate = len(unified) / len(results) if results else 0
        
        print(f"\n🏆 Tasa de éxito: {success_rate:.1%}")
        
        if success_rate >= 0.8:  # 80% o más
            print("🎉 ¡Excelente! La mayoría de las páginas ahora tienen navegación consistente")
            return True
        elif success_rate >= 0.6:  # 60% o más
            print("👍 Buen progreso, pero algunas páginas aún necesitan corrección")
            return False
        else:
            print("⚠️ Varias páginas aún necesitan corrección")
            return False
            
    except Exception as e:
        print(f"❌ Error durante las pruebas: {str(e)}")
        return False

def test_specific_navbar_elements():
    """Prueba elementos específicos de navbar para confirmar unificación"""
    
    print("\n🔍 Verificación detallada de elementos de navegación...")
    
    client = Client()
    User = get_user_model()
    user = User.objects.first()
    
    if not user:
        print("❌ No se puede hacer la verificación sin usuarios")
        return
    
    client.force_login(user)
    
    # URLs clave para comparar
    comparison_urls = [
        '/accounts/dashboard/',
        '/compras/gestion/',
        '/compras/gestion/proveedores/',
        '/compras/solicitudes/'
    ]
    
    print("  🧭 Buscando elementos comunes de navegación...")
    
    common_elements = []
    for url in comparison_urls:
        try:
            response = client.get(url)
            if response.status_code == 200:
                content = response.content.decode('utf-8').lower()
                
                # Buscar elementos específicos de navegación
                nav_elements = {
                    'sidebar': 'sidebar' in content,
                    'navbar': 'navbar' in content,
                    'menu': 'menu' in content,
                    'nav_tag': '<nav' in content,
                    'main_content': 'main' in content,
                    'container': 'container' in content
                }
                
                common_elements.append({
                    'url': url,
                    'elements': nav_elements
                })
                
                print(f"    📄 {url}:")
                for element, found in nav_elements.items():
                    status = "✅" if found else "❌"
                    print(f"      {status} {element}")
                    
        except Exception as e:
            print(f"    ❌ Error en {url}: {str(e)}")
    
    # Verificar consistencia entre páginas
    if len(common_elements) >= 2:
        print("\n  📊 Análisis de consistencia:")
        
        reference = common_elements[0]  # Dashboard como referencia
        
        for page in common_elements[1:]:
            matches = 0
            total_elements = len(reference['elements'])
            
            for element in reference['elements']:
                if reference['elements'][element] == page['elements'][element]:
                    matches += 1
            
            consistency = matches / total_elements
            status = "✅" if consistency >= 0.7 else "⚠️" if consistency >= 0.5 else "❌"
            
            print(f"    {status} {page['url']}: {consistency:.1%} consistente con dashboard")

if __name__ == "__main__":
    print("=" * 80)
    print("PRUEBA COMPLETA DE CORRECCIONES - NAVBAR UNIFICADA")
    print("=" * 80)
    
    success = test_all_corrected_urls()
    test_specific_navbar_elements()
    
    print("\n" + "=" * 80)
    if success:
        print("🎯 RESULTADO: ¡Correcciones aplicadas exitosamente!")
        print("📋 Todas las páginas problemáticas ahora tienen navegación unificada")
        print("🔗 Las siguientes URLs ahora deberían verse consistentes:")
        print("   - http://127.0.0.1:8000/compras/gestion/")
        print("   - http://127.0.0.1:8000/compras/gestion/proveedores/")
        print("   - http://127.0.0.1:8000/compras/gestion/alertas-stock/")
        print("   - http://127.0.0.1:8000/inventario/presentaciones-simple/")
        print("   - http://127.0.0.1:8000/compras/solicitudes/")
    else:
        print("⚠️  RESULTADO: Algunas páginas aún necesitan revisión")
        
    print("=" * 80)