#!/usr/bin/env python
"""
Análisis avanzado del sistema para detectar problemas de rendimiento y configuración
"""

import os
import sys
import django
from datetime import datetime
import json
import time

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from django.db import connection
from django.conf import settings
from django.core.management import call_command
from django.test.client import Client
from django.contrib.auth import get_user_model

User = get_user_model()

def print_header(title):
    """Imprime un header formateado"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)

def analizar_rendimiento_consultas():
    """Analiza el rendimiento de consultas comunes"""
    print_header("ANÁLISIS DE RENDIMIENTO")
    
    consultas_complejas = [
        # Consultas del sistema real
        """
        SELECT COUNT(*) 
        FROM ventas_pedido p 
        LEFT JOIN ventas_cliente c ON p.cliente_id = c.id
        """,
        """
        SELECT COUNT(*) 
        FROM inventario_producto prod 
        LEFT JOIN inventario_stock stock ON prod.id = stock.producto_id
        """,
        """
        SELECT COUNT(*) 
        FROM accounts_user u
        WHERE u.is_active = 1
        """,
    ]
    
    for i, consulta in enumerate(consultas_complejas, 1):
        try:
            start_time = time.time()
            cursor = connection.cursor()
            cursor.execute(consulta.strip())
            result = cursor.fetchone()
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # en milisegundos
            
            status = "🟢 RÁPIDO" if duration < 50 else "🟡 NORMAL" if duration < 200 else "🔴 LENTO"
            print(f"Consulta {i}: {status} ({duration:.2f}ms) - {result[0] if result else 0} registros")
            
        except Exception as e:
            print(f"❌ Error en consulta {i}: {str(e)[:60]}")

def analizar_configuracion_seguridad():
    """Analiza la configuración de seguridad"""
    print_header("ANÁLISIS DE SEGURIDAD")
    
    checks = [
        ('DEBUG en producción', settings.DEBUG, '⚠️ ACTIVADO' if settings.DEBUG else '✅ DESACTIVADO'),
        ('SECRET_KEY', len(getattr(settings, 'SECRET_KEY', '')), f"✅ {len(getattr(settings, 'SECRET_KEY', ''))} caracteres" if len(getattr(settings, 'SECRET_KEY', '')) > 50 else '⚠️ MUY CORTA'),
        ('ALLOWED_HOSTS', len(settings.ALLOWED_HOSTS), f"✅ {len(settings.ALLOWED_HOSTS)} hosts" if len(settings.ALLOWED_HOSTS) > 0 else '❌ VACÍO'),
        ('Base de datos', settings.DATABASES['default']['ENGINE'], '⚠️ SQLite (desarrollo)' if 'sqlite' in settings.DATABASES['default']['ENGINE'] else '✅ Base robusta'),
    ]
    
    for check_name, value, status in checks:
        print(f"{check_name:20}: {status}")

def analizar_usuarios_sistema():
    """Analiza los usuarios del sistema"""
    print_header("ANÁLISIS DE USUARIOS")
    
    try:
        usuarios_por_rol = {}
        activos = User.objects.filter(is_active=True).count()
        inactivos = User.objects.filter(is_active=False).count()
        superusers = User.objects.filter(is_superuser=True).count()
        
        # Analizar roles si existe el campo
        if hasattr(User, 'role'):
            from django.db.models import Count
            roles = User.objects.values('role').annotate(count=Count('role')).order_by('-count')
            for rol in roles:
                usuarios_por_rol[rol['role'] or 'Sin rol'] = rol['count']
        
        print(f"👥 Total usuarios:     {User.objects.count()}")
        print(f"✅ Usuarios activos:   {activos}")
        print(f"❌ Usuarios inactivos: {inactivos}")
        print(f"🔐 Superusuarios:      {superusers}")
        
        if usuarios_por_rol:
            print("\n📊 Distribución por roles:")
            for rol, count in usuarios_por_rol.items():
                print(f"   {rol:15}: {count:>3} usuarios")
    
    except Exception as e:
        print(f"❌ Error analizando usuarios: {e}")

def analizar_logs_errores():
    """Busca logs de errores recientes"""
    print_header("ANÁLISIS DE LOGS")
    
    log_paths = [
        'logs/',
        'django.log',
        'error.log',
        'debug.log'
    ]
    
    errores_encontrados = 0
    for log_path in log_paths:
        if os.path.exists(log_path):
            if os.path.isfile(log_path):
                try:
                    with open(log_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        error_lines = [line for line in lines[-100:] if 'ERROR' in line.upper() or 'CRITICAL' in line.upper()]
                        if error_lines:
                            errores_encontrados += len(error_lines)
                            print(f"⚠️ {log_path}: {len(error_lines)} errores recientes")
                        else:
                            print(f"✅ {log_path}: Sin errores recientes")
                except:
                    print(f"❌ No se pudo leer {log_path}")
            else:
                print(f"📁 {log_path}: Directorio encontrado")
        else:
            print(f"⭕ {log_path}: No existe")
    
    if errores_encontrados == 0:
        print("✅ No se encontraron logs de errores")

def probar_funcionalidades_criticas():
    """Prueba funcionalidades críticas del sistema"""
    print_header("PRUEBA DE FUNCIONALIDADES")
    
    try:
        # Crear cliente de prueba
        client = Client()
        
        # Intentar crear un usuario de prueba
        test_user = User.objects.filter(username='test_debug').first()
        if not test_user:
            test_user = User.objects.create_user(
                username='test_debug',
                password='test123456',
                email='test@debug.com'
            )
            print("✅ Usuario de prueba creado")
        else:
            print("✅ Usuario de prueba ya existe")
        
        # Probar login
        login_success = client.login(username='test_debug', password='test123456')
        if login_success:
            print("✅ Sistema de autenticación funciona")
            
            # Probar algunas URLs autenticado
            urls_autenticadas = [
                ('/accounts/dashboard/', 'Dashboard usuarios'),
                ('/admin/', 'Panel admin'),
            ]
            
            for url, descripcion in urls_autenticadas:
                try:
                    response = client.get(url)
                    if response.status_code < 400:
                        print(f"✅ {descripcion}: OK ({response.status_code})")
                    else:
                        print(f"⚠️ {descripcion}: {response.status_code}")
                except Exception as e:
                    print(f"❌ {descripcion}: Error - {str(e)[:40]}")
        else:
            print("❌ Error en sistema de autenticación")
    
    except Exception as e:
        print(f"❌ Error probando funcionalidades: {e}")

def analizar_espacio_disco():
    """Analiza el uso de espacio en disco"""
    print_header("ANÁLISIS DE ESPACIO")
    
    import shutil
    
    try:
        # Espacio total disponible
        total, used, free = shutil.disk_usage('.')
        total_gb = total // (1024**3)
        used_gb = used // (1024**3)
        free_gb = free // (1024**3)
        
        print(f"💾 Espacio total:      {total_gb} GB")
        print(f"📊 Espacio usado:      {used_gb} GB")
        print(f"📁 Espacio libre:      {free_gb} GB")
        
        # Tamaño de la base de datos
        if os.path.exists('db.sqlite3'):
            db_size = os.path.getsize('db.sqlite3') / (1024**2)  # MB
            print(f"🗄️ Base de datos:      {db_size:.2f} MB")
        
        # Tamaño de archivos estáticos
        static_size = 0
        if os.path.exists('static'):
            for root, dirs, files in os.walk('static'):
                static_size += sum(os.path.getsize(os.path.join(root, file)) for file in files)
            static_size_mb = static_size / (1024**2)
            print(f"📄 Archivos estáticos: {static_size_mb:.2f} MB")
        
        # Tamaño de media
        media_size = 0
        if os.path.exists('media'):
            for root, dirs, files in os.walk('media'):
                media_size += sum(os.path.getsize(os.path.join(root, file)) for file in files)
            media_size_mb = media_size / (1024**2)
            print(f"🖼️ Archivos media:     {media_size_mb:.2f} MB")
    
    except Exception as e:
        print(f"❌ Error analizando espacio: {e}")

def generar_reporte_avanzado():
    """Genera un reporte avanzado completo"""
    reporte = {
        'timestamp': datetime.now().isoformat(),
        'version_django': django.VERSION,
        'configuracion': {
            'debug': settings.DEBUG,
            'database': settings.DATABASES['default']['ENGINE'],
            'allowed_hosts': settings.ALLOWED_HOSTS,
            'installed_apps': len(settings.INSTALLED_APPS)
        }
    }
    
    # Guardar reporte
    with open('reporte_avanzado_sistema.json', 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Reporte avanzado guardado en: reporte_avanzado_sistema.json")

def main():
    """Función principal"""
    print_header("ANÁLISIS AVANZADO DEL SISTEMA")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ejecutar todos los análisis
    analizar_rendimiento_consultas()
    analizar_configuracion_seguridad()
    analizar_usuarios_sistema()
    analizar_logs_errores()
    probar_funcionalidades_criticas()
    analizar_espacio_disco()
    
    # Generar reporte final
    generar_reporte_avanzado()
    
    print_header("ANÁLISIS AVANZADO COMPLETO")
    print("🎯 Sistema analizado exitosamente")
    print("📋 Revisa reporte_avanzado_sistema.json para detalles técnicos")

if __name__ == "__main__":
    main()