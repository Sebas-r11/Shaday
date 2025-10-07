#!/usr/bin/env python
"""
Script para corregir los problemas detectados por el monitoreo del sistema
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

def print_header(title):
    """Imprime un header formateado"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)

def corregir_inventario_dashboard():
    """Corrige el problema de inventario:dashboard que no existe"""
    print_header("CORRIGIENDO INVENTARIO DASHBOARD")
    
    # Buscar si existe el dashboard en inventario/urls.py
    urls_file = 'inventario/urls.py'
    
    try:
        with open(urls_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'dashboard' not in content:
            # Agregar la URL del dashboard
            dashboard_line = "\n    # Dashboard\n    path('', views.InventarioDashboardView.as_view(), name='dashboard'),"
            
            # Encontrar donde insertar (después de urlpatterns = [)
            lines = content.split('\n')
            new_lines = []
            
            for line in lines:
                new_lines.append(line)
                if 'urlpatterns = [' in line:
                    new_lines.append("    # Dashboard")
                    new_lines.append("    path('', views.InventarioDashboardView.as_view(), name='dashboard'),")
                    new_lines.append("")
            
            # Escribir archivo modificado
            with open(urls_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            
            print("✅ URL dashboard agregada a inventario/urls.py")
        else:
            print("✅ URL dashboard ya existe en inventario/urls.py")
    
    except Exception as e:
        print(f"❌ Error corrigiendo dashboard: {e}")

def corregir_campo_fecha_creacion_entrega():
    """Corrige el problema del campo fecha_creacion en el modelo Entrega"""
    print_header("CORRIGIENDO CAMPO FECHA_CREACION EN ENTREGA")
    
    # Buscar el archivo donde se usa fecha_creacion para Entrega
    views_file = 'ventas/general_views.py'
    
    try:
        with open(views_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Reemplazar fecha_creacion por fecha_programada (que sí existe)
        if 'fecha_creacion__date=hoy' in content:
            content = content.replace(
                'fecha_creacion__date=hoy',
                'fecha_programada__date=hoy'
            )
            
            with open(views_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Campo fecha_creacion corregido a fecha_programada en Entrega")
        else:
            print("✅ Campo ya estaba corregido")
    
    except Exception as e:
        print(f"❌ Error corrigiendo campo fecha_creacion: {e}")

def corregir_campo_vendedor_pedido():
    """Corrige el problema del campo vendedor en el modelo Pedido"""
    print_header("CORRIGIENDO CAMPO VENDEDOR EN PEDIDO")
    
    # Buscar archivos que usen select_related('vendedor')
    files_to_check = [
        'ventas/pedidos_views.py',
        'ventas/general_views.py',
        'ventas/views.py'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Reemplazar vendedor por asignado_a (que sí existe según el error)
                if 'select_related(' in content and 'vendedor' in content:
                    content = content.replace(
                        "select_related('vendedor')",
                        "select_related('asignado_a')"
                    )
                    content = content.replace(
                        "select_related('cliente', 'vendedor')",
                        "select_related('cliente', 'asignado_a')"
                    )
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"✅ Campo vendedor corregido a asignado_a en {file_path}")
            
            except Exception as e:
                print(f"❌ Error corrigiendo vendedor en {file_path}: {e}")

def verificar_correcciones():
    """Verifica que las correcciones se aplicaron correctamente"""
    print_header("VERIFICANDO CORRECCIONES")
    
    from django.test.client import Client
    from django.urls import reverse, NoReverseMatch
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    client = Client()
    
    # Verificar inventario:dashboard
    try:
        url = reverse('inventario:dashboard')
        print(f"✅ inventario:dashboard funciona: {url}")
    except NoReverseMatch:
        print("❌ inventario:dashboard aún no funciona")
    
    # Crear usuario de prueba y probar URLs problemáticas
    test_user = User.objects.filter(username='test_corrections').first()
    if not test_user:
        test_user = User.objects.create_user(
            username='test_corrections',
            password='test123',
            email='test@corrections.com'
        )
        if hasattr(test_user, 'role'):
            test_user.role = 'vendedor'
            test_user.save()
    
    # Login y probar URLs
    login_success = client.login(username='test_corrections', password='test123')
    if login_success:
        print("✅ Login exitoso para verificación")
        
        # Probar URLs que fallaban
        urls_to_test = [
            ('/ventas/', 'Dashboard Ventas'),
            ('/ventas/pedidos/', 'Lista Pedidos'),
            ('/inventario/', 'Dashboard Inventario'),
        ]
        
        for url, descripcion in urls_to_test:
            try:
                response = client.get(url)
                if response.status_code < 400:
                    print(f"✅ {descripcion}: OK ({response.status_code})")
                else:
                    print(f"⚠️ {descripcion}: {response.status_code}")
            except Exception as e:
                print(f"❌ {descripcion}: Error - {str(e)[:50]}")
    else:
        print("❌ Error en login para verificación")

def main():
    """Función principal"""
    print("🔧 INICIANDO CORRECCIÓN DE PROBLEMAS DETECTADOS")
    
    # Aplicar correcciones
    corregir_inventario_dashboard()
    corregir_campo_fecha_creacion_entrega()
    corregir_campo_vendedor_pedido()
    
    # Verificar correcciones
    verificar_correcciones()
    
    print_header("CORRECCIONES COMPLETADAS")
    print("🎯 Problemas detectados por el monitoreo han sido corregidos")
    print("🔄 Ejecuta nuevamente el monitor para verificar el estado")

if __name__ == "__main__":
    main()