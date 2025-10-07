#!/usr/bin/env python
"""
Script de instalación rápida - Sistema ERP Distribuciones Shaddai
Automatiza la instalación completa del sistema
"""
import os
import sys
import subprocess
import time

def print_header():
    print("=" * 80)
    print("🚀 DISTRIBUCIONES SHADDAI - INSTALACIÓN AUTOMÁTICA")
    print("   Sistema ERP Empresarial - Versión 1.0")
    print("=" * 80)
    print()

def run_command(command, description, check_error=True):
    """Ejecuta un comando y muestra el progreso"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ {description} - Completado")
            return True
        else:
            print(f"   ❌ {description} - Error:")
            print(f"      {result.stderr}")
            if check_error:
                return False
    except Exception as e:
        print(f"   ❌ {description} - Excepción: {str(e)}")
        if check_error:
            return False
    return True

def install_dependencies():
    """Instala las dependencias del proyecto"""
    print("📦 INSTALANDO DEPENDENCIAS")
    print("-" * 40)
    
    commands = [
        ("pip install --upgrade pip", "Actualizando pip"),
        ("pip install -r requirements.txt", "Instalando dependencias principales"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def setup_database():
    """Configura la base de datos"""
    print("\n🗄️  CONFIGURANDO BASE DE DATOS")
    print("-" * 40)
    
    commands = [
        ("python manage.py makemigrations", "Creando migraciones"),
        ("python manage.py migrate", "Aplicando migraciones"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def collect_static():
    """Recolecta archivos estáticos"""
    print("\n📁 RECOLECTANDO ARCHIVOS ESTÁTICOS")
    print("-" * 40)
    
    return run_command("python manage.py collectstatic --noinput", "Recolectando archivos estáticos", False)

def validate_installation():
    """Valida que la instalación sea correcta"""
    print("\n🔍 VALIDANDO INSTALACIÓN")
    print("-" * 40)
    
    return run_command("python validar_dependencias.py", "Validando dependencias")

def create_superuser_prompt():
    """Pregunta si crear superusuario"""
    print("\n👤 CREACIÓN DE SUPERUSUARIO")
    print("-" * 40)
    
    response = input("¿Deseas crear un superusuario ahora? (s/n): ").lower().strip()
    
    if response in ['s', 'si', 'sí', 'y', 'yes']:
        print("🔄 Creando superusuario...")
        print("   Sigue las instrucciones para crear tu cuenta de administrador:")
        os.system("python manage.py createsuperuser")
        return True
    else:
        print("   ⏭️  Puedes crear un superusuario más tarde con:")
        print("      python manage.py createsuperuser")
        return False

def show_next_steps():
    """Muestra los siguientes pasos"""
    print("\n" + "=" * 80)
    print("🎉 INSTALACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 80)
    print()
    print("📋 SIGUIENTES PASOS:")
    print("-" * 40)
    print("1️⃣ Iniciar servidor de desarrollo:")
    print("   python manage.py runserver")
    print()
    print("2️⃣ Acceder al sistema:")
    print("   🌐 Aplicación: http://127.0.0.1:8000/")
    print("   🛠️  Admin: http://127.0.0.1:8000/admin/")
    print()
    print("3️⃣ Crear usuarios adicionales (opcional):")
    print("   python manage.py createsuperuser")
    print()
    print("4️⃣ Validar funcionalidades:")
    print("   python test_sistema_completo_final.py")
    print()
    print("📊 MÓDULOS DISPONIBLES:")
    print("-" * 40)
    print("✅ Módulo 1: Generación de PDFs")
    print("✅ Módulo 2: REST APIs públicas")
    print("✅ Módulo 3: Sistema de alertas de stock")
    print("✅ Módulo 4: Exportación Excel/CSV")
    print("✅ Módulo 5: Dashboard avanzado con gráficos")
    print("✅ Módulo 6: Sistema de reportes detallados")
    print()
    print("🚀 ¡Sistema ERP listo para usar!")
    print("=" * 80)

def main():
    """Función principal de instalación"""
    print_header()
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('manage.py'):
        print("❌ Error: No se encuentra manage.py")
        print("   Asegúrate de ejecutar este script desde el directorio del proyecto")
        sys.exit(1)
    
    # Verificar que existe requirements.txt
    if not os.path.exists('requirements.txt'):
        print("❌ Error: No se encuentra requirements.txt")
        sys.exit(1)
    
    steps = [
        ("📦 Instalar dependencias", install_dependencies),
        ("🗄️  Configurar base de datos", setup_database),
        ("📁 Recolectar archivos estáticos", collect_static),
        ("🔍 Validar instalación", validate_installation),
    ]
    
    print("🚀 INICIANDO PROCESO DE INSTALACIÓN")
    print("   El proceso tomará unos minutos...")
    print()
    
    for step_name, step_function in steps:
        print(f"▶️  {step_name}")
        success = step_function()
        if not success and step_function != collect_static:  # collect_static es opcional
            print(f"\n❌ Error en: {step_name}")
            print("   La instalación no puede continuar")
            sys.exit(1)
        print()
    
    # Crear superusuario (opcional)
    create_superuser_prompt()
    
    # Mostrar próximos pasos
    show_next_steps()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Instalación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {str(e)}")
        sys.exit(1)