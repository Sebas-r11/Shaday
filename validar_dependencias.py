#!/usr/bin/env python
"""
Validador de dependencias - Sistema ERP Distribuciones Shaddai
Verifica que todas las dependencias del requirements.txt estén correctamente instaladas
"""
import sys
import importlib
import subprocess

def check_dependencies():
    """Verifica las dependencias principales del sistema"""
    print("🔍 VALIDADOR DE DEPENDENCIAS - SISTEMA ERP")
    print("Distribuciones Shaddai - Versión 1.0")
    print("=" * 60)
    
    # Dependencias críticas para el funcionamiento
    critical_dependencies = {
        'django': 'Framework principal del sistema',
        'reportlab': 'Generación de PDFs (Módulo 1)',
        'openpyxl': 'Exportación Excel/CSV (Módulo 4)', 
        'requests': 'APIs REST (Módulo 2)',
        'PIL': 'Procesamiento de imágenes (Pillow)',
        'dateutil': 'Utilidades de fecha y tiempo',
        'rest_framework': 'Django REST Framework'
    }
    
    # Dependencias opcionales pero recomendadas
    optional_dependencies = {
        'crispy_forms': 'Formularios mejorados',
        'debug_toolbar': 'Herramientas de desarrollo',
        'decouple': 'Variables de entorno',
        'django_extensions': 'Extensiones de Django',
        'whitenoise': 'Archivos estáticos en producción'
    }
    
    print("🔍 VERIFICANDO DEPENDENCIAS CRÍTICAS")
    print("-" * 40)
    
    critical_ok = 0
    critical_total = len(critical_dependencies)
    
    for dep, description in critical_dependencies.items():
        try:
            if dep == 'PIL':
                import PIL
                version = PIL.__version__
            elif dep == 'dateutil':
                import dateutil
                version = dateutil.__version__
            elif dep == 'rest_framework':
                import rest_framework
                version = rest_framework.VERSION
            else:
                module = importlib.import_module(dep)
                version = getattr(module, '__version__', 'N/A')
            
            print(f"   ✅ {dep:<15} v{version:<10} - {description}")
            critical_ok += 1
            
        except ImportError:
            print(f"   ❌ {dep:<15} FALTANTE      - {description}")
    
    print()
    print("🔍 VERIFICANDO DEPENDENCIAS OPCIONALES")
    print("-" * 40)
    
    optional_ok = 0
    optional_total = len(optional_dependencies)
    
    for dep, description in optional_dependencies.items():
        try:
            module = importlib.import_module(dep)
            version = getattr(module, '__version__', 'N/A')
            print(f"   ✅ {dep:<15} v{version:<10} - {description}")
            optional_ok += 1
        except ImportError:
            print(f"   ⚠️  {dep:<15} FALTANTE      - {description}")
    
    print()
    print("🔍 VERIFICANDO FUNCIONALIDADES DEL SISTEMA")
    print("-" * 40)
    
    # Test específicos de funcionalidades
    functionalities = []
    
    # Test generación PDFs
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        functionalities.append("✅ Generación de PDFs: OK")
    except ImportError:
        functionalities.append("❌ Generación de PDFs: FALTA reportlab")
    
    # Test exportación Excel
    try:
        from openpyxl import Workbook
        functionalities.append("✅ Exportación Excel: OK")
    except ImportError:
        functionalities.append("❌ Exportación Excel: FALTA openpyxl")
    
    # Test APIs REST
    try:
        from rest_framework.response import Response
        functionalities.append("✅ APIs REST: OK")
    except ImportError:
        functionalities.append("❌ APIs REST: FALTA djangorestframework")
    
    # Test procesamiento imágenes
    try:
        from PIL import Image
        functionalities.append("✅ Procesamiento Imágenes: OK")
    except ImportError:
        functionalities.append("❌ Procesamiento Imágenes: FALTA Pillow")
    
    for func in functionalities:
        print(f"   {func}")
    
    print()
    print("=" * 60)
    print("📊 RESUMEN DE VALIDACIÓN")
    print("=" * 60)
    
    print(f"🎯 Dependencias Críticas: {critical_ok}/{critical_total} ({(critical_ok/critical_total)*100:.1f}%)")
    print(f"🔧 Dependencias Opcionales: {optional_ok}/{optional_total} ({(optional_ok/optional_total)*100:.1f}%)")
    
    if critical_ok == critical_total:
        print("\n🎉 TODAS LAS DEPENDENCIAS CRÍTICAS ESTÁN INSTALADAS")
        print("✅ Sistema listo para funcionar correctamente")
        
        if optional_ok == optional_total:
            print("🏆 INSTALACIÓN PERFECTA: Todas las dependencias presentes")
        else:
            print(f"⚠️  Faltan {optional_total - optional_ok} dependencias opcionales")
            print("   (El sistema funcionará, pero con funcionalidades limitadas)")
    else:
        missing_critical = critical_total - critical_ok
        print(f"\n❌ FALTAN {missing_critical} DEPENDENCIAS CRÍTICAS")
        print("🚨 El sistema NO funcionará correctamente")
        print("\n📝 Para instalar todas las dependencias ejecuta:")
        print("   pip install -r requirements.txt")
    
    print()
    print("🔍 VALIDACIÓN COMPLETADA")
    
    return critical_ok == critical_total

def show_installation_commands():
    """Muestra comandos de instalación"""
    print("\n" + "=" * 60)
    print("📝 COMANDOS DE INSTALACIÓN")
    print("=" * 60)
    print()
    print("1️⃣ Instalar todas las dependencias:")
    print("   pip install -r requirements.txt")
    print()
    print("2️⃣ Migrar base de datos:")
    print("   python manage.py migrate")
    print()
    print("3️⃣ Crear superusuario:")
    print("   python manage.py createsuperuser")
    print()
    print("4️⃣ Ejecutar servidor de desarrollo:")
    print("   python manage.py runserver")
    print()
    print("🔍 Para validar la instalación:")
    print("   python validar_dependencias.py")

if __name__ == '__main__':
    success = check_dependencies()
    
    if '--install-help' in sys.argv:
        show_installation_commands()
    
    if not success:
        print("\n⚠️  Usa: python validar_dependencias.py --install-help")
        print("   Para ver los comandos de instalación")
    
    sys.exit(0 if success else 1)