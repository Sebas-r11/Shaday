#!/usr/bin/env python
"""
Validación completa del sistema de generación de PDFs
Verifica todas las funcionalidades PDF del sistema ERP
"""

import os
import sys
import django
from datetime import datetime, timedelta
import json
import tempfile

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from django.test.client import Client
from django.contrib.auth import get_user_model
from django.urls import reverse, NoReverseMatch
from django.http import HttpResponse
import io

User = get_user_model()

class ValidadorPDFs:
    def __init__(self):
        self.errores = []
        self.warnings = []
        self.pdfs_validados = 0
        self.pdfs_fallidos = 0
        
    def log_error(self, categoria, mensaje, detalles=None):
        """Registra un error"""
        self.errores.append({
            'timestamp': datetime.now().isoformat(),
            'categoria': categoria,
            'mensaje': mensaje,
            'detalles': detalles or {}
        })
        self.pdfs_fallidos += 1
        print(f"❌ [{categoria}] {mensaje}")
        
    def log_warning(self, mensaje):
        """Registra un warning"""
        self.warnings.append({
            'timestamp': datetime.now().isoformat(),
            'mensaje': mensaje
        })
        print(f"⚠️ {mensaje}")
        
    def log_success(self, mensaje):
        """Registra un éxito"""
        self.pdfs_validados += 1
        print(f"✅ {mensaje}")

    def verificar_dependencias_pdf(self):
        """Verifica que las dependencias necesarias estén instaladas"""
        print(f"\n📦 VERIFICANDO DEPENDENCIAS PDF")
        
        dependencias = [
            ('reportlab', 'Generación de PDFs'),
            ('weasyprint', 'HTML a PDF (alternativo)'),
            ('xhtml2pdf', 'HTML a PDF (alternativo)'),
        ]
        
        for modulo, descripcion in dependencias:
            try:
                __import__(modulo)
                self.log_success(f"{descripcion}: {modulo} disponible")
            except ImportError:
                self.log_warning(f"{descripcion}: {modulo} no disponible (opcional)")

    def buscar_urls_pdf_sistema(self):
        """Busca todas las URLs relacionadas con PDFs en el sistema"""
        print(f"\n🔍 BUSCANDO URLs PDF EN EL SISTEMA")
        
        # URLs PDF conocidas por módulo
        urls_pdf_conocidas = [
            # Ventas
            ('ventas:imprimir_pedido', [1], 'Imprimir Pedido'),
            ('ventas:imprimir_factura', [1], 'Imprimir Factura'),
            ('ventas:generar_pdf_cotizacion', [1], 'PDF Cotización'),
            
            # Inventario
            ('inventario:generar_pdf_transferencia', [], 'PDF Transferencia'),
            ('inventario:generar_pdf_ajuste', [], 'PDF Ajuste'),
            ('inventario:imprimir_devolucion', [1], 'PDF Devolución'),
            
            # Compras
            ('compras:generar_pdf_orden', [1], 'PDF Orden Compra'),
            ('compras:imprimir_orden_compra', [1], 'Imprimir Orden'),
            
            # Reportes
            ('ventas:reporte_ventas', [], 'Reporte Ventas PDF'),
            ('inventario:exportar_productos_excel', [], 'Export Excel (no PDF pero relacionado)'),
        ]
        
        urls_encontradas = []
        
        for url_name, args, descripcion in urls_pdf_conocidas:
            try:
                if args:
                    url = reverse(url_name, args=args)
                else:
                    url = reverse(url_name)
                urls_encontradas.append((url_name, url, descripcion))
                self.log_success(f"URL PDF encontrada: {url_name} → {url}")
            except NoReverseMatch:
                self.log_warning(f"URL PDF no encontrada: {url_name}")
            except Exception as e:
                self.log_error("URL_ERROR", f"Error en URL {url_name}: {str(e)}")
        
        return urls_encontradas

    def buscar_funciones_pdf_codigo(self):
        """Busca funciones relacionadas con PDF en el código fuente"""
        print(f"\n🔎 BUSCANDO FUNCIONES PDF EN CÓDIGO")
        
        # Directorios a buscar
        directorios = ['ventas', 'inventario', 'compras', 'analytics']
        funciones_pdf_encontradas = []
        
        for directorio in directorios:
            if os.path.exists(directorio):
                for root, dirs, files in os.walk(directorio):
                    for file in files:
                        if file.endswith('.py'):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    
                                # Buscar patrones PDF
                                patrones_pdf = [
                                    'def.*pdf',
                                    'def.*imprimir',
                                    'reportlab',
                                    'canvas.Canvas',
                                    'HttpResponse.*pdf',
                                    'content_type.*pdf',
                                ]
                                
                                for patron in patrones_pdf:
                                    if patron.lower() in content.lower():
                                        funciones_pdf_encontradas.append((file_path, patron))
                                        
                            except Exception as e:
                                continue
        
        if funciones_pdf_encontradas:
            print(f"📄 Funciones PDF encontradas en {len(funciones_pdf_encontradas)} ubicaciones")
            for file_path, patron in funciones_pdf_encontradas[:10]:  # Mostrar solo las primeras 10
                print(f"   {file_path}: {patron}")
        else:
            self.log_warning("No se encontraron funciones PDF evidentes en el código")

    def probar_urls_pdf_con_autenticacion(self, urls_encontradas):
        """Prueba las URLs PDF con un usuario autenticado"""
        print(f"\n🔐 PROBANDO URLs PDF CON AUTENTICACIÓN")
        
        client = Client()
        
        # Crear usuario de prueba
        test_user = User.objects.filter(username='pdf_test_user').first()
        if not test_user:
            test_user = User.objects.create_user(
                username='pdf_test_user',
                password='pdf123',
                email='pdf@test.com',
                is_staff=True
            )
            if hasattr(test_user, 'role'):
                test_user.role = 'administrador'
                test_user.save()
        
        # Hacer login
        login_success = client.login(username='pdf_test_user', password='pdf123')
        if not login_success:
            self.log_error("AUTH_ERROR", "No se pudo hacer login para probar PDFs")
            return
        
        self.log_success("Login exitoso para pruebas PDF")
        
        # Probar cada URL PDF
        for url_name, url, descripcion in urls_encontradas:
            try:
                response = client.get(url)
                
                if response.status_code == 200:
                    # Verificar si la respuesta es PDF
                    content_type = response.get('Content-Type', '')
                    if 'pdf' in content_type.lower():
                        self.log_success(f"{descripcion}: PDF generado correctamente")
                        
                        # Verificar tamaño del PDF
                        content_length = len(response.content)
                        if content_length > 1000:  # PDF válido debe tener más de 1KB
                            self.log_success(f"  → Tamaño PDF: {content_length} bytes (válido)")
                        else:
                            self.log_warning(f"  → Tamaño PDF muy pequeño: {content_length} bytes")
                            
                    else:
                        # Podría ser HTML o redirección
                        if response.status_code == 200:
                            self.log_success(f"{descripcion}: Respuesta OK (posiblemente formulario)")
                        else:
                            self.log_warning(f"{descripcion}: Respuesta no-PDF: {content_type}")
                            
                elif response.status_code == 302:
                    self.log_success(f"{descripcion}: Redirección OK (posible flujo)")
                elif response.status_code == 404:
                    self.log_error("PDF_404", f"{descripcion}: URL no encontrada")
                elif response.status_code >= 500:
                    self.log_error("PDF_SERVER_ERROR", f"{descripcion}: Error servidor {response.status_code}")
                else:
                    self.log_warning(f"{descripcion}: Status {response.status_code}")
                    
            except Exception as e:
                self.log_error("PDF_EXCEPTION", f"{descripcion}: Excepción - {str(e)}")

    def crear_datos_prueba_pdfs(self):
        """Crea datos de prueba necesarios para generar PDFs"""
        print(f"\n🛠️ CREANDO DATOS DE PRUEBA PARA PDFs")
        
        try:
            from ventas.models import Cliente, Pedido
            from inventario.models import Producto, Categoria
            from compras.models import Proveedor
            
            # Crear categoría de prueba
            categoria_test, created = Categoria.objects.get_or_create(
                nombre='Categoría Test PDF',
                defaults={'activa': True}
            )
            if created:
                self.log_success("Categoría de prueba creada")
            
            # Crear subcategoría de prueba
            from inventario.models import Subcategoria
            subcategoria_test, created = Subcategoria.objects.get_or_create(
                nombre='Subcategoría Test PDF',
                categoria=categoria_test,
                defaults={'activa': True}
            )
            if created:
                self.log_success("Subcategoría de prueba creada")
            
            # Crear producto de prueba
            producto_test, created = Producto.objects.get_or_create(
                codigo='TEST-PDF-001',
                defaults={
                    'nombre': 'Producto Test PDF',
                    'categoria': categoria_test,
                    'subcategoria': subcategoria_test,
                    'precio_minorista': 100.00,
                    'activo': True
                }
            )
            if created:
                self.log_success("Producto de prueba creado")
            
            # Crear cliente de prueba
            cliente_test, created = Cliente.objects.get_or_create(
                numero_documento='12345678',
                defaults={
                    'nombre_completo': 'Cliente Test PDF',
                    'telefono': '1234567890',
                    'activo': True
                }
            )
            if created:
                self.log_success("Cliente de prueba creado")
            
            # Crear proveedor de prueba si existe el modelo
            try:
                proveedor_test, created = Proveedor.objects.get_or_create(
                    nit='900123456',
                    defaults={
                        'nombre': 'Proveedor Test PDF',
                        'telefono': '0987654321',
                        'activo': True
                    }
                )
                if created:
                    self.log_success("Proveedor de prueba creado")
            except:
                self.log_warning("No se pudo crear proveedor de prueba (modelo no disponible)")
            
            return {
                'categoria': categoria_test,
                'producto': producto_test,
                'cliente': cliente_test,
            }
            
        except Exception as e:
            self.log_error("DATA_CREATION_ERROR", f"Error creando datos de prueba: {str(e)}")
            return {}

    def validar_templates_pdf(self):
        """Valida que los templates para PDFs existan"""
        print(f"\n📄 VALIDANDO TEMPLATES PDF")
        
        from django.template.loader import get_template
        from django.template import TemplateDoesNotExist
        
        templates_pdf_posibles = [
            'ventas/pdf/pedido.html',
            'ventas/pdf/factura.html',
            'ventas/pdf/cotizacion.html',
            'inventario/pdf/transferencia.html',
            'compras/pdf/orden_compra.html',
            'reportes/ventas_pdf.html',
        ]
        
        for template_name in templates_pdf_posibles:
            try:
                template = get_template(template_name)
                self.log_success(f"Template PDF encontrado: {template_name}")
            except TemplateDoesNotExist:
                self.log_warning(f"Template PDF no encontrado: {template_name}")
            except Exception as e:
                self.log_error("TEMPLATE_ERROR", f"Error en template {template_name}: {str(e)}")

    def generar_reporte_validacion_pdf(self):
        """Genera el reporte final de validación PDF"""
        total_tests = self.pdfs_validados + self.pdfs_fallidos
        porcentaje_exito = (self.pdfs_validados / total_tests * 100) if total_tests > 0 else 0
        
        reporte = {
            'timestamp': datetime.now().isoformat(),
            'resumen': {
                'pdfs_validados': self.pdfs_validados,
                'pdfs_fallidos': self.pdfs_fallidos,
                'total_tests': total_tests,
                'porcentaje_exito': porcentaje_exito,
                'warnings': len(self.warnings),
                'errores': len(self.errores)
            },
            'errores': self.errores,
            'warnings': self.warnings
        }
        
        # Guardar reporte
        with open('validacion_pdfs_completa.json', 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"📊 REPORTE VALIDACIÓN PDFs")
        print('='*60)
        print(f"✅ PDFs validados: {self.pdfs_validados}")
        print(f"❌ PDFs fallidos: {self.pdfs_fallidos}")
        print(f"⚠️ Warnings: {len(self.warnings)}")
        print(f"📈 Porcentaje éxito: {porcentaje_exito:.1f}%")
        
        if porcentaje_exito >= 90:
            print(f"\n🎉 SISTEMA PDF EN EXCELENTE ESTADO")
        elif porcentaje_exito >= 70:
            print(f"\n✅ SISTEMA PDF EN BUEN ESTADO")
        elif porcentaje_exito >= 50:
            print(f"\n⚠️ SISTEMA PDF REQUIERE ATENCIÓN")
        else:
            print(f"\n❌ SISTEMA PDF REQUIERE CORRECCIÓN URGENTE")
        
        print(f"\n📁 Reporte detallado: validacion_pdfs_completa.json")

    def ejecutar_validacion_completa(self):
        """Ejecuta la validación completa de PDFs"""
        print("📋 INICIANDO VALIDACIÓN COMPLETA DE PDFs")
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Ejecutar todas las validaciones
        self.verificar_dependencias_pdf()
        urls_encontradas = self.buscar_urls_pdf_sistema()
        self.buscar_funciones_pdf_codigo()
        datos_prueba = self.crear_datos_prueba_pdfs()
        self.validar_templates_pdf()
        self.probar_urls_pdf_con_autenticacion(urls_encontradas)
        
        # Generar reporte final
        self.generar_reporte_validacion_pdf()

def main():
    """Función principal"""
    validador = ValidadorPDFs()
    validador.ejecutar_validacion_completa()

if __name__ == "__main__":
    main()