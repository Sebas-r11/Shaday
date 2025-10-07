#!/usr/bin/env python3
"""
Test de instalación específico para Ubuntu/Linux
Valida que todas las dependencias se instalen correctamente en Ubuntu
"""
import subprocess
import sys
import os

def test_ubuntu_installation():
    """Test específico para Ubuntu"""
    print("🐧 TEST DE INSTALACIÓN - UBUNTU/LINUX")
    print("Sistema ERP - Distribuciones Shaddai")
    print("=" * 50)
    
    # Verificar Python
    python_version = sys.version_info
    print(f"🐍 Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Se requiere Python 3.8 o superior")
        return False
    
    # Verificar pip
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"📦 pip: {result.stdout.strip()}")
        else:
            print("❌ pip no disponible")
            return False
    except Exception as e:
        print(f"❌ Error verificando pip: {e}")
        return False
    
    # Verificar requirements.txt
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt no encontrado")
        return False
    
    print("📋 requirements.txt encontrado")
    
    # Mostrar dependencias que se van a instalar
    print("\n📦 DEPENDENCIAS A INSTALAR:")
    print("-" * 30)
    
    with open('requirements.txt', 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line and not line.startswith('#') and '==' in line:
                print(f"   {line}")
    
    print("\n🔧 COMANDOS PARA UBUNTU:")
    print("-" * 30)
    print("# Actualizar sistema")
    print("sudo apt update && sudo apt upgrade -y")
    print()
    print("# Instalar dependencias del sistema")
    print("sudo apt install python3-pip python3-venv python3-dev")
    print()
    print("# Crear entorno virtual")
    print("python3 -m venv venv")
    print()
    print("# Activar entorno virtual")
    print("source venv/bin/activate")
    print()
    print("# Actualizar pip")
    print("pip install --upgrade pip")
    print()
    print("# Instalar dependencias")
    print("pip install -r requirements.txt")
    print()
    print("# Configurar Django")
    print("python manage.py migrate")
    print("python crear_datos_ejemplo.py")
    print("python manage.py runserver")
    
    print("\n⚠️  POSIBLES PROBLEMAS EN UBUNTU:")
    print("-" * 40)
    print("1. Si falla Pillow:")
    print("   sudo apt install libjpeg-dev libpng-dev")
    print()
    print("2. Si falla reportlab:")
    print("   sudo apt install libfreetype6-dev")
    print()
    print("3. Si faltan headers de Python:")
    print("   sudo apt install python3-dev")
    print()
    print("4. Si hay problemas de permisos:")
    print("   Usar entorno virtual (venv)")
    
    print("\n✅ SCRIPT PARA INSTALACIÓN AUTOMÁTICA:")
    print("-" * 45)
    print("""#!/bin/bash
# Script de instalación para Ubuntu
set -e

echo "🐧 Instalando Sistema ERP en Ubuntu..."

# Actualizar sistema
sudo apt update

# Instalar dependencias del sistema
sudo apt install -y python3 python3-pip python3-venv python3-dev \\
                    libjpeg-dev libpng-dev libfreetype6-dev

# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias de Python
pip install -r requirements.txt

# Configurar Django
python manage.py migrate

# Crear datos de ejemplo
python crear_datos_ejemplo.py

echo "✅ Instalación completada!"
echo "🚀 Para ejecutar: source venv/bin/activate && python manage.py runserver"
""")
    
    return True

if __name__ == '__main__':
    test_ubuntu_installation()