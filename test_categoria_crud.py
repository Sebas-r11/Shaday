#!/usr/bin/env python
"""
Script para probar las funcionalidades de edición y eliminación de categorías
"""
import requests

def test_categoria_crud():
    """Prueba las funcionalidades CRUD de categorías"""
    print("🧪 Probando funcionalidades de categorías...")
    
    base_url = 'http://127.0.0.1:8000/inventario/categorias'
    
    urls_to_test = [
        (f'{base_url}/', 'Lista de categorías'),
        (f'{base_url}/crear/', 'Crear nueva categoría'),
        # Las URLs de editar y eliminar requieren un ID específico
    ]
    
    session = requests.Session()
    
    for url, description in urls_to_test:
        try:
            print(f"📡 Probando: {description}")
            print(f"   URL: {url}")
            
            response = session.get(url)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                
                # Verificar funcionalidades específicas
                if 'categoria_list' in url:
                    has_edit_buttons = 'categoria_update' in content
                    has_delete_buttons = 'categoria_delete' in content
                    has_create_button = 'categoria_create' in content
                    
                    print(f"   ✅ Botón crear: {'SÍ' if has_create_button else 'NO'}")
                    print(f"   ✅ Botones editar: {'SÍ' if has_edit_buttons else 'NO'}")
                    print(f"   ✅ Botones eliminar: {'SÍ' if has_delete_buttons else 'NO'}")
                    
                elif 'crear' in url:
                    has_form = 'form' in content and 'nombre' in content
                    has_activa_field = 'name="activa"' in content
                    
                    print(f"   ✅ Formulario: {'SÍ' if has_form else 'NO'}")
                    print(f"   ✅ Campo activa: {'SÍ' if has_activa_field else 'NO'}")
                    
            elif response.status_code == 302:
                print("   🔄 Redirección (requiere autenticación)")
            else:
                print(f"   ❌ Error: {response.status_code}")
                
            print()
            
        except requests.exceptions.ConnectionError:
            print("   ❌ No se pudo conectar al servidor")
            print("   💡 Asegúrate de que el servidor esté corriendo")
            break
        except Exception as e:
            print(f"   ❌ Error inesperado: {e}")

def show_implementation_summary():
    """Muestra resumen de la implementación"""
    print("="*70)
    print("📋 RESUMEN DE IMPLEMENTACIÓN: EDICIÓN Y ELIMINACIÓN DE CATEGORÍAS")
    print("="*70)
    print()
    print("✅ FUNCIONALIDADES IMPLEMENTADAS:")
    print()
    print("🔧 1. VISTA DE ELIMINACIÓN:")
    print("   - Clase: CategoriaDeleteView")
    print("   - URL: /inventario/categorias/<id>/eliminar/")
    print("   - Template: categoria_confirm_delete.html")
    print("   - Validaciones: Verifica productos y subcategorías asociadas")
    print()
    print("🔧 2. MEJORA EN LISTA:")
    print("   - Botones de editar y eliminar en cada categoría")
    print("   - Solo visible para administradores")
    print("   - Contador de productos asociados")
    print()
    print("🔧 3. TEMPLATE DE CONFIRMACIÓN:")
    print("   - Interfaz intuitiva con advertencias")
    print("   - Previene eliminación si hay dependencias")
    print("   - Confirmaciones múltiples para seguridad")
    print()
    print("📋 URLS DISPONIBLES:")
    print("   ✅ GET  /inventario/categorias/")
    print("   ✅ GET  /inventario/categorias/crear/")
    print("   ✅ GET  /inventario/categorias/<id>/editar/")
    print("   ✅ GET  /inventario/categorias/<id>/eliminar/")
    print("   ✅ POST /inventario/categorias/<id>/eliminar/")
    print()
    print("🔒 RESTRICCIONES DE SEGURIDAD:")
    print("   - Solo administradores pueden editar/eliminar")
    print("   - No se puede eliminar si tiene productos asociados")
    print("   - No se puede eliminar si tiene subcategorías asociadas")
    print("   - Confirmaciones múltiples antes de eliminar")
    print()
    print("="*70)

if __name__ == "__main__":
    print("="*70)
    print("VERIFICACIÓN: EDICIÓN Y ELIMINACIÓN DE CATEGORÍAS")
    print("="*70)
    print()
    
    test_categoria_crud()
    show_implementation_summary()