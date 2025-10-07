# 🏢 Sistema ERP - Distribuciones Shaddai

Sistema de Gestión Empresarial completo y moderno desarrollado en Django 5.2.7 con 6 módulos principales implementados.

## 📋 Características Principales

### ✅ Módulos Implementados (6/6)
1. **📄 Generación de PDFs** - Facturas y cotizaciones profesionales
2. **🔌 REST APIs Públicas** - Integración con sistemas externos
3. **⚠️ Sistema de Alertas de Stock** - Monitoreo automático de inventario
4. **📊 Exportación Excel/CSV** - Reportes en múltiples formatos
5. **📈 Dashboard Avanzado** - Gráficos interactivos con Chart.js
6. **📋 Sistema de Reportes** - Business Intelligence integrado

### 🚀 Estado del Sistema
- **URLs**: 33/33 (100%) funcionando
- **Módulos**: 6/6 (100%) implementados
- **Estado**: Enterprise-ready ✅

## 🛠️ Tecnologías Utilizadas

### Framework Principal
- **Django 5.2.7** - Framework web principal
- **Python 3.8+** - Lenguaje de programación

### Dependencias Críticas
- **reportlab 4.2.5** - Generación de PDFs
- **openpyxl 3.1.5** - Exportación Excel/CSV
- **djangorestframework 3.15.2** - APIs REST
- **Pillow 10.4.0** - Procesamiento de imágenes
- **requests 2.32.3** - Cliente HTTP para APIs

### Base de Datos
- **SQLite** (desarrollo) - Incluida en Python
- **PostgreSQL** (producción) - Opcional

## 📦 Instalación

### 🚀 Instalación Automática (Recomendada)

```bash
# Clonar el repositorio
git clone <repository-url>
cd grsys

# Ejecutar instalación automática
python instalar_sistema.py
```

### 🔧 Instalación Manual

```bash
# 1. Clonar el repositorio
git clone <repository-url>
cd grsys

# 2. Instalar dependencias básicas
pip install -r requirements.txt

# 3. Configurar base de datos
python manage.py migrate

# 4. Crear datos de ejemplo (primera vez)
python crear_datos_ejemplo.py

# 5. Iniciar servidor
python manage.py runserver
```

### 🏭 Instalación para Producción

```bash
# Para entornos de producción
pip install -r requirements-production.txt
```

### 👨‍💻 Instalación para Desarrollo

```bash
# Para desarrollo con herramientas adicionales
pip install -r requirements-dev.txt
```

### 🚀 Instalación de Funcionalidades Futuras

```bash
# Solo si vas a implementar ML, WebSockets, etc.
pip install -r requirements-future.txt
```

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar base de datos
python manage.py makemigrations
python manage.py migrate

# 3. Crear superusuario
python manage.py createsuperuser

# 4. Recolectar archivos estáticos
python manage.py collectstatic

# 5. Iniciar servidor
python manage.py runserver
```

### 👨‍💻 Instalación para Desarrollo

```bash
# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Habilitar debug toolbar en settings.py
DEBUG = True
```

## ✅ Validación de Dependencias

```bash
# Verificar que todas las dependencias estén instaladas
python validar_dependencias.py

# Ver comandos de instalación
python validar_dependencias.py --install-help
```

## 🧪 Testing del Sistema

```bash
# Test completo del sistema
python test_sistema_completo_final.py

# Validación de URLs
python validacion_urls_completa.py

# Test específico de módulos
python test_movimientos_corregidos.py
```

## 🌐 Acceso al Sistema

Una vez instalado y ejecutando:

- **🏠 Aplicación Principal**: http://127.0.0.1:8000/
- **🛠️ Panel de Administración**: http://127.0.0.1:8000/admin/
- **📊 Dashboard**: http://127.0.0.1:8000/dashboard/
- **🔌 APIs**: http://127.0.0.1:8000/api/

## 📁 Estructura del Proyecto

```
grsys/
├── 📦 requirements.txt          # Dependencias principales
├── 📦 requirements-dev.txt      # Dependencias de desarrollo
├── 🚀 instalar_sistema.py       # Instalación automática
├── ✅ validar_dependencias.py   # Validador de dependencias
├── 🧪 test_sistema_completo_final.py  # Testing completo
├── accounts/                    # Gestión de usuarios
├── ventas/                      # Módulo de ventas
├── inventario/                  # Módulo de inventario
├── compras/                     # Módulo de compras
├── crm/                         # CRM y oportunidades
├── api/                         # APIs REST
├── static/                      # Archivos estáticos
└── templates/                   # Plantillas HTML
```

## 🔧 Configuración de Producción

### Variables de Entorno

Crear archivo `.env`:

```env
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
DATABASE_URL=postgresql://usuario:password@localhost:5432/basedatos
```

### Dependencias de Producción

```bash
# Para PostgreSQL
pip install psycopg2-binary==2.9.9

# Para servidor web
pip install gunicorn==21.2.0

# Para cache Redis
pip install redis==5.0.8
```

## 🎯 Módulos del Sistema

### 1. 📄 Generación de PDFs
- Facturas profesionales
- Cotizaciones detalladas
- Reportes personalizados
- **Tecnología**: ReportLab

### 2. 🔌 REST APIs
- API de productos
- API de clientes
- API de estadísticas
- **Tecnología**: Django REST Framework

### 3. ⚠️ Alertas de Stock
- Monitoreo automático
- Notificaciones de stock bajo
- Dashboard de alertas
- **Tecnología**: Django nativo

### 4. 📊 Exportación
- Excel con formato
- CSV para análisis
- Filtros avanzados
- **Tecnología**: OpenPyXL

### 5. 📈 Dashboard
- Gráficos interactivos
- Métricas en tiempo real
- KPIs empresariales
- **Tecnología**: Chart.js

### 6. 📋 Reportes
- Business Intelligence
- Reportes ejecutivos
- Análisis de tendencias
- **Tecnología**: Django + ReportLab

## � Seguridad y .gitignore

### 📋 Archivos Protegidos
El sistema incluye un `.gitignore` completo que protege:

- **🗄️ Base de datos**: `db.sqlite3` - Nunca se sube al repositorio
- **🔑 Variables de entorno**: `.env` - Claves secretas protegidas  
- **📁 Archivos de usuario**: `media/` - Uploads de usuarios
- **📊 Reportes generados**: `*.pdf`, `*.xlsx` - Archivos temporales
- **🐍 Cache de Python**: `__pycache__/` - Archivos compilados
- **📝 Logs**: `*.log` - Información sensible del sistema

### 🚀 Para Nuevos Desarrolladores

```bash
# 1. Clonar el repositorio (sin base de datos)
git clone <repository-url>
cd grsys

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Crear base de datos limpia
python manage.py migrate

# 4. Crear datos de ejemplo
python crear_datos_ejemplo.py

# 5. Iniciar servidor
python manage.py runserver
```

### ⚠️ Importante
- La base de datos NO se sube al repositorio por seguridad
- Usa `crear_datos_ejemplo.py` para generar datos de prueba
- Nunca subas archivos con información real de clientes

## �🚨 Solución de Problemas

### Error de dependencias
```bash
python validar_dependencias.py
pip install -r requirements.txt
```

### Error de base de datos
```bash
python manage.py makemigrations
python manage.py migrate
```

### Error de archivos estáticos
```bash
python manage.py collectstatic --clear
```

## 👥 Soporte

Para soporte técnico o consultas:
- 📧 Email: soporte@distribuciones-shaddai.com
- 📱 WhatsApp: +57 XXX XXX XXXX
- 🌐 Web: www.distribuciones-shaddai.com

## 📄 Licencia

Sistema propietario - Distribuciones Shaddai
Todos los derechos reservados © 2025

---

## 🏆 Estado del Proyecto

**✅ SISTEMA ENTERPRISE-READY**
- 6/6 módulos completados
- 33/33 URLs funcionando (100%)
- Sistema listo para producción
- Testing completo validado

**🚀 Listo para usar en Distribuciones Shaddai**