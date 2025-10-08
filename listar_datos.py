#!/usr/bin/env python
"""
Script para listar productos y clientes disponibles
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from inventario.models import Producto
from ventas.models import Cliente

def listar_datos():
    print("=== DATOS DISPONIBLES PARA BÚSQUEDA ===\n")
    
    # Listar productos
    print("📦 PRODUCTOS ACTIVOS:")
    productos = Producto.objects.filter(activo=True)[:10]
    if productos:
        for p in productos:
            print(f"  • {p.codigo} - {p.nombre}")
    else:
        print("  No hay productos activos")
    
    print()
    
    # Listar clientes  
    print("👥 CLIENTES:")
    clientes = Cliente.objects.all()[:10]
    if clientes:
        for c in clientes:
            print(f"  • {c.numero_documento} - {c.nombre_completo}")
    else:
        print("  No hay clientes")

if __name__ == '__main__':
    listar_datos()