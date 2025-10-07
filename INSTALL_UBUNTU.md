# 🐧 Instalación en Ubuntu/Linux

## ⚡ Instalación Rápida (Recomendada)

```bash
# 1. Clonar el repositorio
git clone https://github.com/Sebas-r11/Shaday.git
cd Shaday

# 2. Dar permisos al script
chmod +x install_ubuntu.sh

# 3. Ejecutar instalación automática
./install_ubuntu.sh
```

## 🔧 Instalación Manual

### Paso 1: Dependencias del Sistema

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python y dependencias
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Instalar librerías para imágenes y PDFs
sudo apt install -y libjpeg-dev libpng-dev libfreetype6-dev build-essential
```

### Paso 2: Entorno Virtual

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip
```

### Paso 3: Dependencias de Python

```bash
# Instalar dependencias del proyecto
pip install -r requirements.txt
```

### Paso 4: Configurar Django

```bash
# Aplicar migraciones
python manage.py migrate

# Crear datos de ejemplo
python crear_datos_ejemplo.py

# Recolectar archivos estáticos
python manage.py collectstatic --noinput
```

### Paso 5: Iniciar Servidor

```bash
# Ejecutar servidor de desarrollo
python manage.py runserver

# El sistema estará disponible en:
# http://127.0.0.1:8000/
```

## 🚨 Solución de Problemas Ubuntu

### Error: `django-contrib-auth==0.3`
**Solucionado** ✅ - Ya removido del requirements.txt

### Error: Pillow no se instala
```bash
sudo apt install libjpeg-dev libpng-dev zlib1g-dev
pip install Pillow --upgrade
```

### Error: reportlab no se instala
```bash
sudo apt install libfreetype6-dev
pip install reportlab --upgrade
```

### Error: faltan headers de Python
```bash
sudo apt install python3-dev
```

### Error: permisos de instalación
```bash
# Usar entorno virtual (recomendado)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Error: `ModuleNotFoundError`
```bash
# Verificar que el entorno virtual está activo
source venv/bin/activate

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

## 🧪 Validación

```bash
# Verificar instalación
python test_ubuntu_install.py

# Validar dependencias
python validar_dependencias.py

# Test completo del sistema
python test_sistema_completo_final.py
```

## 🔑 Credenciales por Defecto

- **Usuario**: admin
- **Contraseña**: admin123

## 📋 Comandos Útiles Ubuntu

```bash
# Activar entorno virtual
source venv/bin/activate

# Desactivar entorno virtual
deactivate

# Ver dependencias instaladas
pip list

# Verificar versión de Python
python3 --version

# Verificar estado del servidor
ps aux | grep python

# Ver logs en tiempo real
tail -f django.log
```

## 🚀 Producción en Ubuntu

### Usando Gunicorn

```bash
# Instalar Gunicorn
pip install gunicorn

# Ejecutar con Gunicorn
gunicorn sistema_reyes.wsgi:application --bind 0.0.0.0:8000
```

### Usando systemd (Servicio)

```bash
# Crear archivo de servicio
sudo nano /etc/systemd/system/shaddai-erp.service
```

Contenido del archivo:
```ini
[Unit]
Description=Shaddai ERP Django Application
After=network.target

[Service]
User=sebastian11
Group=www-data
WorkingDirectory=/home/sebastian11/Shaday
Environment="PATH=/home/sebastian11/Shaday/venv/bin"
ExecStart=/home/sebastian11/Shaday/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 sistema_reyes.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Habilitar y iniciar servicio
sudo systemctl daemon-reload
sudo systemctl enable shaddai-erp
sudo systemctl start shaddai-erp
sudo systemctl status shaddai-erp
```

## ⚡ Comandos de Una Línea

```bash
# Instalación completa en una línea
curl -s https://raw.githubusercontent.com/Sebas-r11/Shaday/main/install_ubuntu.sh | bash

# Actualizar proyecto
git pull && source venv/bin/activate && pip install -r requirements.txt && python manage.py migrate

# Backup rápido
tar -czf backup-$(date +%Y%m%d).tar.gz . --exclude=venv --exclude=__pycache__
```

---

## ✅ Estado de Compatibilidad

- ✅ Ubuntu 20.04 LTS
- ✅ Ubuntu 22.04 LTS  
- ✅ Ubuntu 24.04 LTS
- ✅ Debian 11+
- ✅ Python 3.8+
- ✅ Todas las dependencias funcionando