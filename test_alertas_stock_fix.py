#!/usr/bin/env python
"""
Test rápido para verificar que la URL alertas_stock se resuelve correctamente
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
    url = reverse('inventario:alertas_stock')
    print(f"✅ URL inventario:alertas_stock resuelve correctamente: {url}")
    
    # Verificar que la vista existe
    from inventario.views import AlertasStockView
    print(f"✅ Vista AlertasStockView importada correctamente: {AlertasStockView}")
    
    print(f"\n🎉 CORRECCIÓN APLICADA EXITOSAMENTE")
    print(f"   La URL 'inventario:alertas_stock' ahora funciona correctamente")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"   La corrección no fue exitosa")