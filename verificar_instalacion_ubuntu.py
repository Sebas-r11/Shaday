#!/usr/bin/env python
"""
Script de verificación de instalación en Ubuntu
Verifica que todos los componentes funcionen correctamente
"""

import os
import sys
import subprocess
import platform

def verificar_python():
    """Verificar versión de Python"""
    print("🐍 Verificando Python...")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major != 3 or version.minor < 8:
        print("   ❌ ERROR: Se requiere Python 3.8 o superior")
        return False
    
    print("   ✅ Versión de Python compatible")
    return True

def verificar_sistema():
    """Verificar sistema operativo"""
    print("\n🖥️ Verificando Sistema...")
    sistema = platform.system()
    distribucion = platform.version()
    print(f"   Sistema: {sistema}")
    print(f"   Distribución: {distribucion}")
    
    if "Ubuntu" in distribucion or "ubuntu" in distribucion:
        print("   ✅ Ubuntu detectado")
        return True
    else:
        print("   ⚠️ No es Ubuntu, pero debería funcionar")
        return True

def verificar_dependencias():
    """Verificar dependencias de requirements.txt"""
    print("\n📦 Verificando dependencias...")
    
    try:
        import django
        print(f"   ✅ Django {django.get_version()}")
    except ImportError:
        print("   ❌ Django no instalado")
        return False
    
    try:
        import reportlab
        print(f"   ✅ ReportLab disponible")
    except ImportError:
        print("   ❌ ReportLab no instalado")
        return False
    
    try:
        import openpyxl
        print(f"   ✅ OpenPyXL disponible")
    except ImportError:
        print("   ❌ OpenPyXL no instalado")
        return False
    
    try:
        import rest_framework
        print(f"   ✅ Django REST Framework disponible")
    except ImportError:
        print("   ❌ Django REST Framework no instalado")
        return False
    
    return True

def verificar_base_datos():
    """Verificar configuración de base de datos"""
    print("\n🗄️ Verificando base de datos...")
    
    if os.path.exists('db.sqlite3'):
        print("   ✅ Base de datos SQLite encontrada")
        return True
    else:
        print("   ⚠️ Base de datos no encontrada, ejecutar: python manage.py migrate")
        return False

def verificar_estructura_proyecto():
    """Verificar estructura del proyecto Django"""
    print("\n📁 Verificando estructura del proyecto...")
    
    carpetas_requeridas = [
        'accounts', 'inventario', 'ventas', 'compras', 'crm', 
        'templates', 'static', 'sistema_reyes'
    ]
    
    todas_ok = True
    for carpeta in carpetas_requeridas:
        if os.path.exists(carpeta):
            print(f"   ✅ {carpeta}/")
        else:
            print(f"   ❌ {carpeta}/ no encontrada")
            todas_ok = False
    
    return todas_ok

def verificar_servidor():
    """Verificar que el servidor Django puede iniciarse"""
    print("\n🌐 Verificando servidor Django...")
    
    try:
        # Verificar sintaxis básica
        result = subprocess.run([
            sys.executable, 'manage.py', 'check'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("   ✅ Verificación de Django exitosa")
            return True
        else:
            print(f"   ❌ Error en verificación: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("   ❌ Timeout en verificación")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def mostrar_comandos_utiles():
    """Mostrar comandos útiles para Ubuntu"""
    print("\n🛠️ Comandos útiles para Ubuntu:")
    print("   # Actualizar pip:")
    print("   python -m pip install --upgrade pip")
    print("   ")
    print("   # Instalar dependencias del sistema (si es necesario):")
    print("   sudo apt update")
    print("   sudo apt install python3-dev build-essential")
    print("   ")
    print("   # Reinstalar dependencias:")
    print("   pip install -r requirements.txt --force-reinstall")
    print("   ")
    print("   # Crear entorno virtual:")
    print("   python -m venv venv")
    print("   source venv/bin/activate")
    print("   ")
    print("   # Iniciar servidor:")
    print("   python manage.py runserver")

def main():
    """Función principal"""
    print("=" * 60)
    print("🔍 VERIFICACIÓN DE INSTALACIÓN - UBUNTU")
    print("=" * 60)
    
    verificaciones = [
        verificar_python(),
        verificar_sistema(),
        verificar_dependencias(),
        verificar_base_datos(),
        verificar_estructura_proyecto(),
        verificar_servidor()
    ]
    
    exitosas = sum(verificaciones)
    total = len(verificaciones)
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTADO: {exitosas}/{total} verificaciones exitosas")
    
    if exitosas == total:
        print("✅ ¡Instalación completamente funcional!")
        print("🚀 Puedes ejecutar: python manage.py runserver")
    elif exitosas >= 4:
        print("⚠️ Instalación mayormente funcional con advertencias")
        print("💡 Revisa las advertencias anteriores")
    else:
        print("❌ Instalación con problemas importantes")
        print("🔧 Sigue los comandos de solución")
    
    mostrar_comandos_utiles()
    
    return exitosas == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)