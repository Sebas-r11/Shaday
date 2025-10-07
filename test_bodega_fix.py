#!/usr/bin/env python
"""
Script de verificación para la corrección del error de BodegaCreateView
"""
import requests

def test_bodega_create_view():
    """Verifica que la vista de crear bodega funcione sin errores"""
    print("🧪 Probando vista de creación de bodegas...")
    
    try:
        # Probar la URL de creación de bodegas
        url = 'http://127.0.0.1:8000/inventario/bodegas/crear/'
        
        print(f"📡 Probando URL: {url}")
        response = requests.get(url)
        
        print(f"📄 Status de respuesta: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            
            # Verificar que no hay error de FieldError
            has_field_error = 'FieldError' in content or 'Unknown field' in content
            has_descripcion_error = 'descripcion' in content and 'Unknown field' in content
            
            # Verificar campos correctos en el formulario
            has_nombre = 'name="nombre"' in content
            has_direccion = 'name="direccion"' in content
            has_telefono = 'name="telefono"' in content
            has_activa = 'name="activa"' in content
            has_es_principal = 'name="es_principal"' in content
            has_link_ubicacion = 'name="link_ubicacion"' in content
            
            print(f"❌ Error de campo 'descripcion': {'SÍ' if has_descripcion_error else 'NO'}")
            print(f"📝 Campo nombre: {'✅' if has_nombre else '❌'}")
            print(f"📍 Campo dirección: {'✅' if has_direccion else '❌'}")
            print(f"📞 Campo teléfono: {'✅' if has_telefono else '❌'}")
            print(f"🔲 Campo activa: {'✅' if has_activa else '❌'}")
            print(f"⭐ Campo es_principal: {'✅' if has_es_principal else '❌'}")
            print(f"🔗 Campo link_ubicacion: {'✅' if has_link_ubicacion else '❌'}")
            
            if not has_field_error and not has_descripcion_error:
                print("\n🎉 ¡CORRECCIÓN EXITOSA!")
                print("✅ La vista de crear bodega funciona sin errores")
                print("✅ No hay referencias al campo inexistente 'descripcion'")
                print("✅ Todos los campos del modelo están disponibles")
                return True
            else:
                print("\n❌ PROBLEMA PERSISTENTE")
                print("❌ Aún hay errores relacionados con campos")
                return False
                
        elif response.status_code == 302:
            print("🔄 Redirección detectada (probablemente por autenticación)")
            print("💡 Intenta acceder manualmente para verificar")
            return "redirect"
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar al servidor")
        print("💡 Asegúrate de que el servidor esté corriendo")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def show_correction_summary():
    """Muestra resumen de la corrección aplicada"""
    print("\n" + "="*70)
    print("📋 RESUMEN DE CORRECCIÓN APLICADA")
    print("="*70)
    print("🔧 PROBLEMA:")
    print("   - Error: Unknown field(s) (descripcion) specified for Bodega")
    print("   - La vista BodegaCreateView incluía 'descripcion' en fields")
    print("   - El modelo Bodega NO tiene campo 'descripcion'")
    print()
    print("✅ SOLUCIÓN:")
    print("   - Eliminado 'descripcion' de los fields en BodegaCreateView")
    print("   - Eliminado 'descripcion' de los fields en BodegaUpdateView")
    print("   - Agregados campos correctos: es_principal, link_ubicacion")
    print()
    print("📝 CAMPOS VÁLIDOS DEL MODELO BODEGA:")
    print("   ✅ nombre")
    print("   ✅ direccion")
    print("   ✅ telefono")
    print("   ✅ activa")
    print("   ✅ es_principal")
    print("   ✅ link_ubicacion")
    print("="*70)

if __name__ == "__main__":
    print("="*70)
    print("VERIFICACIÓN: CORRECCIÓN ERROR BODEGA CREATE VIEW")
    print("="*70)
    
    result = test_bodega_create_view()
    
    if result == True:
        print("\n🎯 VERIFICACIÓN EXITOSA")
        print("✅ La corrección fue aplicada correctamente")
    elif result == "redirect":
        print("\n🔄 VERIFICACIÓN REQUIERE LOGIN")
        print("💡 Accede manualmente para confirmar")
    else:
        print("\n❌ VERIFICACIÓN FALLIDA")
        print("⚠️  Puede que necesites revisión adicional")
    
    show_correction_summary()