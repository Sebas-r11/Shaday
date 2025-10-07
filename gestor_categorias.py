#!/usr/bin/env python
"""
Herramienta para gestionar el estado de categorías y subcategorías
Permite activar/desactivar y verificar el estado actual
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from inventario.models import Categoria, Subcategoria

def mostrar_menu():
    print("\n🗂️ GESTOR DE CATEGORÍAS")
    print("=" * 40)
    print("1. 📊 Ver estado actual")
    print("2. ✅ Activar todas las categorías")
    print("3. ✅ Activar todas las subcategorías")
    print("4. ❌ Desactivar categoría específica")
    print("5. ❌ Desactivar subcategoría específica")
    print("6. 🔧 Activar categoría específica")
    print("7. 🔧 Activar subcategoría específica")
    print("0. 🚪 Salir")
    print("=" * 40)

def ver_estado():
    print("\n📊 ESTADO ACTUAL")
    print("=" * 50)
    
    # Categorías
    categorias = Categoria.objects.all().order_by('nombre')
    activas_cat = categorias.filter(activa=True).count()
    inactivas_cat = categorias.filter(activa=False).count()
    
    print(f"📁 CATEGORÍAS: {categorias.count()} total")
    print(f"   ✅ Activas: {activas_cat}")
    print(f"   ❌ Inactivas: {inactivas_cat}")
    
    if inactivas_cat > 0:
        print("   🔍 Categorías inactivas:")
        for cat in categorias.filter(activa=False):
            print(f"      • {cat.nombre}")
    
    # Subcategorías
    subcategorias = Subcategoria.objects.all().order_by('categoria__nombre', 'nombre')
    activas_sub = subcategorias.filter(activa=True).count()
    inactivas_sub = subcategorias.filter(activa=False).count()
    
    print(f"\n📂 SUBCATEGORÍAS: {subcategorias.count()} total")
    print(f"   ✅ Activas: {activas_sub}")
    print(f"   ❌ Inactivas: {inactivas_sub}")
    
    if inactivas_sub > 0:
        print("   🔍 Subcategorías inactivas:")
        for sub in subcategorias.filter(activa=False):
            print(f"      • {sub.categoria.nombre} > {sub.nombre}")

def activar_todas_categorias():
    inactivas = Categoria.objects.filter(activa=False)
    count = inactivas.count()
    
    if count == 0:
        print("✅ Todas las categorías ya están activas")
        return
    
    print(f"🔧 Activando {count} categorías...")
    for cat in inactivas:
        print(f"   • {cat.nombre}")
    
    inactivas.update(activa=True)
    print(f"✅ {count} categorías activadas exitosamente")

def activar_todas_subcategorias():
    inactivas = Subcategoria.objects.filter(activa=False)
    count = inactivas.count()
    
    if count == 0:
        print("✅ Todas las subcategorías ya están activas")
        return
    
    print(f"🔧 Activando {count} subcategorías...")
    for sub in inactivas:
        print(f"   • {sub.categoria.nombre} > {sub.nombre}")
    
    inactivas.update(activa=True)
    print(f"✅ {count} subcategorías activadas exitosamente")

def desactivar_categoria():
    categorias = Categoria.objects.filter(activa=True).order_by('nombre')
    
    if not categorias.exists():
        print("❌ No hay categorías activas para desactivar")
        return
    
    print("\n📁 Categorías activas:")
    for i, cat in enumerate(categorias, 1):
        print(f"   {i}. {cat.nombre}")
    
    try:
        opcion = int(input("\nSelecciona el número de categoría a desactivar (0 para cancelar): "))
        if opcion == 0:
            return
        
        categoria = categorias[opcion - 1]
        
        # Verificar si tiene subcategorías activas
        subcategorias_activas = categoria.subcategorias.filter(activa=True).count()
        if subcategorias_activas > 0:
            print(f"⚠️ Esta categoría tiene {subcategorias_activas} subcategorías activas")
            confirmar = input("¿Quieres desactivarla de todas formas? (s/n): ")
            if confirmar.lower() not in ['s', 'si', 'sí']:
                return
        
        categoria.activa = False
        categoria.save()
        print(f"❌ Categoría '{categoria.nombre}' desactivada")
        
    except (ValueError, IndexError):
        print("❌ Opción inválida")

def activar_categoria():
    categorias = Categoria.objects.filter(activa=False).order_by('nombre')
    
    if not categorias.exists():
        print("✅ No hay categorías inactivas para activar")
        return
    
    print("\n📁 Categorías inactivas:")
    for i, cat in enumerate(categorias, 1):
        print(f"   {i}. {cat.nombre}")
    
    try:
        opcion = int(input("\nSelecciona el número de categoría a activar (0 para cancelar): "))
        if opcion == 0:
            return
        
        categoria = categorias[opcion - 1]
        categoria.activa = True
        categoria.save()
        print(f"✅ Categoría '{categoria.nombre}' activada")
        
    except (ValueError, IndexError):
        print("❌ Opción inválida")

def main():
    while True:
        mostrar_menu()
        
        try:
            opcion = input("\nSelecciona una opción: ").strip()
            
            if opcion == "0":
                print("👋 ¡Hasta luego!")
                break
            elif opcion == "1":
                ver_estado()
            elif opcion == "2":
                activar_todas_categorias()
            elif opcion == "3":
                activar_todas_subcategorias()
            elif opcion == "4":
                desactivar_categoria()
            elif opcion == "6":
                activar_categoria()
            elif opcion == "5" or opcion == "7":
                print("🚧 Funcionalidad de subcategorías en desarrollo...")
            else:
                print("❌ Opción no válida")
        
        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
        
        input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    main()