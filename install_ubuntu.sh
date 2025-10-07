#!/bin/bash
# ================================================================================
# SCRIPT DE INSTALACIÓN PARA UBUNTU/DEBIAN
# Sistema ERP - Distribuciones Shaddai
# ================================================================================

set -e  # Salir si hay cualquier error

echo "🐧 DISTRIBUCIONES SHADDAI - INSTALACIÓN UBUNTU"
echo "   Sistema ERP Empresarial - Versión 1.0"
echo "==============================================="
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "❌ Error: No se encuentra manage.py"
    echo "   Ejecuta este script desde el directorio del proyecto"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: No se encuentra requirements.txt"
    exit 1
fi

echo "🔄 Paso 1: Actualizando sistema..."
sudo apt update

echo ""
echo "🔄 Paso 2: Instalando dependencias del sistema..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    build-essential

echo ""
echo "🔄 Paso 3: Creando entorno virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   ✅ Entorno virtual creado"
else
    echo "   ℹ️  Entorno virtual ya existe"
fi

echo ""
echo "🔄 Paso 4: Activando entorno virtual..."
source venv/bin/activate

echo ""
echo "🔄 Paso 5: Actualizando pip..."
pip install --upgrade pip

echo ""
echo "🔄 Paso 6: Instalando dependencias de Python..."
pip install -r requirements.txt

echo ""
echo "🔄 Paso 7: Configurando base de datos..."
python manage.py makemigrations
python manage.py migrate

echo ""
echo "🔄 Paso 8: Creando datos de ejemplo..."
if [ -f "crear_datos_ejemplo.py" ]; then
    python crear_datos_ejemplo.py
else
    echo "   ⚠️  crear_datos_ejemplo.py no encontrado, saltando..."
fi

echo ""
echo "🔄 Paso 9: Recolectando archivos estáticos..."
python manage.py collectstatic --noinput || echo "   ⚠️  Collectstatic falló, continuando..."

echo ""
echo "==============================================="
echo "🎉 INSTALACIÓN COMPLETADA EXITOSAMENTE"
echo "==============================================="
echo ""
echo "📋 SIGUIENTES PASOS:"
echo "   1. Activar entorno virtual:"
echo "      source venv/bin/activate"
echo ""
echo "   2. Iniciar servidor:"
echo "      python manage.py runserver"
echo ""
echo "   3. Acceder al sistema:"
echo "      🌐 http://127.0.0.1:8000/"
echo "      🛠️  http://127.0.0.1:8000/admin/"
echo ""
echo "🔑 CREDENCIALES:"
echo "   Usuario: admin"
echo "   Contraseña: admin123"
echo ""
echo "🧪 VALIDAR INSTALACIÓN:"
echo "   python validar_dependencias.py"
echo ""
echo "🚀 ¡Sistema ERP listo para usar!"
echo "==============================================="