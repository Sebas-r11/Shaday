#!/usr/bin/env python
"""
Script completo de debug para el sistema Django ERP
Analiza múltiples aspectos del sistema para identificar problemas potenciales
"""

import os
import sys
import django
from datetime import datetime
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from django.urls import reverse, NoReverseMatch
from django.core.management import execute_from_command_line
from django.test.client import Client
from django.contrib.auth.models import User
from django.db import connection
from django.conf import settings

def print_header(title):
    """Imprime un header formateado"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)

def analizar_urls_restantes():
    """Analiza las URLs que aún fallan"""
    print_header("ANÁLISIS DE URLs RESTANTES")
    
    # URLs que sabemos que aún fallan
    urls_problematicas = [
        ('ventas:pedido_detail', [1]),
        ('inventario:producto_detail', [1]),
        ('accounts:user_detail', [1]),
        ('ventas:cliente_detail', [1]),
        ('analytics:dashboard', []),
    ]
    
    resultados = []
    for url_name, args in urls_problematicas:
        try:
            url = reverse(url_name, args=args) if args else reverse(url_name)
            status = "✅ FUNCIONA"
        except NoReverseMatch as e:
            status = f"❌ ERROR: {str(e)}"
        except Exception as e:
            status = f"⚠️ OTRO ERROR: {str(e)}"
        
        resultados.append({
            'url': url_name,
            'args': args,
            'status': status
        })
        print(f"{url_name:30} {status}")
    
    return resultados

def analizar_modelos_datos():
    """Analiza el estado de los modelos y datos"""
    print_header("ANÁLISIS DE MODELOS Y DATOS")
    
    try:
        from ventas.models import Pedido, Factura
        from inventario.models import Producto
        from accounts.models import User
        
        stats = {
            'pedidos': Pedido.objects.count(),
            'facturas': Factura.objects.count(),
            'productos': Producto.objects.count(),
            'usuarios': User.objects.count(),
        }
        
        for modelo, count in stats.items():
            print(f"{modelo.capitalize():15}: {count:>5} registros")
        
        return stats
    except Exception as e:
        print(f"❌ Error analizando modelos: {e}")
        return {}

def analizar_configuracion():
    """Analiza la configuración del sistema"""
    print_header("ANÁLISIS DE CONFIGURACIÓN")
    
    config_items = [
        ('DEBUG', getattr(settings, 'DEBUG', 'No definido')),
        ('DATABASE', settings.DATABASES['default']['ENGINE']),
        ('STATIC_URL', getattr(settings, 'STATIC_URL', 'No definido')),
        ('MEDIA_URL', getattr(settings, 'MEDIA_URL', 'No definido')),
        ('ALLOWED_HOSTS', getattr(settings, 'ALLOWED_HOSTS', [])),
        ('INSTALLED_APPS', len(getattr(settings, 'INSTALLED_APPS', []))),
    ]
    
    for item, value in config_items:
        print(f"{item:15}: {value}")

def analizar_consultas_db():
    """Analiza consultas lentas de base de datos"""
    print_header("ANÁLISIS DE CONSULTAS DB")
    
    try:
        from django.db import connection
        
        # Ejecutar algunas consultas comunes y medir tiempo
        consultas_test = [
            "SELECT COUNT(*) FROM ventas_pedido",
            "SELECT COUNT(*) FROM inventario_producto",
            "SELECT COUNT(*) FROM auth_user",
        ]
        
        for consulta in consultas_test:
            try:
                start_time = datetime.now()
                cursor = connection.cursor()
                cursor.execute(consulta)
                result = cursor.fetchone()
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                print(f"{consulta:40} | {result[0]:>5} rows | {duration:.3f}s")
            except Exception as e:
                print(f"❌ Error en consulta: {e}")
                
    except Exception as e:
        print(f"❌ Error analizando DB: {e}")

def probar_vistas_criticas():
    """Prueba las vistas más críticas del sistema"""
    print_header("PRUEBA DE VISTAS CRÍTICAS")
    
    client = Client()
    
    # URLs críticas para probar
    urls_criticas = [
        ('/', 'Página principal'),
        ('/admin/', 'Admin Django'),
        ('/accounts/login/', 'Login'),
        ('/ventas/', 'Dashboard ventas'),
        ('/inventario/', 'Dashboard inventario'),
    ]
    
    resultados = []
    for url, descripcion in urls_criticas:
        try:
            response = client.get(url)
            status = f"✅ {response.status_code}"
            if response.status_code >= 400:
                status = f"❌ {response.status_code}"
        except Exception as e:
            status = f"❌ ERROR: {str(e)[:50]}"
        
        resultados.append({
            'url': url,
            'descripcion': descripcion,
            'status': status
        })
        print(f"{descripcion:20} | {url:20} | {status}")
    
    return resultados

def analizar_archivos_estaticos():
    """Analiza el estado de archivos estáticos"""
    print_header("ANÁLISIS DE ARCHIVOS ESTÁTICOS")
    
    static_dirs = [
        'static/',
        'templates/',
        'media/',
    ]
    
    for dir_name in static_dirs:
        if os.path.exists(dir_name):
            files = []
            for root, dirs, filenames in os.walk(dir_name):
                files.extend(filenames)
            print(f"{dir_name:15}: {len(files):>5} archivos")
        else:
            print(f"{dir_name:15}: ❌ No existe")

def generar_reporte_debug():
    """Genera un reporte completo de debug"""
    print_header("GENERANDO REPORTE COMPLETO")
    
    reporte = {
        'timestamp': datetime.now().isoformat(),
        'urls_restantes': analizar_urls_restantes(),
        'modelos_datos': analizar_modelos_datos(),
        'vistas_criticas': probar_vistas_criticas(),
    }
    
    # Guardar reporte
    with open('reporte_debug_completo.json', 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Reporte guardado en: reporte_debug_completo.json")
    return reporte

def main():
    """Función principal"""
    print_header("DEBUG SISTEMA COMPLETO - INICIO")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ejecutar todos los análisis
    analizar_urls_restantes()
    analizar_modelos_datos()
    analizar_configuracion()
    analizar_consultas_db()
    probar_vistas_criticas()
    analizar_archivos_estaticos()
    
    # Generar reporte final
    reporte = generar_reporte_debug()
    
    print_header("DEBUG COMPLETO - FINALIZADO")
    print("Revisa el archivo reporte_debug_completo.json para detalles")

if __name__ == "__main__":
    main()