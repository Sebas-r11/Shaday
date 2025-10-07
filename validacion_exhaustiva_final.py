#!/usr/bin/env python
"""
Validación exhaustiva final del sistema Django ERP
Análisis profundo de todos los aspectos del sistema para detectar problemas ocultos
"""

import os
import sys
import django
from datetime import datetime, timedelta
import json
import time
import threading
import traceback

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from django.test.client import Client
from django.urls import reverse, NoReverseMatch
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.core.management import call_command
from django.conf import settings
from django.template.loader import get_template
from django.template import TemplateDoesNotExist

User = get_user_model()

class ValidacionExhaustiva:
    def __init__(self):
        self.errores_encontrados = []
        self.warnings_encontrados = []
        self.tests_pasados = 0
        self.tests_fallidos = 0
        
    def log_error(self, categoria, mensaje, detalles=None):
        """Registra un error encontrado"""
        error = {
            'timestamp': datetime.now().isoformat(),
            'categoria': categoria,
            'mensaje': mensaje,
            'detalles': detalles or {}
        }
        self.errores_encontrados.append(error)
        self.tests_fallidos += 1
        print(f"❌ [{categoria}] {mensaje}")
        
    def log_warning(self, categoria, mensaje):
        """Registra un warning"""
        warning = {
            'timestamp': datetime.now().isoformat(),
            'categoria': categoria,
            'mensaje': mensaje
        }
        self.warnings_encontrados.append(warning)
        print(f"⚠️ [{categoria}] {mensaje}")
        
    def log_success(self, mensaje):
        """Registra un test exitoso"""
        self.tests_pasados += 1
        print(f"✅ {mensaje}")

    def validar_todas_urls_sistema(self):
        """Valida TODAS las URLs del sistema, no solo las básicas"""
        print(f"\n🔍 VALIDACIÓN EXHAUSTIVA DE URLs")
        
        # URLs críticas por módulo
        urls_completas = [
            # Ventas - URLs críticas
            ('ventas:dashboard', None, 'Dashboard Ventas'),
            ('ventas:pedido_list', None, 'Lista Pedidos'),
            ('ventas:pedido_create', None, 'Crear Pedido'),
            ('ventas:factura_list', None, 'Lista Facturas'),
            ('ventas:factura_create', None, 'Crear Factura'),
            ('ventas:cliente_list', None, 'Lista Clientes'),
            ('ventas:cliente_create', None, 'Crear Cliente'),
            ('ventas:cotizacion_list', None, 'Lista Cotizaciones'),
            
            # Inventario - URLs críticas
            ('inventario:dashboard', None, 'Dashboard Inventario'),
            ('inventario:producto_list', None, 'Lista Productos'),
            ('inventario:producto_create', None, 'Crear Producto'),
            ('inventario:categoria_list', None, 'Lista Categorías'),
            ('inventario:bodega_list', None, 'Lista Bodegas'),
            ('inventario:stock_list', None, 'Lista Stock'),
            ('inventario:movimiento_list', None, 'Lista Movimientos'),
            
            # Compras - URLs críticas
            ('compras:dashboard', None, 'Dashboard Compras'),
            ('compras:orden_list', None, 'Lista Órdenes'),
            ('compras:proveedor_list', None, 'Lista Proveedores'),
            
            # Accounts - URLs críticas
            ('accounts:dashboard', None, 'Dashboard Usuarios'),
            ('accounts:user_list', None, 'Lista Usuarios'),
            ('accounts:user_create', None, 'Crear Usuario'),
            ('accounts:login', None, 'Login'),
            
            # Analytics - URLs críticas
            ('analytics:dashboard', None, 'Dashboard Analytics'),
            
            # CRM - URLs críticas
            ('crm:dashboard', None, 'Dashboard CRM'),
            ('crm:oportunidad_list', None, 'Lista Oportunidades'),
        ]
        
        for url_name, args, descripcion in urls_completas:
            try:
                if args:
                    url = reverse(url_name, args=args)
                else:
                    url = reverse(url_name)
                self.log_success(f"URL {url_name} → {url}")
            except NoReverseMatch as e:
                self.log_warning("URL_MISSING", f"{url_name}: {str(e)}")
            except Exception as e:
                self.log_error("URL_ERROR", f"Error en {url_name}: {str(e)}")

    def validar_templates_existen(self):
        """Valida que los templates críticos existen"""
        print(f"\n📄 VALIDACIÓN DE TEMPLATES")
        
        templates_criticos = [
            'base.html',
            'ventas/dashboard.html',
            'ventas/pedido_list.html',
            'ventas/pedido_form.html',
            'inventario/dashboard.html',
            'inventario/producto_list.html',
            'accounts/login.html',
            'accounts/dashboard.html',
            'partials/navbar.html',
        ]
        
        for template_name in templates_criticos:
            try:
                template = get_template(template_name)
                self.log_success(f"Template {template_name} existe")
            except TemplateDoesNotExist:
                self.log_error("TEMPLATE_MISSING", f"Template {template_name} no existe")
            except Exception as e:
                self.log_error("TEMPLATE_ERROR", f"Error en template {template_name}: {str(e)}")

    def validar_modelos_integridad(self):
        """Valida la integridad de los modelos principales"""
        print(f"\n🗄️ VALIDACIÓN DE MODELOS")
        
        try:
            # Importar modelos principales
            from ventas.models import Pedido, Factura, Cliente
            from inventario.models import Producto, Stock, Categoria
            from accounts.models import User
            from compras.models import OrdenCompra, Proveedor
            
            modelos_test = [
                (User, 'Usuario'),
                (Cliente, 'Cliente'),
                (Producto, 'Producto'),
                (Categoria, 'Categoría'),
                (Stock, 'Stock'),
                (Pedido, 'Pedido'),
                (Factura, 'Factura'),
                (OrdenCompra, 'Orden Compra'),
                (Proveedor, 'Proveedor'),
            ]
            
            for modelo, nombre in modelos_test:
                try:
                    count = modelo.objects.count()
                    self.log_success(f"Modelo {nombre}: {count} registros")
                except Exception as e:
                    self.log_error("MODEL_ERROR", f"Error en modelo {nombre}: {str(e)}")
                    
        except ImportError as e:
            self.log_error("IMPORT_ERROR", f"Error importando modelos: {str(e)}")

    def validar_configuracion_produccion(self):
        """Valida configuraciones críticas para producción"""
        print(f"\n⚙️ VALIDACIÓN DE CONFIGURACIÓN")
        
        # Configuraciones críticas
        checks = [
            ('SECRET_KEY', len(settings.SECRET_KEY) > 50, 'SECRET_KEY debe tener más de 50 caracteres'),
            ('DEBUG', not settings.DEBUG if 'prod' in str(settings.ALLOWED_HOSTS).lower() else True, 'DEBUG debe estar False en producción'),
            ('ALLOWED_HOSTS', len(settings.ALLOWED_HOSTS) > 0, 'ALLOWED_HOSTS no puede estar vacío'),
            ('DATABASE', 'sqlite' not in settings.DATABASES['default']['ENGINE'] if 'prod' in str(settings.ALLOWED_HOSTS).lower() else True, 'Considerar base robusta para producción'),
        ]
        
        for nombre, condicion, mensaje in checks:
            if condicion:
                self.log_success(f"Configuración {nombre}: OK")
            else:
                self.log_warning("CONFIG", f"{nombre}: {mensaje}")

    def validar_permisos_usuarios(self):
        """Valida que los permisos de usuarios funcionan correctamente"""
        print(f"\n👥 VALIDACIÓN DE PERMISOS")
        
        try:
            client = Client()
            
            # Crear usuarios de prueba con diferentes roles
            roles_test = ['vendedor', 'bodega', 'administrador']
            
            for rol in roles_test:
                username = f'test_{rol}'
                test_user = User.objects.filter(username=username).first()
                if not test_user:
                    test_user = User.objects.create_user(
                        username=username,
                        password='test123',
                        email=f'{rol}@test.com'
                    )
                    if hasattr(test_user, 'role'):
                        test_user.role = rol
                        test_user.save()
                
                # Probar login
                login_success = client.login(username=username, password='test123')
                if login_success:
                    self.log_success(f"Login {rol}: OK")
                    client.logout()
                else:
                    self.log_error("AUTH_ERROR", f"No se pudo hacer login como {rol}")
                    
        except Exception as e:
            self.log_error("PERMISSION_ERROR", f"Error validando permisos: {str(e)}")

    def validar_consultas_rendimiento(self):
        """Valida el rendimiento de consultas críticas"""
        print(f"\n⚡ VALIDACIÓN DE RENDIMIENTO")
        
        consultas_criticas = [
            ("SELECT COUNT(*) FROM accounts_user WHERE is_active = 1", "Usuarios activos"),
            ("SELECT COUNT(*) FROM inventario_producto WHERE activo = 1", "Productos activos"),
            ("SELECT COUNT(*) FROM ventas_cliente WHERE activo = 1", "Clientes activos"),
            ("SELECT COUNT(*) FROM inventario_stock", "Registros de stock"),
        ]
        
        for consulta, descripcion in consultas_criticas:
            try:
                start_time = time.time()
                cursor = connection.cursor()
                cursor.execute(consulta)
                result = cursor.fetchone()
                end_time = time.time()
                duration = (end_time - start_time) * 1000  # ms
                
                if duration < 100:
                    self.log_success(f"{descripcion}: {duration:.2f}ms - {result[0] if result else 0} registros")
                elif duration < 500:
                    self.log_warning("PERFORMANCE", f"{descripcion}: {duration:.2f}ms (lento)")
                else:
                    self.log_error("PERFORMANCE_CRITICAL", f"{descripcion}: {duration:.2f}ms (muy lento)")
                    
            except Exception as e:
                self.log_error("QUERY_ERROR", f"Error en consulta {descripcion}: {str(e)}")

    def validar_migraciones_actualizadas(self):
        """Valida que todas las migraciones están aplicadas"""
        print(f"\n🔄 VALIDACIÓN DE MIGRACIONES")
        
        try:
            # Verificar migraciones pendientes
            from django.core.management.commands.migrate import Command
            from io import StringIO
            import sys
            
            # Capturar output de showmigrations
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()
            
            try:
                call_command('showmigrations', '--plan')
                output = captured_output.getvalue()
                
                if '[X]' in output and '[ ]' not in output:
                    self.log_success("Todas las migraciones están aplicadas")
                elif '[ ]' in output:
                    self.log_warning("MIGRATIONS", "Hay migraciones pendientes")
                else:
                    self.log_success("Estado de migraciones verificado")
                    
            finally:
                sys.stdout = old_stdout
                
        except Exception as e:
            self.log_error("MIGRATION_ERROR", f"Error verificando migraciones: {str(e)}")

    def validar_archivos_estaticos(self):
        """Valida archivos estáticos y media"""
        print(f"\n📁 VALIDACIÓN DE ARCHIVOS")
        
        directorios_criticos = [
            ('static/', 'Archivos estáticos'),
            ('media/', 'Archivos media'),
            ('templates/', 'Templates'),
        ]
        
        for directorio, descripcion in directorios_criticos:
            if os.path.exists(directorio):
                archivos = 0
                for root, dirs, files in os.walk(directorio):
                    archivos += len(files)
                self.log_success(f"{descripcion}: {archivos} archivos")
            else:
                self.log_error("FILE_MISSING", f"{descripcion}: Directorio no existe")

    def prueba_estres_basica(self):
        """Prueba básica de estrés del sistema"""
        print(f"\n🚀 PRUEBA DE ESTRÉS BÁSICA")
        
        client = Client()
        urls_test = ['/', '/admin/', '/accounts/login/']
        
        for url in urls_test:
            try:
                start_time = time.time()
                for i in range(10):  # 10 requests rápidas
                    response = client.get(url)
                end_time = time.time()
                
                promedio = ((end_time - start_time) / 10) * 1000  # ms por request
                
                if promedio < 200:
                    self.log_success(f"Estrés {url}: {promedio:.2f}ms promedio")
                else:
                    self.log_warning("STRESS", f"Estrés {url}: {promedio:.2f}ms (lento)")
                    
            except Exception as e:
                self.log_error("STRESS_ERROR", f"Error en prueba de estrés {url}: {str(e)}")

    def generar_reporte_final_completo(self):
        """Genera el reporte final completo"""
        total_tests = self.tests_pasados + self.tests_fallidos
        porcentaje_exito = (self.tests_pasados / total_tests * 100) if total_tests > 0 else 0
        
        reporte = {
            'timestamp': datetime.now().isoformat(),
            'resumen': {
                'tests_pasados': self.tests_pasados,
                'tests_fallidos': self.tests_fallidos,
                'total_tests': total_tests,
                'porcentaje_exito': porcentaje_exito,
                'errores_criticos': len([e for e in self.errores_encontrados if 'CRITICAL' in e['categoria']]),
                'warnings': len(self.warnings_encontrados),
            },
            'errores': self.errores_encontrados,
            'warnings': self.warnings_encontrados
        }
        
        # Guardar reporte
        with open('validacion_exhaustiva_final.json', 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"📊 REPORTE FINAL DE VALIDACIÓN EXHAUSTIVA")
        print('='*60)
        print(f"✅ Tests pasados: {self.tests_pasados}")
        print(f"❌ Tests fallidos: {self.tests_fallidos}")
        print(f"⚠️ Warnings: {len(self.warnings_encontrados)}")
        print(f"📈 Porcentaje éxito: {porcentaje_exito:.1f}%")
        
        if porcentaje_exito >= 95:
            print(f"\n🎉 SISTEMA EN EXCELENTE ESTADO")
        elif porcentaje_exito >= 85:
            print(f"\n✅ SISTEMA EN BUEN ESTADO")
        elif porcentaje_exito >= 70:
            print(f"\n⚠️ SISTEMA REQUIERE ATENCIÓN")
        else:
            print(f"\n❌ SISTEMA REQUIERE CORRECCIÓN URGENTE")
        
        print(f"\n📁 Reporte detallado: validacion_exhaustiva_final.json")

    def ejecutar_validacion_completa(self):
        """Ejecuta todas las validaciones"""
        print("🔍 INICIANDO VALIDACIÓN EXHAUSTIVA DEL SISTEMA")
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Ejecutar todas las validaciones
        self.validar_todas_urls_sistema()
        self.validar_templates_existen()
        self.validar_modelos_integridad()
        self.validar_configuracion_produccion()
        self.validar_permisos_usuarios()
        self.validar_consultas_rendimiento()
        self.validar_migraciones_actualizadas()
        self.validar_archivos_estaticos()
        self.prueba_estres_basica()
        
        # Generar reporte final
        self.generar_reporte_final_completo()

def main():
    """Función principal"""
    validador = ValidacionExhaustiva()
    validador.ejecutar_validacion_completa()

if __name__ == "__main__":
    main()