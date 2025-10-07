#!/usr/bin/env python
"""
Script para verificar el estado de las categorías y activar las inactivas
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from inventario.models import Categoria
from django.utils import timezone

def verificar_categorias():
    print("🔍 VERIFICANDO ESTADO DE CATEGORÍAS")
    print("=" * 50)
    
    categorias = Categoria.objects.all().order_by('fecha_creacion')
    
    activas = 0
    inactivas = 0
    
    print(f"\n📊 TODAS LAS CATEGORÍAS ({categorias.count()}):")
    for categoria in categorias:
        estado = "✅ ACTIVA" if categoria.activa else "❌ INACTIVA"
        print(f"  • ID: {categoria.id:2d} | {categoria.nombre:25s} | {estado} | Creada: {categoria.fecha_creacion.strftime('%d/%m/%Y %H:%M')}")
        
        if categoria.activa:
            activas += 1
        else:
            inactivas += 1
    
    print(f"\n📈 RESUMEN:")
    print(f"  ✅ Activas: {activas}")
    print(f"  ❌ Inactivas: {inactivas}")
    
    return inactivas > 0

def activar_categorias_inactivas():
    print("\n🔧 ACTIVANDO CATEGORÍAS INACTIVAS...")
    
    categorias_inactivas = Categoria.objects.filter(activa=False)
    
    if not categorias_inactivas.exists():
        print("  ✅ No hay categorías inactivas")
        return
    
    print(f"  📋 Encontradas {categorias_inactivas.count()} categorías inactivas:")
    for categoria in categorias_inactivas:
        print(f"     • {categoria.nombre}")
    
    # Activar todas las categorías inactivas
    actualizadas = categorias_inactivas.update(activa=True)
    print(f"  ✅ {actualizadas} categorías activadas exitosamente")

def verificar_formulario_categoria():
    print("\n🧪 VERIFICANDO FORMULARIO DE CATEGORÍAS")
    print("=" * 50)
    
    # Verificar si hay un formulario específico para categorías
    try:
        from inventario.forms import CategoriaForm
        print("  ✅ Formulario CategoriaForm encontrado")
        
        # Verificar campo activa
        form = CategoriaForm()
        if 'activa' in form.fields:
            field = form.fields['activa']
            initial = getattr(field, 'initial', None)
            print(f"  📋 Campo 'activa' configurado con initial: {initial}")
        else:
            print("  ⚠️ Campo 'activa' no encontrado en el formulario")
            
    except ImportError:
        print("  ⚠️ No hay formulario CategoriaForm específico")
        print("  📝 Se están usando fields directos en la vista")

def verificar_vista_categoria():
    print("\n🔎 VERIFICANDO VISTA DE CREACIÓN")
    print("=" * 50)
    
    try:
        from inventario.views import CategoriaCreateView
        print("  ✅ Vista CategoriaCreateView encontrada")
        
        # Verificar configuración
        fields = getattr(CategoriaCreateView, 'fields', None)
        form_class = getattr(CategoriaCreateView, 'form_class', None)
        
        if fields:
            print(f"  📋 Campos configurados: {fields}")
        elif form_class:
            print(f"  📋 Formulario configurado: {form_class}")
        else:
            print("  ⚠️ No se pudo determinar la configuración de campos")
            
    except ImportError:
        print("  ❌ Vista CategoriaCreateView no encontrada")

def main():
    print("🗂️ DIAGNÓSTICO COMPLETO: CATEGORÍAS INACTIVAS")
    print("=" * 60)
    
    # 1. Verificar estado actual
    hay_inactivas = verificar_categorias()
    
    # 2. Verificar formulario
    verificar_formulario_categoria()
    
    # 3. Verificar vista
    verificar_vista_categoria()
    
    # 4. Activar si es necesario
    if hay_inactivas:
        respuesta = input("\n¿Quieres activar todas las categorías inactivas? (s/n): ")
        if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
            activar_categorias_inactivas()
            print("\n" + "="*50)
            print("📊 ESTADO DESPUÉS DE LA ACTIVACIÓN:")
            verificar_categorias()
    
    # 5. Solución para el futuro
    print("\n💡 SOLUCIONES RECOMENDADAS:")
    print("   1. Verificar formulario de creación de categorías")
    print("   2. Asegurar que campo 'activa' tenga initial=True")
    print("   3. Revisar si hay código que desactiva categorías automáticamente")
    print("   4. Considerar hacer el campo opcional en formularios")

if __name__ == "__main__":
    main()