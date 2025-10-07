# 📋 MANUAL COMPLETO DEL ADMINISTRADOR
**Sistema de Gestión Empresarial GRSYS**

---

## 🎯 **ÍNDICE DE CONTENIDOS**

1. [Gestión de Usuarios](#gestión-de-usuarios)
2. [Módulo de Inventario](#módulo-de-inventario)
3. [Módulo de Ventas](#módulo-de-ventas)
4. [Módulo de Compras](#módulo-de-compras)
5. [Módulo CRM](#módulo-crm)
6. [Configuración del Sistema](#configuración-del-sistema)
7. [Reportes y Análisis](#reportes-y-análisis)
8. [Gestión de Devoluciones](#gestión-de-devoluciones)

---

## 👥 **GESTIÓN DE USUARIOS**

### **Panel de Administración Django**

**🔗 Acceso:** `/admin/`
**📝 Descripción:** Panel principal para gestionar toda la estructura del sistema

#### **Botones y Funciones:**

**1. 👤 Usuarios (Users)**
- **➕ Agregar Usuario:** Crear nuevas cuentas de usuario
- **✏️ Editar Usuario:** Modificar información personal y permisos
- **🔑 Cambiar Contraseña:** Actualizar credenciales de acceso
- **🏷️ Grupos:** Asignar roles específicos (Vendedor, Bodeguero, Repartidor)

**2. 🏢 Grupos (Groups)**
- **📋 Ver Grupos:** Lista todos los roles del sistema
- **➕ Crear Grupo:** Definir nuevos roles con permisos específicos
- **⚙️ Permisos:** Configurar qué acciones puede realizar cada rol

**3. 🔐 Permisos (Permissions)**
- **👁️ Ver Permisos:** Lista completa de acciones disponibles
- **🎯 Asignar:** Otorgar permisos específicos a usuarios o grupos

### **Flujo de Creación de Usuario:**

```
1. Admin → Users → Add User
2. Completar formulario básico (username, password)
3. Save and continue editing
4. Agregar información personal (nombre, email, etc.)
5. Seleccionar Groups apropiados
6. Configurar User permissions si es necesario
7. Marcar "Active" para habilitar la cuenta
8. Save
```

**⚠️ Importante:** Siempre asignar grupo apropiado para heredar permisos correctos.

---

## 📦 **MÓDULO DE INVENTARIO**

### **Gestión de Productos**

**🔗 Acceso:** Inventario → Productos
**📝 Descripción:** Control completo del catálogo de productos

#### **Botones Principales:**

**1. 📋 Lista de Productos**
- **👁️ Ver:** Visualizar información básica del producto
- **✏️ Editar:** Modificar datos del producto
- **🗑️ Eliminar:** Remover producto del sistema
- **📊 Stock:** Ver niveles de inventario por bodega
- **📈 Historial:** Consultar movimientos del producto

**2. ➕ Crear Producto**
- **Información Básica:**
  - Nombre del producto
  - SKU (código único)
  - Descripción
  - Precio de venta
  - Precio de compra
- **Categorización:**
  - Categoría principal
  - Subcategoría
- **Inventario:**
  - Stock mínimo
  - Stock máximo
  - Unidad de medida
- **📷 Imagen:** Subir foto del producto

**3. 📊 Exportar a Excel**
- **📄 Generar:** Crear reporte completo de productos
- **💾 Descargar:** Archivo Excel con toda la información

### **Gestión de Categorías**

**🔗 Acceso:** Inventario → Categorías

#### **Botones y Funciones:**

**1. 📁 Categorías**
- **➕ Nueva Categoría:** Crear categoría principal
- **✏️ Editar:** Modificar nombre y descripción
- **🗑️ Eliminar:** Quitar categoría (solo si no tiene productos)

**2. 📂 Subcategorías**
- **➕ Nueva Subcategoría:** Crear bajo una categoría existente
- **🔄 Reasignar:** Mover subcategoría a otra categoría
- **📊 Ver Productos:** Lista productos de la subcategoría

### **Gestión de Bodegas**

**🔗 Acceso:** Inventario → Bodegas

#### **Funcionalidades:**

**1. 🏪 Lista de Bodegas**
- **👁️ Ver Detalle:** Información completa y stock actual
- **✏️ Editar:** Modificar datos de la bodega
- **👥 Asignar Bodegueros:** Gestionar personal asignado

**2. ➕ Crear Bodega**
- **Información Básica:**
  - Nombre de la bodega
  - Dirección completa
  - Teléfono de contacto
  - Email
- **Configuración:**
  - Capacidad máxima
  - Tipo de bodega
  - Estado (activa/inactiva)

### **Control de Stock**

**🔗 Acceso:** Inventario → Stock

#### **Botones de Acción:**

**1. 📊 Vista General**
- **🔍 Buscar:** Filtrar por producto, bodega o categoría
- **📈 Ver Detalle:** Información completa del stock
- **⚠️ Alertas:** Productos con stock bajo

**2. 🔄 Transferencias**
- **➡️ Nueva Transferencia:** Mover productos entre bodegas
- **📋 Ver Historial:** Consultar transferencias realizadas
- **📄 Generar PDF:** Comprobante de transferencia

### **Movimientos de Inventario**

**🔗 Acceso:** Inventario → Movimientos

#### **Tipos de Movimientos:**

**1. 📥 Entradas**
- Compras a proveedores
- Ajustes positivos
- Transferencias recibidas

**2. 📤 Salidas**
- Ventas realizadas
- Ajustes negativos
- Transferencias enviadas

**3. 🔄 Ajustes**
- Correcciones de inventario
- Productos dañados
- Pérdidas

---

## 💰 **MÓDULO DE VENTAS**

### **Gestión de Ventas**

**🔗 Acceso:** Ventas → Ventas

#### **Botones Principales:**

**1. 📋 Lista de Ventas**
- **👁️ Ver Detalle:** Información completa de la venta
- **📄 Imprimir Factura:** Generar documento PDF
- **✏️ Editar:** Modificar venta (solo si no está facturada)
- **❌ Anular:** Cancelar venta con justificación

**2. ➕ Nueva Venta**
- **👤 Seleccionar Cliente:** Buscar o crear cliente
- **🛒 Agregar Productos:** Añadir items al carrito
- **💰 Definir Precios:** Aplicar descuentos si es necesario
- **💳 Método de Pago:** Efectivo, tarjeta, crédito
- **📍 Dirección Entrega:** Para delivery
- **💾 Guardar:** Confirmar la venta

### **Gestión de Clientes**

**🔗 Acceso:** Ventas → Clientes

#### **Funcionalidades:**

**1. 👥 Lista de Clientes**
- **👁️ Ver Perfil:** Información completa y historial
- **✏️ Editar:** Actualizar datos personales
- **📊 Historial Ventas:** Ver todas las compras
- **💳 Estado Crédito:** Consultar límite y saldo

**2. ➕ Nuevo Cliente**
- **Información Personal:**
  - Nombre completo
  - Documento de identidad
  - Teléfono y email
- **Dirección:**
  - Dirección principal
  - Direcciones adicionales
  - Información de entrega
- **Configuración Comercial:**
  - Límite de crédito
  - Descuento especial
  - Vendedor asignado

### **Gestión de Pedidos**

**🔗 Acceso:** Ventas → Pedidos

#### **Estados de Pedidos:**

**1. 📝 Pendiente**
- **✅ Confirmar:** Aprobar el pedido
- **❌ Rechazar:** Cancelar con motivo
- **✏️ Editar:** Modificar productos o cantidades

**2. ✅ Confirmado**
- **📦 Preparar:** Enviar a bodega para alistamiento
- **⏰ Programar:** Asignar fecha de entrega

**3. 📦 En Preparación**
- **🚚 Asignar Repartidor:** Definir quien entrega
- **📍 Confirmar Ruta:** Optimizar recorrido

**4. 🚚 En Ruta**
- **📍 Rastrear:** Ver ubicación en tiempo real
- **🔄 Actualizar Estado:** Cambios durante entrega

**5. ✅ Entregado**
- **📄 Ver Comprobante:** Evidencia de entrega
- **💰 Confirmar Pago:** Si fue contraentrega

### **Rutas de Entrega**

**🔗 Acceso:** Ventas → Optimizar Rutas

#### **Botones de Gestión:**

**1. 🗓️ Seleccionar Fecha**
- **📅 Calendario:** Elegir día de entrega
- **🔄 Actualizar:** Cargar pedidos del día

**2. 🚚 Asignar Repartidor**
- **👤 Seleccionar:** Elegir repartidor disponible
- **📊 Ver Capacidad:** Verificar carga máxima

**3. 🗺️ Optimizar Ruta**
- **🎯 Calcular:** Generar ruta más eficiente
- **👁️ Ver Mapa:** Visualizar recorrido
- **💾 Guardar:** Confirmar asignación

**4. 📱 Controles de Entrega**
- **▶️ Iniciar Ruta:** Comenzar recorrido
- **📍 Actualizar Ubicación:** Seguimiento GPS
- **✅ Confirmar Entrega:** Marcar como entregado
- **🔄 Registrar Devolución:** Si no se puede entregar

---

## 🛒 **MÓDULO DE COMPRAS**

### **Gestión de Proveedores**

**🔗 Acceso:** Compras → Proveedores

#### **Funcionalidades:**

**1. 📋 Lista de Proveedores**
- **👁️ Ver Detalle:** Información y historial
- **✏️ Editar:** Actualizar datos
- **📊 Evaluar:** Calificar desempeño

**2. ➕ Nuevo Proveedor**
- **Información Empresarial:**
  - Razón social
  - NIT/RUT
  - Contacto principal
- **Datos Comerciales:**
  - Condiciones de pago
  - Tiempo de entrega
  - Productos que suministra

### **Órdenes de Compra**

**🔗 Acceso:** Compras → Órdenes de Compra

#### **Proceso de Compra:**

**1. ➕ Nueva Orden**
- **🏪 Seleccionar Proveedor:** Elegir proveedor
- **📦 Agregar Productos:** Definir cantidades
- **💰 Negociar Precios:** Ajustar costos
- **📅 Fecha Entrega:** Programar recepción

**2. 📋 Gestionar Orden**
- **📤 Enviar:** Transmitir orden al proveedor
- **⏰ Hacer Seguimiento:** Control de tiempos
- **📦 Recibir:** Confirmar llegada de productos
- **💰 Facturar:** Procesar pago

---

## 👥 **MÓDULO CRM**

### **Gestión de Contactos**

**🔗 Acceso:** CRM → Contactos

#### **Funciones Principales:**

**1. 👤 Perfil de Contacto**
- **📝 Información Personal:** Datos básicos
- **📞 Historial Comunicación:** Llamadas y reuniones
- **💰 Oportunidades:** Ventas potenciales
- **📊 Análisis:** Valor del cliente

**2. 📈 Oportunidades de Venta**
- **➕ Nueva Oportunidad:** Crear prospecto
- **🔄 Actualizar Estado:** Avance en el proceso
- **💰 Estimar Valor:** Proyección de venta
- **📅 Programar Seguimiento:** Próximas acciones

### **Campañas de Marketing**

**🔗 Acceso:** CRM → Campañas

#### **Gestión de Campañas:**

**1. 📧 Email Marketing**
- **✉️ Crear Campaña:** Diseñar comunicación
- **👥 Segmentar:** Definir audiencia objetivo
- **📊 Medir Resultados:** Análisis de respuesta

**2. 📱 SMS Marketing**
- **💬 Mensaje Masivo:** Envío a grupos
- **📅 Programar:** Envío automático
- **📈 Seguimiento:** Control de entregas

---

## ⚙️ **CONFIGURACIÓN DEL SISTEMA**

### **Parámetros Generales**

**🔗 Acceso:** Admin → Configuración

#### **Configuraciones Clave:**

**1. 🏢 Información Empresa**
- **📝 Datos Básicos:** Nombre, NIT, dirección
- **📞 Contacto:** Teléfonos y emails
- **🖼️ Logo:** Imagen corporativa

**2. 💰 Configuración Financiera**
- **💳 Métodos de Pago:** Efectivo, tarjeta, crédito
- **🧾 Facturación:** Numeración automática
- **💱 Moneda:** Configuración regional

**3. 📦 Configuración Logística**
- **🚚 Zonas de Entrega:** Definir áreas de cobertura
- **💰 Costos Envío:** Tarifas por zona
- **⏰ Horarios:** Disponibilidad de entregas

### **Gestión de Permisos**

**🔗 Acceso:** Admin → Auth → Groups

#### **Roles del Sistema:**

**1. 👑 Administrador**
- **✅ Acceso Total:** Todos los módulos
- **⚙️ Configuración:** Cambiar parámetros
- **👥 Gestión Usuarios:** Crear y modificar cuentas

**2. 💼 Vendedor**
- **🛒 Ventas:** Crear y gestionar ventas
- **👥 Clientes:** Gestionar su cartera
- **📊 Reportes:** Ver sus estadísticas

**3. 📦 Bodeguero**
- **📦 Inventario:** Gestionar stock
- **🔄 Movimientos:** Registrar entradas/salidas
- **📊 Reportes:** Informes de inventario

**4. 🚚 Repartidor**
- **📱 App Móvil:** Acceso a rutas
- **📍 Entregas:** Confirmar entregas
- **🔄 Devoluciones:** Registrar no entregas

---

## 📊 **REPORTES Y ANÁLISIS**

### **Dashboard Principal**

**🔗 Acceso:** Página de inicio tras login

#### **Métricas en Tiempo Real:**

**1. 💰 Ventas del Día**
- **📈 Total Vendido:** Suma del día actual
- **🎯 Meta vs Real:** Comparación con objetivo
- **📊 Gráfico Tendencia:** Evolución por horas

**2. 📦 Estado Inventario**
- **⚠️ Alertas Stock:** Productos bajo mínimo
- **📊 Rotación:** Productos más vendidos
- **💰 Valor Inventario:** Total en stock

**3. 🚚 Entregas del Día**
- **📋 Pendientes:** Pedidos por entregar
- **✅ Completadas:** Entregas exitosas
- **🔄 Devoluciones:** No entregadas

### **Reportes Específicos**

#### **1. 📈 Reporte de Ventas**
**🔗 Acceso:** Ventas → Reportes

**Filtros Disponibles:**
- **📅 Rango de Fechas:** Desde/hasta
- **👤 Vendedor:** Filtrar por vendedor específico
- **🏪 Sucursal:** Si maneja múltiples locaciones
- **💳 Método de Pago:** Efectivo, tarjeta, crédito

**Botones de Acción:**
- **👁️ Ver Reporte:** Mostrar en pantalla
- **📄 Exportar PDF:** Generar documento
- **📊 Exportar Excel:** Descargar datos
- **📧 Enviar Email:** Compartir reporte

#### **2. 📦 Reporte de Inventario**
**🔗 Acceso:** Inventario → Reportes

**Tipos de Reporte:**
- **📊 Stock Actual:** Niveles por producto
- **🔄 Movimientos:** Entradas y salidas
- **💰 Valoración:** Valor del inventario
- **📈 Rotación:** Análisis de movimiento

#### **3. 👥 Reporte de Clientes**
**🔗 Acceso:** CRM → Reportes

**Análisis Disponibles:**
- **💰 Top Clientes:** Por volumen de compra
- **📈 Frecuencia:** Clientes más activos
- **💳 Cartera:** Estado de créditos
- **🎯 Segmentación:** Clasificación por valor

---

## 🔄 **GESTIÓN DE DEVOLUCIONES**

### **Control desde Entregas**

**🔗 Acceso:** Ventas → Optimizar Rutas → Entregas

#### **Proceso de Devolución:**

**1. 🚚 Durante la Entrega**
- **❌ No se puede entregar:** Marcar motivo
  - 🏠 Cliente ausente
  - 📍 Dirección incorrecta
  - 🚫 Cliente rechaza producto
  - 📦 Producto dañado

**2. 🔄 Registro Automático**
- **💾 Guardar Devolución:** Sistema registra automáticamente
- **📱 Confirmación:** Repartidor confirma en app
- **📊 Actualización:** Stock se actualiza en tiempo real

### **Gestión en Bodega**

**🔗 Acceso:** Inventario → Devoluciones

#### **Pantalla Principal:**

**1. 📋 Lista de Devoluciones**
- **📊 Estadísticas Generales:**
  - ⏳ Pendientes de recibir
  - 🔄 Parcialmente recibidas
  - ✅ Completamente procesadas
  - 💰 Valor total pendiente

**2. 🔍 Filtros Avanzados**
- **📅 Por Fecha:** Rango de fechas
- **👤 Por Repartidor:** Filtrar por quien devolvió
- **🏷️ Por Motivo:** Tipo de devolución
- **📦 Por Estado:** Pendiente, parcial, completa

#### **Botones de Acción:**

**1. 👁️ Ver Detalle**
- **📋 Información Completa:** Cliente, repartidor, productos
- **📊 Resumen Financiero:** Valores involucrados
- **📅 Historial:** Timeline de cambios

**2. ✅ Procesar Devolución**
- **📦 Recibir Productos:** Confirmar llegada a bodega
- **🔢 Cantidad Específica:** Control granular por item
- **💬 Observaciones:** Notas sobre estado del producto
- **📊 Actualizar Stock:** Automático al confirmar

**3. ❌ Rechazar Devolución**
- **📝 Motivo Rechazo:** Explicar por qué se rechaza
- **📧 Notificación:** Avisar a repartidor y administrador
- **📊 Registro:** Mantener histórico de decisiones

#### **Procesamiento Individual:**

**1. 📦 Por Producto**
- **🔢 Cantidad a Recibir:** Número específico
- **✅ Confirmar Recepción:** Marcar como recibido
- **❌ Rechazar Item:** Si está dañado o no corresponde
- **💬 Observaciones:** Comentarios sobre el producto

**2. ⚡ Acciones Rápidas**
- **✅ Recibir Todos:** Procesar toda la devolución
- **❌ Rechazar Todos:** Si hay problemas generales
- **📄 Imprimir:** Comprobante de recepción

### **Reportes de Devoluciones**

**🔗 Acceso:** Inventario → Devoluciones → Reportes

#### **Dashboard Analítico:**

**1. 📊 Métricas Principales**
- **📈 Total Devoluciones:** Número y tendencia
- **💰 Valor Involucrado:** Impacto financiero
- **📊 Tasa de Devolución:** % vs ventas totales
- **⏱️ Tiempo Promedio:** Procesamiento en bodega

**2. 📈 Gráficos Interactivos**
- **📅 Tendencia Temporal:** Devoluciones por día/semana
- **🎯 Por Motivo:** Distribución de causas
- **👥 Por Repartidor:** Quién tiene más devoluciones
- **📦 Por Producto:** Items más devueltos

#### **Filtros de Análisis:**

**1. ⏰ Período de Tiempo**
- 🗓️ Últimos 7 días
- 📅 Último mes
- 📊 Últimos 3 meses
- 📈 Año completo
- 🎯 Rango personalizado

**2. 🔍 Segmentación**
- **👤 Por Repartidor:** Análisis individual
- **🏷️ Por Motivo:** Causas específicas
- **📦 Por Producto:** Items problemáticos
- **🏪 Por Zona:** Áreas geográficas

#### **Exportación y Compartir:**

**1. 📄 Formatos Disponibles**
- **📊 Excel:** Datos para análisis
- **📄 PDF:** Reporte ejecutivo
- **📈 PowerPoint:** Presentación
- **📧 Email:** Envío automático

**2. 📧 Distribución Automática**
- **📅 Programada:** Reportes periódicos
- **👥 Lista Distribución:** Stakeholders clave
- **⚠️ Alertas:** Cuando excede límites

---

## 🔧 **FLUJOS DE TRABAJO CRÍTICOS**

### **Flujo Completo de Venta**

```
1. 🛒 Crear Venta
   ↓
2. 👤 Registrar Cliente
   ↓
3. 📦 Verificar Stock
   ↓
4. 💰 Procesar Pago
   ↓
5. 📋 Generar Pedido
   ↓
6. 🏪 Alistar en Bodega
   ↓
7. 🚚 Asignar Repartidor
   ↓
8. 📍 Optimizar Ruta
   ↓
9. 🚛 Realizar Entrega
   ↓
10. ✅ Confirmar Recepción
```

### **Flujo de Devolución**

```
1. 🚚 Intento de Entrega Fallido
   ↓
2. 📱 Registrar Motivo en App
   ↓
3. 💾 Sistema Crea Devolución
   ↓
4. 🔄 Repartidor Retorna a Base
   ↓
5. 📦 Bodeguero Recibe Productos
   ↓
6. ✅ Confirmar Recepción
   ↓
7. 📊 Actualizar Stock
   ↓
8. 📈 Generar Reportes
```

### **Flujo de Gestión de Stock**

```
1. ⚠️ Alerta de Stock Bajo
   ↓
2. 📋 Revisar Necesidades
   ↓
3. 🛒 Crear Orden de Compra
   ↓
4. 📤 Enviar a Proveedor
   ↓
5. 📦 Recibir Mercancía
   ↓
6. ✅ Verificar Calidad
   ↓
7. 📊 Actualizar Inventario
   ↓
8. 💰 Procesar Factura
```

---

## 🆘 **SOLUCIÓN DE PROBLEMAS COMUNES**

### **Problemas de Acceso**

**❌ No puedo iniciar sesión**
- ✅ Verificar usuario y contraseña
- ✅ Confirmar que la cuenta esté activa
- ✅ Contactar administrador para reset

**❌ No veo ciertos módulos**
- ✅ Verificar permisos asignados
- ✅ Confirmar grupo de usuario correcto
- ✅ Solicitar permisos adicionales

### **Problemas de Inventario**

**❌ Stock negativo**
- ✅ Revisar últimos movimientos
- ✅ Verificar transferencias pendientes
- ✅ Hacer ajuste de inventario

**❌ Productos duplicados**
- ✅ Verificar SKU único
- ✅ Consolidar productos similares
- ✅ Actualizar referencias

### **Problemas de Ventas**

**❌ No se puede facturar**
- ✅ Verificar stock disponible
- ✅ Confirmar datos del cliente
- ✅ Revisar configuración de facturación

**❌ Error en cálculos**
- ✅ Verificar precios de productos
- ✅ Revisar configuración de impuestos
- ✅ Confirmar descuentos aplicados

---

## 📞 **SOPORTE TÉCNICO**

### **Contactos de Emergencia**

**🔧 Soporte Técnico:** [email/teléfono]
**👨‍💼 Administrador Sistema:** [contacto]
**📋 Manual Actualizado:** [fecha última actualización]

### **Recursos Adicionales**

**📚 Documentación Técnica:** [ubicación]
**🎥 Videos Tutoriales:** [enlaces]
**💬 Chat de Soporte:** [sistema interno]

---

**📝 Nota:** Este manual debe actualizarse regularmente conforme evolucione el sistema. Versión actual compatible con GRSYS v2024.

**🔄 Última Actualización:** Octubre 2025