#!/usr/bin/env python
"""
Script para probar la creación de una categoría nueva y verificar que se cree como activa
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from inventario.models import Categoria
from inventario.forms import CategoriaForm

def probar_formulario_categoria():
    print("🧪 PROBANDO FORMULARIO DE CATEGORÍA")
    print("=" * 50)
    
    # 1. Instanciar formulario vacío
    form = CategoriaForm()
    
    print("📋 Configuración del formulario:")
    for field_name, field in form.fields.items():
        initial = getattr(field, 'initial', None)
        widget_attrs = getattr(field.widget, 'attrs', {})
        checked = widget_attrs.get('checked', False)
        print(f"  • {field_name}: initial={initial}, checked={checked}")
    
    # 2. Simular datos de formulario
    datos_prueba = {
        'nombre': 'Categoría Prueba Script',
        'descripcion': 'Categoría creada por script para verificar que se cree como activa',
        'activa': True  # Explícitamente True
    }
    
    print(f"\n📝 Datos de prueba: {datos_prueba}")
    
    # 3. Crear formulario con datos
    form_con_datos = CategoriaForm(data=datos_prueba)
    
    if form_con_datos.is_valid():
        print("✅ Formulario válido")
        
        # Verificar si ya existe
        if Categoria.objects.filter(nombre=datos_prueba['nombre']).exists():
            print("⚠️ Categoría de prueba ya existe, eliminándola...")
            Categoria.objects.filter(nombre=datos_prueba['nombre']).delete()
        
        # Guardar
        categoria = form_con_datos.save()
        print(f"✅ Categoría creada: {categoria.nombre} | Activa: {categoria.activa}")
        
        return categoria.activa
        
    else:
        print("❌ Formulario inválido:")
        for field, errors in form_con_datos.errors.items():
            print(f"  • {field}: {errors}")
        return False

def probar_creacion_directa():
    print("\n🔧 PROBANDO CREACIÓN DIRECTA (sin formulario)")
    print("=" * 50)
    
    try:
        # Verificar si ya existe
        if Categoria.objects.filter(nombre='Categoría Directa Script').exists():
            Categoria.objects.filter(nombre='Categoría Directa Script').delete()
        
        # Crear directamente
        categoria = Categoria.objects.create(
            nombre='Categoría Directa Script',
            descripcion='Categoría creada directamente para verificar default'
            # NO especificar 'activa' para que use el default del modelo
        )
        
        print(f"✅ Categoría creada directamente: {categoria.nombre} | Activa: {categoria.activa}")
        return categoria.activa
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🔍 PRUEBA COMPLETA: CREACIÓN DE CATEGORÍAS")
    print("=" * 60)
    
    # 1. Probar formulario
    resultado_formulario = probar_formulario_categoria()
    
    # 2. Probar creación directa
    resultado_directo = probar_creacion_directa()
    
    # 3. Resumen
    print("\n" + "=" * 60)
    print("📊 RESULTADOS:")
    print(f"  • Formulario: {'✅ Activa' if resultado_formulario else '❌ Inactiva'}")
    print(f"  • Creación directa: {'✅ Activa' if resultado_directo else '❌ Inactiva'}")
    
    if resultado_formulario and resultado_directo:
        print("\n🎉 ¡TODO FUNCIONA CORRECTAMENTE!")
        print("   Las categorías se crean como activas por defecto")
    else:
        print("\n⚠️ HAY PROBLEMAS:")
        if not resultado_formulario:
            print("   • El formulario no está configurando activa=True")
        if not resultado_directo:
            print("   • El modelo no tiene default=True")

if __name__ == "__main__":
    main()