#!/usr/bin/env python
"""
Script para verificar categorías y subcategorías en la base de datos
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from inventario.models import Categoria, Subcategoria

def verificar_categorias():
    print("🗂️ VERIFICACIÓN DE CATEGORÍAS Y SUBCATEGORÍAS")
    print("=" * 50)
    
    # Verificar categorías
    categorias = Categoria.objects.all()
    print(f"\n📁 CATEGORÍAS ENCONTRADAS: {categorias.count()}")
    
    if categorias.exists():
        for categoria in categorias:
            print(f"  • ID: {categoria.id} | {categoria.nombre} | Activa: {categoria.activa}")
            
            # Subcategorías de cada categoría
            subcategorias = categoria.subcategorias.all()
            if subcategorias.exists():
                print(f"    └── Subcategorías ({subcategorias.count()}):")
                for subcategoria in subcategorias:
                    print(f"        • {subcategoria.nombre} (Activa: {subcategoria.activa})")
            else:
                print("        └── Sin subcategorías")
    else:
        print("  ❌ No se encontraron categorías")
    
    # Verificar subcategorías totales
    subcategorias = Subcategoria.objects.all()
    print(f"\n📂 SUBCATEGORÍAS TOTALES: {subcategorias.count()}")
    
    # Verificar categorías activas para dropdown
    categorias_activas = Categoria.objects.filter(activa=True).order_by('nombre')
    print(f"\n✅ CATEGORÍAS ACTIVAS (para dropdown): {categorias_activas.count()}")
    for categoria in categorias_activas:
        print(f"  • {categoria.nombre}")
    
    if categorias_activas.count() == 0:
        print("\n⚠️ PROBLEMA DETECTADO:")
        print("   No hay categorías activas para mostrar en el dropdown")
        print("   Necesitas crear categorías primero o activar las existentes")
        return False
    
    return True

def crear_categorias_ejemplo():
    print("\n🔧 CREANDO CATEGORÍAS DE EJEMPLO...")
    
    categorias_ejemplo = [
        {
            'nombre': 'Electrónicos',
            'descripcion': 'Dispositivos y equipos electrónicos'
        },
        {
            'nombre': 'Oficina',
            'descripcion': 'Materiales y suministros de oficina'
        },
        {
            'nombre': 'Limpieza',
            'descripcion': 'Productos de limpieza e higiene'
        }
    ]
    
    for cat_data in categorias_ejemplo:
        categoria, created = Categoria.objects.get_or_create(
            nombre=cat_data['nombre'],
            defaults={'descripcion': cat_data['descripcion']}
        )
        if created:
            print(f"  ✅ Creada: {categoria.nombre}")
        else:
            print(f"  📁 Ya existe: {categoria.nombre}")

if __name__ == "__main__":
    if not verificar_categorias():
        respuesta = input("\n¿Quieres crear categorías de ejemplo? (s/n): ")
        if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
            crear_categorias_ejemplo()
            print("\n" + "="*50)
            verificar_categorias()