#!/usr/bin/env python
"""
Test para verificar que la URL transferencia_create se resuelve correctamente
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

try:
    from django.urls import reverse
    
    # Probar resolver la URL
    url = reverse('inventario:transferencia_create')
    print(f"✅ URL inventario:transferencia_create resuelve correctamente: {url}")
    
    # Verificar que la vista existe
    from inventario.views import transferencia_producto
    print(f"✅ Vista transferencia_producto importada correctamente: {transferencia_producto}")
    
    print(f"\n🎉 CORRECCIÓN APLICADA EXITOSAMENTE")
    print(f"   La URL 'inventario:transferencia_create' ahora funciona correctamente")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"   La corrección no fue exitosa")