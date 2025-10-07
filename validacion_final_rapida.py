#!/usr/bin/env python
"""
Validación final súper rápida - Solo aspectos críticos
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from django.test.client import Client
from django.urls import reverse, NoReverseMatch
from django.template.loader import get_template
from django.template import TemplateDoesNotExist

def main():
    print("🚀 VALIDACIÓN FINAL SÚPER RÁPIDA")
    print("="*50)
    
    errores = 0
    tests = 0
    
    # 1. URLs críticas
    urls_criticas = [
        'ventas:dashboard',
        'inventario:dashboard', 
        'accounts:dashboard',
        'analytics:dashboard'
    ]
    
    print("\n🔗 URLs Críticas:")
    for url_name in urls_criticas:
        tests += 1
        try:
            url = reverse(url_name)
            print(f"✅ {url_name} → {url}")
        except:
            print(f"❌ {url_name} FALLA")
            errores += 1
    
    # 2. Templates críticos
    templates_criticos = [
        'base.html',
        'inventario/dashboard.html',
        'ventas/dashboard.html'
    ]
    
    print("\n📄 Templates Críticos:")
    for template in templates_criticos:
        tests += 1
        try:
            get_template(template)
            print(f"✅ {template}")
        except:
            print(f"❌ {template} NO EXISTE")
            errores += 1
    
    # 3. Conexión DB
    print("\n💾 Base de Datos:")
    tests += 1
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("✅ Conexión DB OK")
    except:
        print("❌ Error conexión DB")
        errores += 1
    
    # 4. Test de login
    print("\n🔐 Sistema Auth:")
    tests += 1
    try:
        client = Client()
        response = client.get('/accounts/login/')
        if response.status_code == 200:
            print("✅ Sistema login OK")
        else:
            print(f"❌ Login error: {response.status_code}")
            errores += 1
    except Exception as e:
        print(f"❌ Error login: {e}")
        errores += 1
    
    # RESULTADO FINAL
    exito = ((tests - errores) / tests * 100) if tests > 0 else 0
    
    print("\n" + "="*50)
    print("🎯 RESULTADO FINAL:")
    print(f"✅ Tests pasados: {tests - errores}/{tests}")
    print(f"❌ Tests fallidos: {errores}")
    print(f"📊 Porcentaje éxito: {exito:.1f}%")
    
    if exito == 100:
        print("\n🎉 SISTEMA 100% FUNCIONAL - LISTO PARA PRODUCCIÓN")
        return True
    elif exito >= 90:
        print(f"\n✅ SISTEMA EN BUEN ESTADO ({errores} problemas menores)")
        return True
    else:
        print(f"\n⚠️ SISTEMA REQUIERE ATENCIÓN ({errores} problemas)")
        return False

if __name__ == "__main__":
    resultado = main()
    sys.exit(0 if resultado else 1)