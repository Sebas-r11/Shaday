#!/usr/bin/env python
"""
Script para probar el formulario de subcategorías y verificar el dropdown
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from inventario.models import Categoria, Subcategoria
from django.template import Context, Template
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from inventario.categorias_views import SubcategoriaCreateView

User = get_user_model()

def simular_formulario_subcategoria():
    print("🧪 SIMULANDO FORMULARIO DE SUBCATEGORÍAS")
    print("=" * 50)
    
    # Crear usuario de prueba
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        print("❌ No hay usuario administrador")
        return False
    
    # Simular request
    factory = RequestFactory()
    request = factory.get('/inventario/subcategorias/crear/')
    request.user = user
    
    # Instanciar vista
    view = SubcategoriaCreateView()
    view.request = request
    
    try:
        # Obtener contexto
        context = view.get_context_data()
        
        print(f"📋 CONTEXTO DEL FORMULARIO:")
        print(f"   - form: {context.get('form')}")
        print(f"   - categorias en contexto: {context.get('categorias')}")
        
        # Verificar categorias
        categorias = context.get('categorias')
        if categorias:
            print(f"\n✅ CATEGORÍAS DISPONIBLES ({categorias.count()}):")
            for categoria in categorias:
                print(f"   • ID: {categoria.id} | {categoria.nombre} | Activa: {categoria.activa}")
        else:
            print("\n❌ NO HAY CATEGORÍAS EN EL CONTEXTO")
            
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def verificar_formulario_html():
    print("\n🔍 VERIFICANDO TEMPLATE DE FORMULARIO")
    print("=" * 50)
    
    # Leer template
    try:
        with open('templates/inventario/subcategoria_form.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Buscar la parte del dropdown
        if '{% for categoria in categorias %}' in content:
            print("✅ El template está configurado para iterar sobre 'categorias'")
        else:
            print("❌ El template NO está configurado correctamente")
            
        if 'value="{{ categoria.pk }}"' in content:
            print("✅ El template usa categoria.pk como value")
        else:
            print("❌ El template NO usa categoria.pk correctamente")
            
        if 'option value=""' in content:
            print("✅ El template tiene opción por defecto")
        else:
            print("❌ El template NO tiene opción por defecto")
            
        return True
        
    except Exception as e:
        print(f"❌ ERROR al leer template: {e}")
        return False

def probar_creacion_subcategoria():
    print("\n🆕 PROBANDO CREACIÓN DE SUBCATEGORÍA")
    print("=" * 50)
    
    # Buscar una categoría para probar
    categoria = Categoria.objects.filter(activa=True).first()
    if not categoria:
        print("❌ No hay categorías activas para probar")
        return False
    
    print(f"📁 Usando categoría: {categoria.nombre} (ID: {categoria.id})")
    
    # Intentar crear subcategoría
    try:
        subcategoria_test = Subcategoria(
            categoria=categoria,
            nombre="Test Subcategoría Script",
            descripcion="Subcategoría creada por script de prueba",
            activa=True
        )
        
        # Validar (no guardar aún)
        subcategoria_test.full_clean()
        print("✅ Validación exitosa")
        
        # Verificar si ya existe
        if Subcategoria.objects.filter(categoria=categoria, nombre="Test Subcategoría Script").exists():
            print("⚠️ La subcategoría de prueba ya existe")
        else:
            subcategoria_test.save()
            print(f"✅ Subcategoría creada: {subcategoria_test}")
            
        return True
        
    except Exception as e:
        print(f"❌ ERROR al crear subcategoría: {e}")
        return False

def main():
    print("🔧 DIAGNÓSTICO COMPLETO: FORMULARIO SUBCATEGORÍAS")
    print("=" * 60)
    
    resultados = []
    
    # 1. Verificar categorías en BD
    categorias_count = Categoria.objects.filter(activa=True).count()
    print(f"📊 Categorías activas en BD: {categorias_count}")
    resultados.append(categorias_count > 0)
    
    # 2. Simular formulario
    resultados.append(simular_formulario_subcategoria())
    
    # 3. Verificar template
    resultados.append(verificar_formulario_html())
    
    # 4. Probar creación
    resultados.append(probar_creacion_subcategoria())
    
    # Resumen
    exitosos = sum(resultados)
    total = len(resultados)
    
    print("\n" + "=" * 60)
    print(f"📈 RESULTADO FINAL: {exitosos}/{total} pruebas exitosas")
    
    if exitosos == total:
        print("✅ El formulario debería funcionar correctamente")
        print("💡 Si el dropdown sigue vacío, puede ser un problema de caché o JavaScript")
    else:
        print("❌ Hay problemas detectados que deben corregirse")
        
    return exitosos == total

if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\n🔧 POSIBLES SOLUCIONES:")
        print("1. Limpiar caché del navegador")
        print("2. Verificar que la vista esté pasando 'categorias' al contexto")
        print("3. Verificar que el template esté accediendo correctamente al contexto")
        print("4. Probar con un navegador en modo incógnito")
    
    sys.exit(0 if success else 1)