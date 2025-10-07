#!/usr/bin/env python
"""
Script simple para probar la corrección del formulario de categorías
"""
import requests
import re

def test_categoria_form():
    """Prueba que el formulario de categorías tiene el campo activa"""
    print("🧪 Probando formulario de creación de categorías...")
    
    try:
        # Hacer login primero (simulado)
        session = requests.Session()
        
        # Obtener página de creación de categoría
        url = 'http://127.0.0.1:8000/inventario/categorias/crear/'
        response = session.get(url)
        
        print(f"📄 Status de respuesta: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            
            # Buscar elementos del formulario
            has_nombre = 'name="nombre"' in content
            has_descripcion = 'name="descripcion"' in content  
            has_activa = 'name="activa"' in content and 'type="checkbox"' in content
            has_label_activa = 'Categoría activa' in content
            
            print(f"📝 Campo nombre: {'✅' if has_nombre else '❌'}")
            print(f"📝 Campo descripción: {'✅' if has_descripcion else '❌'}")
            print(f"🔲 Campo activa (checkbox): {'✅' if has_activa else '❌'}")
            print(f"🏷️  Label 'Categoría activa': {'✅' if has_label_activa else '❌'}")
            
            # Verificar que tiene la estructura correcta
            if has_nombre and has_descripcion and has_activa and has_label_activa:
                print("\n🎉 ¡CORRECCIÓN EXITOSA!")
                print("✅ El formulario ahora incluye el campo 'activa'")
                print("✅ El usuario puede marcar/desmarcar si la categoría está activa")
                return True
            else:
                print("\n❌ PROBLEMA ENCONTRADO")
                print("❌ El formulario no tiene todos los campos esperados")
                return False
                
        elif response.status_code == 302:
            print("🔄 Redirección detectada (probablemente por autenticación)")
            print("💡 Sugerencia: Accede manualmente a la URL para verificar")
            return "redirect"
        else:
            print(f"❌ Error al acceder a la página: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar al servidor")
        print("💡 Asegúrate de que el servidor esté corriendo en el puerto 8000")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def show_manual_verification():
    """Muestra instrucciones para verificación manual"""
    print("\n" + "="*60)
    print("📋 VERIFICACIÓN MANUAL RECOMENDADA")
    print("="*60)
    print("1. Abrir navegador en: http://127.0.0.1:8000/inventario/categorias/crear/")
    print("2. Hacer login como admin")
    print("3. Verificar que el formulario tiene:")
    print("   ✅ Campo 'Nombre de la Categoría'")
    print("   ✅ Campo 'Descripción'")
    print("   ✅ Checkbox 'Categoría activa' (NUEVO)")
    print("4. Crear una categoría con el checkbox marcado")
    print("5. Verificar que aparece como activa en la lista")
    print("="*60)

if __name__ == "__main__":
    print("="*60)
    print("VERIFICACIÓN DE CORRECCIÓN: CAMPO ACTIVA EN CATEGORÍAS")
    print("="*60)
    
    result = test_categoria_form()
    
    if result == True:
        print("\n🎯 CORRECCIÓN VERIFICADA EXITOSAMENTE")
    elif result == "redirect":
        print("\n🔄 VERIFICACIÓN REQUIERE LOGIN MANUAL")
        show_manual_verification()
    else:
        print("\n❌ VERIFICACIÓN FALLIDA")
        show_manual_verification()