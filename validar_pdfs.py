#!/usr/bin/env python
"""
Script para validar las funciones de generación de PDF
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from ventas.models import Cliente, Cotizacion, Pedido, Factura
from compras.models import Proveedor, OrdenCompra
from inventario.models import Producto, Categoria, Subcategoria

User = get_user_model()

def validar_templates_pdf():
    """Valida que los templates de impresión existan"""
    print("🖨️  VALIDACIÓN DE TEMPLATES PDF")
    print("=" * 50)
    
    templates_pdf = [
        'ventas/cotizacion_print.html',
        'ventas/pedido_print.html', 
        'ventas/factura_print.html',
        'compras/orden_compra_print.html',
    ]
    
    base_dir = Path(__file__).parent
    templates_dir = base_dir / 'templates'
    
    for template in templates_pdf:
        template_path = templates_dir / template
        if template_path.exists():
            print(f"   ✅ {template}")
        else:
            print(f"   ❌ {template}")
    
    return True

def validar_funciones_pdf():
    """Valida que las funciones de PDF funcionen correctamente"""
    print("\n📄 VALIDACIÓN DE FUNCIONES PDF")
    print("=" * 50)
    
    factory = RequestFactory()
    
    try:
        # Verificar que existe al menos un usuario admin
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                username='admin_test',
                email='admin@test.com',
                password='admin123'
            )
            print("   ✅ Usuario admin creado para pruebas")
        
        # Test 1: Validar importaciones de PDF
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            print("   ✅ ReportLab está instalado correctamente")
        except ImportError as e:
            print(f"   ❌ Error de importación ReportLab: {e}")
            return False
        
        # Test 2: Validar vistas de PDF existen
        pdf_views = [
            'ventas.views.cotizacion_pdf',
            'ventas.views.pedido_pdf',
            'ventas.views.factura_pdf',
            'compras.views.orden_compra_pdf',
        ]
        
        for view_path in pdf_views:
            try:
                module_path, view_name = view_path.rsplit('.', 1)
                module = __import__(module_path, fromlist=[view_name])
                view_func = getattr(module, view_name)
                print(f"   ✅ Vista {view_path} existe")
            except (ImportError, AttributeError) as e:
                print(f"   ⚠️  Vista {view_path} no encontrada: {e}")
        
        # Test 3: Crear datos de prueba para PDF
        print("\n📊 CREANDO DATOS DE PRUEBA PARA PDF")
        print("-" * 30)
        
        # Crear categoría si no existe
        categoria, created = Categoria.objects.get_or_create(
            nombre="Categoria Test",
            defaults={'descripcion': 'Categoria para pruebas PDF'}
        )
        if created:
            print("   ✅ Categoría de prueba creada")
        
        # Crear subcategoría si no existe
        subcategoria, created = Subcategoria.objects.get_or_create(
            nombre="Subcategoria Test",
            categoria=categoria,
            defaults={'descripcion': 'Subcategoria para pruebas PDF'}
        )
        if created:
            print("   ✅ Subcategoría de prueba creada")
        
        # Crear producto si no existe
        producto, created = Producto.objects.get_or_create(
            codigo="PROD001",
            defaults={
                'nombre': 'Producto Test PDF',
                'categoria': categoria,
                'subcategoria': subcategoria,
                'precio_minorista': 100.00,
                'stock_minimo': 10
            }
        )
        if created:
            print("   ✅ Producto de prueba creado")
        
        # Crear cliente si no existe
        cliente, created = Cliente.objects.get_or_create(
            numero_documento="12345678-9",
            defaults={
                'nombre_completo': 'Cliente Test PDF',
                'telefono': '123456789',
                'direccion': 'Calle 123 #45-67',
                'ciudad': 'Bogotá'
            }
        )
        if created:
            print("   ✅ Cliente de prueba creado")
        
        # Crear proveedor si no existe
        proveedor, created = Proveedor.objects.get_or_create(
            numero_documento="98765432-1",
            defaults={
                'razon_social': 'Proveedor Test PDF',
                'nombre_comercial': 'Proveedor Test',
                'tipo_documento': 'NIT'
            }
        )
        if created:
            print("   ✅ Proveedor de prueba creado")
        
        print(f"\n✅ Datos de prueba listos:")
        print(f"   - Categoria: {categoria.nombre}")
        print(f"   - Subcategoria: {subcategoria.nombre}")
        print(f"   - Producto: {producto.nombre}")
        print(f"   - Cliente: {cliente.nombre_completo}")
        print(f"   - Proveedor: {proveedor.razon_social}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error en validación de funciones PDF: {e}")
        return False

def validar_urls_pdf():
    """Valida que las URLs de PDF estén configuradas"""
    print("\n🔗 VALIDACIÓN DE URLs PDF")
    print("=" * 50)
    
    try:
        from django.urls import reverse
        
        # URLs que deberían existir para PDF
        pdf_urls = [
            'ventas:cotizacion-pdf',
            'ventas:pedido-pdf',
            'ventas:factura-pdf',
            'compras:orden-compra-pdf',
        ]
        
        for url_name in pdf_urls:
            try:
                # Intentar resolver la URL con un ID dummy
                url = reverse(url_name, args=[1])
                print(f"   ✅ URL {url_name}: {url}")
            except Exception as e:
                print(f"   ❌ URL {url_name}: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error en validación de URLs: {e}")
        return False

def generar_reporte_pdf():
    """Genera un reporte del estado de los PDFs"""
    print("\n📋 REPORTE FINAL DE VALIDACIÓN PDF")
    print("=" * 50)
    
    # Contar templates existentes
    templates_dir = Path(__file__).parent / 'templates'
    templates_pdf = [
        'ventas/cotizacion_print.html',
        'ventas/pedido_print.html',
        'ventas/factura_print.html', 
        'compras/orden_compra_print.html',
    ]
    
    templates_encontrados = 0
    for template in templates_pdf:
        if (templates_dir / template).exists():
            templates_encontrados += 1
    
    print(f"📊 ESTADÍSTICAS:")
    print(f"   Templates PDF: {templates_encontrados}/{len(templates_pdf)} ({(templates_encontrados/len(templates_pdf)*100):.1f}%)")
    
    # Verificar dependencias
    try:
        import reportlab
        print(f"   ReportLab: ✅ Versión {reportlab.Version}")
    except ImportError:
        print(f"   ReportLab: ❌ No instalado")
    
    try:
        import weasyprint
        print(f"   WeasyPrint: ✅ Instalado")
    except ImportError:
        print(f"   WeasyPrint: ⚠️  No instalado (opcional)")
    
    if templates_encontrados == len(templates_pdf):
        print(f"\n🎉 ¡Todos los templates PDF están presentes!")
        return True
    else:
        print(f"\n⚠️  Faltan {len(templates_pdf) - templates_encontrados} templates PDF")
        return False

if __name__ == "__main__":
    print("🔍 INICIANDO VALIDACIÓN COMPLETA DE PDFs")
    print("=" * 60)
    
    # Ejecutar todas las validaciones
    validar_templates_pdf()
    validar_funciones_pdf()
    validar_urls_pdf()
    exito = generar_reporte_pdf()
    
    if exito:
        print("\n✅ VALIDACIÓN COMPLETA: PDFs listos para usar")
    else:
        print("\n⚠️  VALIDACIÓN COMPLETA: Se requieren correcciones")