#!/usr/bin/env python
"""
Validación completa de URLs del Sistema ERP
Distribuciones Shaddai - Versión 1.0
"""

import os
import sys
import django

# Configuración Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

import time
from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse, NoReverseMatch
from django.db import transaction
from ventas.models import Cliente, Cotizacion, Pedido, Factura, Entrega

def crear_datos_test():
    """Crear datos mínimos para las pruebas"""
    print("🔧 Preparando datos de prueba...")
    
    User = get_user_model()
    
    # Crear usuario admin si no existe
    try:
        admin_user = User.objects.get(username='admin')
    except User.DoesNotExist:
        admin_user = User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
        print("✅ Usuario admin creado")
    
    # Crear cliente si no existe
    try:
        cliente = Cliente.objects.first()
        if not cliente:
            cliente = Cliente.objects.create(
                nombre='Cliente Test',
                email='test@test.com',
                telefono='1234567890'
            )
            print("✅ Cliente test creado")
    except Exception as e:
        print(f"⚠️  Error creando cliente: {e}")
    
    return admin_user

def validar_urls_principales():
    """Validar URLs principales del sistema"""
    print("\n🔍 VALIDANDO URLs PRINCIPALES DEL SISTEMA")
    print("=" * 60)
    
    client = Client()
    admin_user = crear_datos_test()
    
    # Login
    client.force_login(admin_user)
    
    # URLs principales a validar
    urls_principales = [
        # URLs básicas
        ('/', 'Página Principal'),
        ('/admin/', 'Panel Admin'),
        
        # URLs de ventas
        ('/ventas/', 'Dashboard Ventas'),
        ('/ventas/dashboard/', 'Dashboard Principal'),
        ('/ventas/clientes/', 'Lista Clientes'),
        ('/ventas/cotizaciones/', 'Lista Cotizaciones'),
        ('/ventas/pedidos/', 'Lista Pedidos'),
        ('/ventas/facturas/', 'Lista Facturas'),
        ('/ventas/entregas/', 'Lista Entregas'),
        
        # URLs de reportes
        ('/ventas/reportes/', 'Página Reportes'),
        ('/ventas/reportes/ventas/', 'Reporte Ventas'),
        ('/ventas/reportes/inventario/', 'Reporte Inventario'),
        ('/ventas/reportes/compras/', 'Reporte Compras'),
        
        # APIs públicas
        ('/api/productos/', 'API Productos'),
        ('/api/clientes/', 'API Clientes'),
        
        # Export URLs
        ('/ventas/pedidos/exportar/excel/', 'Export Pedidos Excel'),
        ('/ventas/pedidos/exportar/csv/', 'Export Pedidos CSV'),
    ]
    
    resultados = []
    
    for url, descripcion in urls_principales:
        try:
            start_time = time.time()
            response = client.get(url)
            tiempo = time.time() - start_time
            
            status = response.status_code
            if status == 200:
                emoji = "✅"
                color = "verde"
            elif status in [301, 302]:
                emoji = "🔄"
                color = "amarillo"
            elif status == 404:
                emoji = "❌"
                color = "rojo"
            elif status == 403:
                emoji = "🔒"
                color = "naranja"
            else:
                emoji = "⚠️"
                color = "azul"
            
            print(f"   {emoji} {descripcion:<30} Status {status} ({tiempo:.3f}s)")
            resultados.append({
                'url': url,
                'descripcion': descripcion,
                'status': status,
                'tiempo': tiempo,
                'ok': status in [200, 301, 302]
            })
            
        except Exception as e:
            print(f"   ❌ {descripcion:<30} ERROR: {str(e)[:50]}")
            resultados.append({
                'url': url,
                'descripcion': descripcion,
                'status': 500,
                'tiempo': 0,
                'ok': False,
                'error': str(e)
            })
    
    return resultados

def validar_urls_con_parametros():
    """Validar URLs que requieren parámetros"""
    print("\n🔍 VALIDANDO URLs CON PARÁMETROS")
    print("=" * 60)
    
    client = Client()
    admin_user = crear_datos_test()
    client.force_login(admin_user)
    
    resultados = []
    
    # Obtener IDs existentes
    try:
        cliente = Cliente.objects.first()
        cotizacion = Cotizacion.objects.first()
        pedido = Pedido.objects.first()
        factura = Factura.objects.first()
        entrega = Entrega.objects.first()
        
        urls_parametros = []
        
        if cliente:
            urls_parametros.extend([
                (f'/ventas/clientes/{cliente.id}/', f'Detalle Cliente {cliente.id}'),
                (f'/ventas/clientes/{cliente.id}/edit/', f'Editar Cliente {cliente.id}'),
            ])
        
        if cotizacion:
            urls_parametros.extend([
                (f'/ventas/cotizaciones/{cotizacion.id}/', f'Detalle Cotización {cotizacion.id}'),
                (f'/ventas/cotizaciones/{cotizacion.id}/imprimir/', f'PDF Cotización {cotizacion.id}'),
            ])
        
        if pedido:
            urls_parametros.extend([
                (f'/ventas/pedidos/{pedido.id}/', f'Detalle Pedido {pedido.id}'),
                (f'/ventas/pedidos/{pedido.id}/imprimir/', f'PDF Pedido {pedido.id}'),
            ])
        
        if factura:
            urls_parametros.extend([
                (f'/ventas/facturas/{factura.id}/', f'Detalle Factura {factura.id}'),
                (f'/ventas/facturas/{factura.id}/imprimir/', f'PDF Factura {factura.id}'),
            ])
        
        if entrega:
            urls_parametros.extend([
                (f'/ventas/entregas/{entrega.id}/', f'Detalle Entrega {entrega.id}'),
            ])
        
        for url, descripcion in urls_parametros:
            try:
                start_time = time.time()
                response = client.get(url)
                tiempo = time.time() - start_time
                
                status = response.status_code
                if status == 200:
                    emoji = "✅"
                elif status in [301, 302]:
                    emoji = "🔄"
                elif status == 404:
                    emoji = "❌"
                else:
                    emoji = "⚠️"
                
                print(f"   {emoji} {descripcion:<30} Status {status} ({tiempo:.3f}s)")
                resultados.append({
                    'url': url,
                    'descripcion': descripcion,
                    'status': status,
                    'tiempo': tiempo,
                    'ok': status in [200, 301, 302]
                })
                
            except Exception as e:
                print(f"   ❌ {descripcion:<30} ERROR: {str(e)[:50]}")
                resultados.append({
                    'url': url,
                    'descripcion': descripcion,
                    'status': 500,
                    'tiempo': 0,
                    'ok': False,
                    'error': str(e)
                })
        
        if not urls_parametros:
            print("   ⚠️  No hay datos suficientes para probar URLs con parámetros")
            
    except Exception as e:
        print(f"   ❌ Error general en URLs con parámetros: {e}")
    
    return resultados

def validar_apis_completas():
    """Validar APIs más profundamente"""
    print("\n🔍 VALIDANDO APIs DETALLADAMENTE")
    print("=" * 60)
    
    client = Client()
    admin_user = crear_datos_test()
    client.force_login(admin_user)
    
    apis = [
        ('/api/productos/', 'API Productos'),
        ('/api/clientes/', 'API Clientes'),
        ('/api/estadisticas/dashboard/', 'API Estadísticas Dashboard'),
        ('/api/estadisticas/ventas-mes/', 'API Ventas por Mes'),
        ('/api/estadisticas/productos-vendidos/', 'API Productos Vendidos'),
        ('/api/estadisticas/estados-pedidos/', 'API Estados Pedidos'),
        ('/api/estadisticas/ventas-vendedor/', 'API Ventas por Vendedor'),
        ('/ventas/api/alertas-stock/', 'API Alertas Stock'),
    ]
    
    resultados = []
    
    for url, descripcion in apis:
        try:
            start_time = time.time()
            response = client.get(url)
            tiempo = time.time() - start_time
            
            status = response.status_code
            if status == 200:
                emoji = "✅"
                # Verificar que sea JSON válido
                try:
                    data = response.json()
                    items = len(data) if isinstance(data, list) else len(data.keys()) if isinstance(data, dict) else 0
                    extra_info = f"({items} items)"
                except:
                    extra_info = "(No JSON)"
            elif status == 404:
                emoji = "❌"
                extra_info = "(Not Found)"
            else:
                emoji = "⚠️"
                extra_info = f"(Status {status})"
            
            print(f"   {emoji} {descripcion:<30} Status {status} {extra_info} ({tiempo:.3f}s)")
            resultados.append({
                'url': url,
                'descripcion': descripcion,
                'status': status,
                'tiempo': tiempo,
                'ok': status == 200
            })
            
        except Exception as e:
            print(f"   ❌ {descripcion:<30} ERROR: {str(e)[:50]}")
            resultados.append({
                'url': url,
                'descripcion': descripcion,
                'status': 500,
                'tiempo': 0,
                'ok': False,
                'error': str(e)
            })
    
    return resultados

def generar_reporte_final(resultados_principales, resultados_parametros, resultados_apis):
    """Generar reporte final de validación"""
    print("\n" + "=" * 80)
    print("🎯 REPORTE FINAL DE VALIDACIÓN DE URLs")
    print("=" * 80)
    
    total_urls = len(resultados_principales) + len(resultados_parametros) + len(resultados_apis)
    urls_ok = sum(1 for r in resultados_principales + resultados_parametros + resultados_apis if r.get('ok', False))
    urls_error = total_urls - urls_ok
    
    porcentaje_ok = (urls_ok / total_urls * 100) if total_urls > 0 else 0
    
    print(f"📊 ESTADÍSTICAS GENERALES:")
    print(f"   • Total URLs validadas: {total_urls}")
    print(f"   • URLs funcionando: {urls_ok} ({porcentaje_ok:.1f}%)")
    print(f"   • URLs con problemas: {urls_error}")
    
    print(f"\n📋 DETALLE POR CATEGORÍA:")
    
    # URLs Principales
    principales_ok = sum(1 for r in resultados_principales if r.get('ok', False))
    print(f"   ✅ URLs Principales: {principales_ok}/{len(resultados_principales)} OK")
    
    # URLs con Parámetros
    parametros_ok = sum(1 for r in resultados_parametros if r.get('ok', False))
    print(f"   🔗 URLs con Parámetros: {parametros_ok}/{len(resultados_parametros)} OK")
    
    # APIs
    apis_ok = sum(1 for r in resultados_apis if r.get('ok', False))
    print(f"   🔌 APIs: {apis_ok}/{len(resultados_apis)} OK")
    
    # URLs con problemas
    problematicas = [r for r in resultados_principales + resultados_parametros + resultados_apis if not r.get('ok', False)]
    
    if problematicas:
        print(f"\n⚠️  URLs CON PROBLEMAS:")
        for problema in problematicas:
            status = problema.get('status', 'N/A')
            error = problema.get('error', '')
            if error:
                print(f"   ❌ {problema['descripcion']}: {error[:60]}")
            else:
                print(f"   ❌ {problema['descripcion']}: Status {status}")
    
    # Rendimiento
    tiempos = [r.get('tiempo', 0) for r in resultados_principales + resultados_parametros + resultados_apis if r.get('tiempo')]
    if tiempos:
        tiempo_promedio = sum(tiempos) / len(tiempos)
        tiempo_max = max(tiempos)
        print(f"\n⚡ RENDIMIENTO:")
        print(f"   • Tiempo promedio: {tiempo_promedio:.3f}s")
        print(f"   • Tiempo máximo: {tiempo_max:.3f}s")
    
    # Estado final
    if porcentaje_ok >= 90:
        estado = "🎉 EXCELENTE"
        color = "verde"
    elif porcentaje_ok >= 75:
        estado = "✅ BUENO"
        color = "amarillo"
    elif porcentaje_ok >= 50:
        estado = "⚠️  REGULAR"
        color = "naranja"
    else:
        estado = "❌ NECESITA ATENCIÓN"
        color = "rojo"
    
    print(f"\n🏆 ESTADO GENERAL DEL SISTEMA: {estado}")
    print(f"   Sistema ERP con {porcentaje_ok:.1f}% de URLs funcionando correctamente")
    
    return {
        'total_urls': total_urls,
        'urls_ok': urls_ok,
        'urls_error': urls_error,
        'porcentaje_ok': porcentaje_ok,
        'estado': estado
    }

def main():
    """Función principal de validación"""
    print("🔍 VALIDACIÓN COMPLETA DE URLs - SISTEMA ERP")
    print("Distribuciones Shaddai - Versión 1.0")
    print("=" * 80)
    
    # Ejecutar validaciones
    resultados_principales = validar_urls_principales()
    resultados_parametros = validar_urls_con_parametros()
    resultados_apis = validar_apis_completas()
    
    # Generar reporte final
    reporte = generar_reporte_final(resultados_principales, resultados_parametros, resultados_apis)
    
    print("\n" + "=" * 80)
    print("✅ VALIDACIÓN COMPLETA DE URLs FINALIZADA")
    print(f"🚀 Sistema listo con {reporte['porcentaje_ok']:.1f}% de funcionalidad")

if __name__ == '__main__':
    main()