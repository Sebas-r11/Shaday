#!/usr/bin/env python
"""
Herramienta de monitoreo en tiempo real del sistema Django ERP
Detecta problemas, errores 404/500, y URLs problemáticas en vivo
"""

import os
import sys
import django
from datetime import datetime, timedelta
import json
import time
import threading

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from django.test.client import Client
from django.urls import reverse, NoReverseMatch
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

class SistemaMonitor:
    def __init__(self):
        self.client = Client()
        self.errores_detectados = []
        self.urls_criticas = []
        self.running = False
        self.report_data = {
            'inicio_monitoreo': datetime.now().isoformat(),
            'errores': [],
            'urls_probadas': 0,
            'urls_exitosas': 0,
            'urls_fallidas': 0
        }
    
    def log_error(self, tipo, descripcion, detalles=None):
        """Registra un error detectado"""
        error = {
            'timestamp': datetime.now().isoformat(),
            'tipo': tipo,
            'descripcion': descripcion,
            'detalles': detalles or {}
        }
        self.errores_detectados.append(error)
        self.report_data['errores'].append(error)
        print(f"🚨 [{datetime.now().strftime('%H:%M:%S')}] {tipo}: {descripcion}")
    
    def log_success(self, mensaje):
        """Registra un éxito"""
        print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] {mensaje}")
    
    def probar_url(self, url, descripcion, expected_status=None):
        """Prueba una URL específica"""
        try:
            response = self.client.get(url)
            self.report_data['urls_probadas'] += 1
            
            if expected_status:
                if response.status_code == expected_status:
                    self.report_data['urls_exitosas'] += 1
                    self.log_success(f"{descripcion}: {response.status_code}")
                    return True
                else:
                    self.report_data['urls_fallidas'] += 1
                    self.log_error("URL_ERROR", f"{descripcion} - Status inesperado", {
                        'url': url,
                        'expected': expected_status,
                        'actual': response.status_code
                    })
                    return False
            else:
                if response.status_code < 400:
                    self.report_data['urls_exitosas'] += 1
                    self.log_success(f"{descripcion}: {response.status_code}")
                    return True
                else:
                    self.report_data['urls_fallidas'] += 1
                    self.log_error("URL_ERROR", f"{descripcion} - Error {response.status_code}", {
                        'url': url,
                        'status': response.status_code
                    })
                    return False
        except Exception as e:
            self.report_data['urls_fallidas'] += 1
            self.log_error("URL_EXCEPTION", f"{descripcion} - Excepción", {
                'url': url,
                'error': str(e)
            })
            return False
    
    def probar_urls_django_reverse(self):
        """Prueba URLs usando Django reverse para detectar NoReverseMatch"""
        print(f"\n🔍 [{datetime.now().strftime('%H:%M:%S')}] Probando URLs con Django reverse...")
        
        urls_to_test = [
            # URLs básicas
            ('ventas:dashboard', None, 'Dashboard Ventas'),
            ('inventario:dashboard', None, 'Dashboard Inventario'), 
            ('accounts:dashboard', None, 'Dashboard Usuarios'),
            ('analytics:dashboard', None, 'Dashboard Analytics'),
            
            # URLs con argumentos (usando IDs que existen)
            ('ventas:pedido_detail', [1], 'Detalle Pedido'),
            ('inventario:producto_detail', [1], 'Detalle Producto'),
            ('accounts:user_detail', [1], 'Detalle Usuario'),
            ('ventas:cliente_detail', [1], 'Detalle Cliente'),
            
            # URLs de listados
            ('ventas:pedido_list', None, 'Lista Pedidos'),
            ('ventas:factura_list', None, 'Lista Facturas'),
            ('inventario:producto_list', None, 'Lista Productos'),
            ('accounts:user_list', None, 'Lista Usuarios'),
        ]
        
        for url_name, args, descripcion in urls_to_test:
            try:
                if args:
                    url = reverse(url_name, args=args)
                else:
                    url = reverse(url_name)
                self.log_success(f"Reverse OK: {url_name} -> {url}")
            except NoReverseMatch as e:
                self.log_error("REVERSE_ERROR", f"NoReverseMatch: {url_name}", {
                    'url_name': url_name,
                    'args': args,
                    'error': str(e)
                })
            except Exception as e:
                self.log_error("REVERSE_EXCEPTION", f"Error en reverse: {url_name}", {
                    'url_name': url_name,
                    'args': args,
                    'error': str(e)
                })
    
    def probar_urls_autenticadas(self):
        """Prueba URLs que requieren autenticación"""
        print(f"\n🔐 [{datetime.now().strftime('%H:%M:%S')}] Probando URLs autenticadas...")
        
        # Crear usuario de prueba si no existe
        test_user = User.objects.filter(username='monitor_test').first()
        if not test_user:
            test_user = User.objects.create_user(
                username='monitor_test',
                password='monitor123',
                email='monitor@test.com'
            )
            if hasattr(test_user, 'role'):
                test_user.role = 'vendedor'
                test_user.save()
        
        # Login
        login_success = self.client.login(username='monitor_test', password='monitor123')
        if login_success:
            self.log_success("Login exitoso para pruebas autenticadas")
            
            # URLs que requieren autenticación
            urls_autenticadas = [
                ('/ventas/', 'Dashboard Ventas Autenticado'),
                ('/accounts/dashboard/', 'Dashboard Usuarios Autenticado'),
                ('/admin/', 'Panel Admin'),
                ('/ventas/pedidos/', 'Lista Pedidos Autenticado'),
                ('/inventario/productos/', 'Lista Productos Autenticado'),
            ]
            
            for url, descripcion in urls_autenticadas:
                self.probar_url(url, descripcion)
            
            # Logout
            self.client.logout()
        else:
            self.log_error("AUTH_ERROR", "No se pudo hacer login para pruebas autenticadas")
    
    def monitorear_base_datos(self):
        """Monitorea el estado de la base de datos"""
        print(f"\n💾 [{datetime.now().strftime('%H:%M:%S')}] Monitoreando base de datos...")
        
        try:
            # Probar conexión básica
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            self.log_success("Conexión a base de datos OK")
            
            # Verificar tablas principales
            tablas_principales = [
                'accounts_user',
                'ventas_pedido',
                'ventas_factura',
                'inventario_producto',
                'django_session'
            ]
            
            for tabla in tablas_principales:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                    count = cursor.fetchone()[0]
                    self.log_success(f"Tabla {tabla}: {count} registros")
                except Exception as e:
                    self.log_error("DB_TABLE_ERROR", f"Error en tabla {tabla}", {
                        'tabla': tabla,
                        'error': str(e)
                    })
        
        except Exception as e:
            self.log_error("DB_CONNECTION_ERROR", "Error de conexión a base de datos", {
                'error': str(e)
            })
    
    def verificar_archivos_criticos(self):
        """Verifica que existan archivos críticos del sistema"""
        print(f"\n📁 [{datetime.now().strftime('%H:%M:%S')}] Verificando archivos críticos...")
        
        archivos_criticos = [
            ('manage.py', 'Script de gestión Django'),
            ('sistema_reyes/settings.py', 'Configuración principal'),
            ('sistema_reyes/urls.py', 'URLs principales'),
            ('db.sqlite3', 'Base de datos'),
            ('templates/', 'Directorio de templates'),
            ('static/', 'Directorio de archivos estáticos'),
            ('media/', 'Directorio de archivos media'),
        ]
        
        for archivo, descripcion in archivos_criticos:
            if os.path.exists(archivo):
                self.log_success(f"{descripcion}: Existe")
            else:
                self.log_error("FILE_MISSING", f"{descripcion}: NO EXISTE", {
                    'archivo': archivo
                })
    
    def ejecutar_ciclo_monitoreo(self):
        """Ejecuta un ciclo completo de monitoreo"""
        print(f"\n{'='*60}")
        print(f"🎯 CICLO DE MONITOREO - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print('='*60)
        
        # Ejecutar todas las verificaciones
        self.probar_urls_django_reverse()
        self.probar_urls_autenticadas()
        self.monitorear_base_datos()
        self.verificar_archivos_criticos()
        
        # Resumen del ciclo
        errores_ciclo = len([e for e in self.errores_detectados if 
                           datetime.fromisoformat(e['timestamp']) > datetime.now() - timedelta(minutes=1)])
        
        if errores_ciclo == 0:
            print(f"\n✅ Ciclo completado - Sistema funcionando correctamente")
        else:
            print(f"\n⚠️ Ciclo completado - {errores_ciclo} errores detectados")
    
    def generar_reporte_final(self):
        """Genera el reporte final del monitoreo"""
        self.report_data['fin_monitoreo'] = datetime.now().isoformat()
        self.report_data['total_errores'] = len(self.errores_detectados)
        
        # Calcular estadísticas
        if self.report_data['urls_probadas'] > 0:
            self.report_data['porcentaje_exito'] = (
                self.report_data['urls_exitosas'] / self.report_data['urls_probadas']
            ) * 100
        
        # Guardar reporte
        with open('reporte_monitoreo_sistema.json', 'w', encoding='utf-8') as f:
            json.dump(self.report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 REPORTE FINAL DE MONITOREO")
        print(f"URLs probadas: {self.report_data['urls_probadas']}")
        print(f"URLs exitosas: {self.report_data['urls_exitosas']}")
        print(f"URLs fallidas: {self.report_data['urls_fallidas']}")
        if self.report_data['urls_probadas'] > 0:
            print(f"Porcentaje éxito: {self.report_data['porcentaje_exito']:.1f}%")
        print(f"Total errores: {self.report_data['total_errores']}")
        print(f"\n📁 Reporte guardado: reporte_monitoreo_sistema.json")

def main():
    """Función principal"""
    monitor = SistemaMonitor()
    
    print("🚀 INICIANDO MONITOREO DEL SISTEMA")
    print("Presiona Ctrl+C para detener el monitoreo")
    
    try:
        # Ejecutar un ciclo de monitoreo
        monitor.ejecutar_ciclo_monitoreo()
        
        # Generar reporte final
        monitor.generar_reporte_final()
        
    except KeyboardInterrupt:
        print(f"\n🛑 Monitoreo detenido por el usuario")
        monitor.generar_reporte_final()
    except Exception as e:
        print(f"\n❌ Error en monitoreo: {e}")
        monitor.generar_reporte_final()

if __name__ == "__main__":
    main()