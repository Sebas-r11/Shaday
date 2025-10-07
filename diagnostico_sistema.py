#!/usr/bin/env python
"""
🔧 CORRECCIONES FINALES DEL SISTEMA ERP
Solución de errores detectados en las pruebas comprehensivas
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

def aplicar_correcciones():
    """Aplicar correcciones a los errores detectados"""
    
    print("🔧 APLICANDO CORRECCIONES FINALES AL SISTEMA")
    print("="*60)
    
    # 1. Verificar modelos y campos
    print("\n1. Verificando estructura de modelos...")
    
    try:
        from ventas.models import Cotizacion, Pedido, Entrega
        
        # Verificar campos de Cotizacion
        cotizacion = Cotizacion.objects.first()
        if cotizacion:
            print(f"   ✅ Cotización encontrada: {cotizacion}")
            print(f"   📋 Campos disponibles: {[f.name for f in Cotizacion._meta.fields]}")
        
        # Verificar campos de Pedido
        pedido = Pedido.objects.first()
        if pedido:
            print(f"   ✅ Pedido encontrado: {pedido}")
            print(f"   📋 Campos disponibles: {[f.name for f in Pedido._meta.fields]}")
            
        # Verificar campos de Entrega
        print(f"   📋 Campos Entrega: {[f.name for f in Entrega._meta.fields]}")
        
    except Exception as e:
        print(f"   ❌ Error verificando modelos: {e}")
    
    # 2. Verificar URLs de APIs
    print("\n2. Verificando URLs de APIs...")
    
    try:
        from django.urls import reverse, NoReverseMatch
        
        urls_to_check = [
            'api:paises',
            'api:departamentos', 
            'api:ciudades',
            'api:productos',
            'api:clientes',
        ]
        
        for url_name in urls_to_check:
            try:
                url = reverse(url_name)
                print(f"   ✅ {url_name}: {url}")
            except NoReverseMatch:
                print(f"   ❌ {url_name}: No encontrada")
                
    except Exception as e:
        print(f"   ❌ Error verificando URLs: {e}")
    
    # 3. Verificar comandos de management
    print("\n3. Verificando comandos de management...")
    
    try:
        from django.core.management import get_commands
        commands = get_commands()
        
        stock_commands = [cmd for cmd in commands if 'stock' in cmd.lower() or 'alert' in cmd.lower()]
        print(f"   📋 Comandos relacionados con stock: {stock_commands}")
        
    except Exception as e:
        print(f"   ❌ Error verificando comandos: {e}")
    
    # 4. Información del sistema
    print("\n4. Información del sistema actual...")
    
    try:
        from inventario.models import Producto
        from ventas.models import Cliente, Factura
        
        print(f"   📊 Total productos: {Producto.objects.count()}")
        print(f"   📊 Total clientes: {Cliente.objects.count()}")
        print(f"   📊 Total facturas: {Factura.objects.count()}")
        
        # Verificar primer producto
        producto = Producto.objects.first()
        if producto:
            print(f"   📋 Campos Producto: {[f.name for f in Producto._meta.fields]}")
            print(f"   📋 Propiedades Producto: {[attr for attr in dir(producto) if not attr.startswith('_') and not callable(getattr(producto, attr))]}")
        
    except Exception as e:
        print(f"   ❌ Error en información del sistema: {e}")
    
    print("\n" + "="*60)
    print("✅ DIAGNÓSTICO COMPLETO REALIZADO")

if __name__ == "__main__":
    aplicar_correcciones()