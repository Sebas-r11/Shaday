#!/usr/bin/env python
"""
Test para verificar la corrección de categorías activas
"""
import os
import sys
import django
from django.test import Client
from django.contrib.auth.models import User

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

def test_categoria_create_form():
    """Test del formulario de creación de categorías con campo activa"""
    print("🧪 Probando formulario de creación de categorías...")
    
    client = Client()
    
    # Login como admin
    try:
        admin_user = User.objects.get(username='admin')
        client.force_login(admin_user)
        print("✅ Login exitoso como admin")
    except User.DoesNotExist:
        print("❌ Usuario admin no encontrado")
        return False
    
    # Probar página de creación de categoría
    response = client.get('/inventario/categorias/crear/')
    print(f"📄 Status de página crear categoría: {response.status_code}")
    
    if response.status_code == 200:
        content = response.content.decode()
        
        # Verificar que existe el checkbox de activa
        has_checkbox = 'name="activa"' in content and 'type="checkbox"' in content
        has_label = 'Categoría activa' in content
        
        print(f"🔲 Campo checkbox activa presente: {'✅' if has_checkbox else '❌'}")
        print(f"🏷️  Label del campo presente: {'✅' if has_label else '❌'}")
        
        if has_checkbox and has_label:
            print("✅ Formulario tiene el campo activa correctamente")
            return test_create_active_category(client)
        else:
            print("❌ Formulario no tiene el campo activa")
            return False
    else:
        print("❌ No se pudo cargar la página de creación")
        return False

def test_create_active_category(client):
    """Test de creación de categoría activa"""
    print("\n🧪 Probando creación de categoría activa...")
    
    # Datos para crear una categoría activa
    form_data = {
        'nombre': 'Categoría Test Activa',
        'descripcion': 'Categoría de prueba para verificar que se puede crear activa',
        'activa': 'on'  # Checkbox marcado
    }
    
    response = client.post('/inventario/categorias/crear/', form_data)
    print(f"📨 Status POST crear categoría: {response.status_code}")
    
    if response.status_code == 302:  # Redirect después de crear
        print("✅ Categoría creada exitosamente (redirect)")
        
        # Verificar que la categoría se creó activa
        from inventario.models import Categoria
        try:
            categoria = Categoria.objects.get(nombre='Categoría Test Activa')
            print(f"📋 Categoría encontrada: {categoria.nombre}")
            print(f"✅ Estado activa: {'✅ SÍ' if categoria.activa else '❌ NO'}")
            
            # Limpiar datos de prueba
            categoria.delete()
            print("🧹 Datos de prueba eliminados")
            
            return categoria.activa
        except Categoria.DoesNotExist:
            print("❌ Categoría no encontrada en la base de datos")
            return False
    else:
        print("❌ Error al crear categoría")
        if hasattr(response, 'content'):
            content = response.content.decode()
            if 'error' in content.lower():
                print("📝 Posibles errores en el formulario")
        return False

def test_create_inactive_category(client):
    """Test de creación de categoría inactiva"""
    print("\n🧪 Probando creación de categoría inactiva...")
    
    # Datos para crear una categoría inactiva
    form_data = {
        'nombre': 'Categoría Test Inactiva',
        'descripcion': 'Categoría de prueba para verificar que se puede crear inactiva',
        # No enviamos 'activa' para que sea False
    }
    
    response = client.post('/inventario/categorias/crear/', form_data)
    print(f"📨 Status POST crear categoría inactiva: {response.status_code}")
    
    if response.status_code == 302:  # Redirect después de crear
        print("✅ Categoría inactiva creada exitosamente")
        
        # Verificar que la categoría se creó inactiva
        from inventario.models import Categoria
        try:
            categoria = Categoria.objects.get(nombre='Categoría Test Inactiva')
            print(f"📋 Categoría encontrada: {categoria.nombre}")
            print(f"❌ Estado activa: {'✅ SÍ' if categoria.activa else '❌ NO (correcto)'}")
            
            # Limpiar datos de prueba
            categoria.delete()
            print("🧹 Datos de prueba eliminados")
            
            return not categoria.activa  # Retornamos True si está inactiva (correcto)
        except Categoria.DoesNotExist:
            print("❌ Categoría no encontrada en la base de datos")
            return False
    else:
        print("❌ Error al crear categoría inactiva")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("PRUEBA DE CORRECCIÓN: CAMPO ACTIVA EN CATEGORÍAS")
    print("=" * 80)
    
    # Test del formulario
    form_ok = test_categoria_create_form()
    
    if form_ok:
        # Test adicional de creación inactiva
        client = Client()
        admin_user = User.objects.get(username='admin')
        client.force_login(admin_user)
        inactive_ok = test_create_inactive_category(client)
        
        print("\n" + "=" * 80)
        if form_ok and inactive_ok:
            print("🎉 ¡CORRECCIÓN EXITOSA!")
            print("✅ El campo 'activa' funciona correctamente en el formulario")
            print("✅ Se pueden crear categorías activas e inactivas")
            print("✅ La funcionalidad está totalmente reparada")
        else:
            print("⚠️  CORRECCIÓN PARCIAL")
            print("✅ Formulario tiene el campo activa")
            print("❌ Hay problemas con la funcionalidad")
    else:
        print("\n" + "=" * 80)
        print("❌ CORRECCIÓN FALLIDA")
        print("❌ El formulario aún no tiene el campo activa")
    
    print("=" * 80)