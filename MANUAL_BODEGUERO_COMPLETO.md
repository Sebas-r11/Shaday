# 📦 MANUAL COMPLETO DEL BODEGUERO
**Sistema de Gestión Empresarial GRSYS**

---

## 🎯 **ÍNDICE DE CONTENIDOS**

1. [Inicio de Sesión y Dashboard](#inicio-de-sesión-y-dashboard)
2. [Gestión de Inventario](#gestión-de-inventario)
3. [Recepción de Mercancía](#recepción-de-mercancía)
4. [Alistamiento de Pedidos](#alistamiento-de-pedidos)
5. [Transferencias entre Bodegas](#transferencias-entre-bodegas)
6. [Control de Stock](#control-de-stock)
7. [Gestión de Devoluciones](#gestión-de-devoluciones)
8. [Reportes de Bodega](#reportes-de-bodega)
9. [Solución de Problemas](#solución-de-problemas)

---

## 🔐 **INICIO DE SESIÓN Y DASHBOARD**

### **Acceso al Sistema**

**🔗 URL de Acceso:** `[dominio-empresa]/accounts/login/`

#### **Proceso de Login:**

**1. 📝 Formulario de Ingreso**
- **👤 Usuario:** Su nombre de usuario asignado
- **🔑 Contraseña:** Clave personal (cambiarla en primer uso)
- **🔐 Ingresar:** Click en botón "Iniciar Sesión"

**⚠️ Recordatorio:**
- Cerrar sesión al terminar el turno
- No compartir credenciales con otros usuarios
- Reportar problemas de acceso inmediatamente

### **Dashboard del Bodeguero**

**📊 Vista Principal tras el Login**

#### **Widgets Informativos:**

**1. 📦 Estado General del Inventario**
- **📊 Total Productos:** Cantidad de SKUs activos
- **💰 Valor Inventario:** Monto total en stock
- **⚠️ Alertas Stock:** Productos bajo mínimo
- **🔄 Movimientos Hoy:** Entradas y salidas del día

**2. 📋 Pedidos para Alistar**
- **⏳ Pendientes:** Órdenes esperando preparación
- **👷 En Proceso:** Pedidos siendo alistados
- **✅ Completados Hoy:** Órdenes terminadas
- **🎯 Meta Diaria:** Objetivo de alistamiento

**3. 🚚 Entregas del Día**
- **📦 Listos para Envío:** Pedidos preparados
- **🚛 En Ruta:** Enviados con repartidores
- **✅ Entregados:** Confirmados por clientes
- **🔄 Devueltos:** Retornados a bodega

**4. ⚠️ Alertas Críticas**
- **📉 Stock Agotado:** Productos sin existencias
- **⏰ Órdenes Urgentes:** Pedidos con alta prioridad
- **🔍 Discrepancias:** Diferencias en inventario
- **📅 Vencimientos:** Productos próximos a caducar

#### **Accesos Rápidos:**

**Botones de Acción Inmediata:**
- **📥 Recibir Mercancía:** Registrar entrada de productos
- **📋 Alistar Pedidos:** Ver órdenes pendientes
- **🔄 Movimiento Rápido:** Entrada/salida express
- **📊 Consultar Stock:** Verificar disponibilidad

---

## 📦 **GESTIÓN DE INVENTARIO**

### **Consulta de Productos**

**🔗 Acceso:** Inventario → Productos

#### **Vista Principal:**

**1. 📋 Lista de Productos**
- **📦 Nombre:** Descripción del producto
- **🔤 SKU:** Código único identificador
- **📁 Categoría:** Clasificación del producto
- **📊 Stock Actual:** Cantidad disponible
- **📍 Ubicación:** Sector/estante en bodega
- **⚠️ Stock Mínimo:** Nivel de alerta

**2. 🔍 Herramientas de Búsqueda**
- **🔤 Buscar por Nombre:** Campo de texto libre
- **📊 Buscar por SKU:** Código específico
- **📁 Filtrar por Categoría:** Tipo de producto
- **⚠️ Solo con Alertas:** Productos bajo mínimo
- **📍 Por Ubicación:** Sector específico de bodega

#### **Botones de Acción por Producto:**

**1. 👁️ Ver Detalle**
- **📊 Stock por Bodega:** Si hay múltiples ubicaciones
- **📈 Historial Movimientos:** Entradas y salidas recientes
- **📍 Ubicación Exacta:** Estante/sector específico
- **📅 Última Actualización:** Cuándo se modificó

**2. 🔄 Movimiento Rápido**
- **📥 Entrada:** Agregar stock rápidamente
- **📤 Salida:** Descontar por ajuste o daño
- **📝 Observaciones:** Comentarios del movimiento
- **📅 Fecha/Hora:** Automática o manual

**3. 📍 Cambiar Ubicación**
- **🗺️ Mapa de Bodega:** Vista gráfica de sectores
- **📝 Nueva Ubicación:** Seleccionar sector/estante
- **✅ Confirmar Cambio:** Actualizar ubicación
- **📋 Registro:** Mantener historial de cambios

### **Stock por Bodega**

**🔗 Acceso:** Inventario → Stock

#### **Vista Consolidada:**

**1. 📊 Información por Producto**
- **🏪 Bodega Principal:** Stock en almacén central
- **🚚 Bodega Móvil:** Inventario con repartidores
- **🏢 Otras Sucursales:** Si hay múltiples locaciones
- **📊 Total Sistema:** Suma de todas las ubicaciones

**2. 🔍 Filtros Avanzados**
- **🏪 Por Bodega:** Solo una ubicación específica
- **⚠️ Solo Alertas:** Productos bajo mínimo
- **📊 Sin Stock:** Productos agotados
- **💰 Por Valor:** Productos de alto/bajo costo

#### **Acciones de Stock:**

**📊 Consultar Detalle**
- **📈 Gráfico Histórico:** Tendencia de stock
- **📅 Proyección:** Cuándo se agotará
- **🔄 Movimientos Recientes:** Últimas transacciones
- **📋 Pedidos Pendientes:** Comprometido en órdenes

**⚠️ Configurar Alertas**
- **📉 Stock Mínimo:** Nivel de alerta
- **📈 Stock Máximo:** Nivel de sobrestock
- **📧 Notificaciones:** Email automático
- **👥 Destinatarios:** Quién debe ser notificado

---

## 📥 **RECEPCIÓN DE MERCANCÍA**

### **Registro de Entradas**

**🔗 Acceso:** Inventario → Movimientos → "📥 Nueva Entrada"

#### **Tipos de Entrada:**

**1. 🛒 Compra a Proveedor**
- **🏢 Seleccionar Proveedor:** De lista predefinida
- **📄 Número Factura:** Documento del proveedor
- **📅 Fecha Recepción:** Cuándo llegó la mercancía
- **👤 Recibido por:** Su nombre como responsable

**2. 🔄 Transferencia de Otra Bodega**
- **🏪 Bodega Origen:** De dónde viene
- **📄 Número Transferencia:** Documento de envío
- **🚚 Transportista:** Quién trajo la mercancía
- **📦 Estado Mercancía:** Condición al llegar

**3. ⚖️ Ajuste de Inventario**
- **📊 Diferencia Encontrada:** Sobrante en conteo
- **📝 Motivo Ajuste:** Razón de la diferencia
- **👁️ Supervisor:** Quien autoriza el ajuste
- **📄 Documento Soporte:** Evidencia del ajuste

#### **Proceso de Recepción:**

**Paso 1: 📋 Información General**
- **📅 Fecha y Hora:** Cuándo se recibe
- **👤 Responsable:** Su usuario como receptor
- **🏪 Bodega Destino:** Dónde se almacena
- **📝 Observaciones:** Comentarios generales

**Paso 2: 📦 Agregar Productos**
- **🔍 Buscar Producto:** Por nombre o SKU
- **🔢 Cantidad Recibida:** Unidades que llegan
- **💰 Costo Unitario:** Precio de compra
- **📅 Fecha Vencimiento:** Si aplica
- **📍 Ubicación:** Dónde se almacena

**Paso 3: ✅ Verificación**
- **📊 Resumen Total:** Cantidad y valor
- **🔍 Revisar Items:** Verificar cada producto
- **📝 Observaciones Finales:** Comentarios especiales
- **✅ Confirmar Recepción:** Procesar entrada

#### **Botones Durante Recepción:**

**🔄 Gestión de Items**
- **➕ Agregar Producto:** Incluir más items
- **✏️ Editar Cantidad:** Modificar unidades
- **❌ Eliminar Item:** Quitar de la lista
- **📋 Duplicar:** Copiar item similar

**📊 Validaciones**
- **🔍 Verificar Precios:** Comparar con histórico
- **📊 Calcular Totales:** Suma automática
- **⚠️ Alertas Stock:** Notificar si excede máximos
- **💾 Guardar Borrador:** Continuar después

### **Control de Calidad**

#### **Inspección de Mercancía:**

**✅ Estado de Productos**
- **🆕 Nuevo/Perfecto:** Condición óptima
- **⚠️ Con Observaciones:** Pequeños defectos
- **❌ Dañado:** No apto para venta
- **🔄 Requiere Devolución:** Retornar al proveedor

**📝 Registro de Incidencias**
- **📷 Tomar Fotos:** Evidencia de daños
- **📝 Descripción Detallada:** Qué está mal
- **👨‍💼 Notificar Supervisor:** Escalar problema
- **📄 Crear Reclamo:** Documento formal

#### **Acciones por Estado:**

**✅ Productos Conformes**
- **📦 Almacenar Normalmente:** En ubicación asignada
- **📊 Actualizar Stock:** Sumar al inventario
- **✅ Marcar Disponible:** Para venta inmediata

**⚠️ Productos con Observaciones**
- **🏷️ Etiquetar:** Marcar condición especial
- **📍 Área Especial:** Zona de productos observados
- **👨‍💼 Decidir Destino:** Vender, devolver o ajustar precio

**❌ Productos Dañados**
- **🚫 No Ingresar:** No sumar al stock
- **📝 Documento Reclamo:** Crear nota de crédito
- **📦 Separar:** Área de productos defectuosos
- **🔄 Gestionar Devolución:** Proceso con proveedor

---

## 📋 **ALISTAMIENTO DE PEDIDOS**

### **Lista de Pedidos Pendientes**

**🔗 Acceso:** Ventas → Pedidos → "📦 Para Alistar"

#### **Vista de Trabajo:**

**1. 📊 Filtros de Prioridad**
- **🔥 Urgentes:** Pedidos con entrega inmediata
- **📅 Programados Hoy:** Para entrega hoy
- **📅 Mañana:** Preparar para día siguiente
- **🎯 Por Zona:** Agrupar por área de entrega

**2. 📋 Información por Pedido**
- **📄 Número:** Identificador único
- **👤 Cliente:** Nombre y contacto
- **📍 Dirección:** Lugar de entrega
- **⏰ Hora Límite:** Cuándo debe estar listo
- **📦 Cantidad Items:** Productos a alistar
- **👤 Vendedor:** Quien tomó el pedido

#### **Estados de Alistamiento:**

**📝 Pendiente**
- **⏰ Recién Asignado:** Esperando iniciar
- **👷 Sin Asignar:** Necesita bodeguero
- **📦 Productos Listos:** Items disponibles

**👷 En Proceso**
- **👤 Asignado a:** Su nombre como responsable
- **📊 Progreso:** Porcentaje completado
- **⏰ Tiempo Transcurrido:** Cuánto lleva

**✅ Completado**
- **📦 Listo para Envío:** Empacado y etiquetado
- **👤 Completado por:** Quien lo terminó
- **⏰ Tiempo Total:** Duración del alistamiento

### **Proceso de Alistamiento**

#### **Iniciar Alistamiento:**

**1. ▶️ Tomar Pedido**
- **👁️ Ver Detalle:** Lista completa de productos
- **✅ Aceptar:** Asignarse el pedido
- **⏰ Tiempo Estimado:** Sistema calcula duración
- **📍 Ruta Sugerida:** Orden óptimo de recolección

**2. 📦 Lista de Productos**
- **📦 Producto:** Nombre y descripción
- **🔢 Cantidad:** Unidades solicitadas
- **📍 Ubicación:** Dónde encontrarlo
- **✅ Estado:** Pendiente/Completado

#### **Botones Durante Alistamiento:**

**✅ Completar Item**
- **🔢 Confirmar Cantidad:** Validar unidades
- **📦 Marcar Alistado:** Item completado
- **📝 Observaciones:** Si hay algún problema
- **📷 Foto:** Evidencia si es necesario

**⚠️ Reportar Problema**
- **❌ Stock Insuficiente:** No hay cantidad completa
- **📦 Producto Dañado:** Item en mal estado
- **❓ No Encontrado:** No está en ubicación
- **🔄 Producto Sustituto:** Ofrecer alternativa

**💾 Guardar Progreso**
- **⏸️ Pausar:** Continuar después
- **🔄 Cambiar Asignación:** Reasignar a otro bodeguero
- **📞 Solicitar Ayuda:** Pedir asistencia

#### **Finalizar Alistamiento:**

**📦 Empaque y Etiquetado**
- **📦 Verificar Contenido:** Revisar todos los items
- **🏷️ Etiqueta Cliente:** Nombre y dirección
- **📄 Lista Empaque:** Relación de productos
- **✅ Sellar/Cerrar:** Asegurar el paquete

**🚚 Preparar para Envío**
- **📍 Zona de Despacho:** Mover a área de salida
- **📅 Programar Entrega:** Asignar fecha/hora
- **👤 Asignar Repartidor:** Si ya está definido
- **📱 Notificar Cliente:** Envío automático

### **Gestión de Incidencias**

#### **Problemas Comunes:**

**❌ Stock Insuficiente**
- **📊 Verificar Disponibilidad:** Confirmar en sistema
- **🔍 Buscar en Otras Ubicaciones:** Revisar otras áreas
- **📞 Contactar Vendedor:** Informar situación
- **🔄 Producto Sustituto:** Sugerir alternativa

**📦 Producto Dañado**
- **📷 Fotografiar:** Evidencia del daño
- **🚫 No Incluir:** Separar del pedido
- **📝 Reportar:** Notificar al sistema
- **🔄 Buscar Reemplazo:** Unidad en buen estado

**❓ Producto No Encontrado**
- **🔍 Búsqueda Exhaustiva:** Revisar toda la bodega
- **📊 Verificar Sistema:** Confirmar ubicación registrada
- **👥 Preguntar Colegas:** Verificar con otros bodegueros
- **📞 Escalar Problema:** Notificar supervisor

---

## 🔄 **TRANSFERENCIAS ENTRE BODEGAS**

### **Crear Transferencia**

**🔗 Acceso:** Inventario → Transferencias → "➡️ Nueva Transferencia"

#### **Configuración Inicial:**

**1. 🏪 Bodegas Involucradas**
- **📤 Bodega Origen:** De dónde sale
- **📥 Bodega Destino:** Hacia dónde va
- **👤 Responsable Envío:** Su usuario
- **👤 Responsable Recepción:** Quien recibe

**2. 📅 Programación**
- **📅 Fecha Transferencia:** Cuándo se envía
- **⏰ Hora:** Momento específico
- **🚚 Método Transporte:** Vehículo/transportista
- **📝 Motivo:** Razón de la transferencia

#### **Agregar Productos:**

**🔍 Selección de Items**
- **📦 Buscar Producto:** Por nombre o SKU
- **📊 Stock Disponible:** Cantidad en bodega origen
- **🔢 Cantidad a Transferir:** Unidades a enviar
- **📍 Ubicación Origen:** Dónde está actualmente

**✅ Validaciones**
- **📊 Stock Suficiente:** Verificar disponibilidad
- **🚫 Productos Reservados:** Considerar comprometidos
- **⚠️ Stock Mínimo:** No dejar bajo límite
- **💰 Valor Total:** Cálculo automático

#### **Botones de Gestión:**

**📦 Gestión de Items**
- **➕ Agregar Más:** Incluir otros productos
- **✏️ Editar Cantidad:** Modificar unidades
- **❌ Eliminar:** Quitar producto de transferencia
- **📋 Duplicar:** Copiar configuración similar

**📊 Controles**
- **🔄 Recalcular:** Actualizar totales
- **💾 Guardar Borrador:** Continuar después
- **👁️ Vista Previa:** Ver documento antes de confirmar
- **✅ Confirmar:** Procesar transferencia

### **Procesar Envío**

#### **Preparación de Mercancía:**

**📦 Alistamiento**
- **📋 Lista de Transferencia:** Productos a enviar
- **🔍 Verificar Items:** Confirmar cada producto
- **📦 Empacar:** Preparar para transporte
- **🏷️ Etiquetar:** Bodega destino y contenido

**📄 Documentación**
- **📋 Generar Guía:** Documento de transferencia
- **📝 Observaciones:** Comentarios especiales
- **👤 Firmas:** Responsables de envío
- **📅 Fecha/Hora Real:** Momento de salida

#### **Confirmar Envío:**

**🚚 Despacho**
- **✅ Mercancía Verificada:** Todo correcto
- **🚛 Vehículo Asignado:** Transporte confirmado
- **👤 Conductor:** Responsable del traslado
- **📱 Contacto:** Teléfono para seguimiento

**📊 Actualización de Stock**
- **📤 Descontar Origen:** Reducir stock bodega emisora
- **🔄 Estado "En Tránsito":** Mercancía en movimiento
- **📧 Notificar Destino:** Avisar a bodega receptora
- **📊 Actualizar Sistema:** Registros automáticos

### **Recibir Transferencia**

#### **Notificación de Llegada:**

**📥 Transferencia Pendiente**
- **🔔 Alerta Sistema:** Notificación automática
- **📋 Detalle Envío:** Qué debe llegar
- **👤 Quien Envía:** Bodega y responsable origen
- **📅 Fecha Programada:** Cuándo debe llegar

#### **Proceso de Recepción:**

**📦 Verificación Física**
- **📋 Lista de Verificación:** Productos esperados
- **🔢 Contar Unidades:** Confirmar cantidades
- **👁️ Inspeccionar Estado:** Verificar condición
- **📝 Registrar Diferencias:** Si hay faltantes/sobrantes

**✅ Confirmar Recepción**
- **📊 Cantidades Correctas:** Todo conforme
- **⚠️ Reportar Diferencias:** Si hay discrepancias
- **📅 Fecha/Hora Real:** Momento de recepción
- **👤 Recibido por:** Su firma como responsable

#### **Botones de Recepción:**

**✅ Recepción Completa**
- **📦 Todo Conforme:** Recibir toda la transferencia
- **📊 Actualizar Stock:** Sumar al inventario
- **✅ Cerrar Transferencia:** Completar proceso
- **📧 Notificar Origen:** Confirmar recepción

**⚠️ Recepción Parcial**
- **🔢 Cantidad Recibida:** Unidades realmente llegadas
- **📝 Motivo Diferencia:** Razón del faltante
- **🔄 Transferencia Pendiente:** Mantener abierta
- **📞 Contactar Origen:** Coordinar completar

**❌ Rechazar Transferencia**
- **📝 Motivo Rechazo:** Por qué no se acepta
- **🔄 Devolver Mercancía:** Retornar a origen
- **📄 Documento Rechazo:** Evidencia formal
- **📧 Notificar Sistema:** Actualizar estados

---

## 📊 **CONTROL DE STOCK**

### **Inventario Físico**

**🔗 Acceso:** Inventario → "📊 Inventario Físico"

#### **Preparación del Conteo:**

**1. 📅 Programar Inventario**
- **📅 Fecha:** Cuándo realizar el conteo
- **⏰ Hora Inicio:** Momento de comenzar
- **🏪 Área/Sector:** Qué zona contar
- **👥 Responsables:** Quiénes participan

**2. 🔒 Congelar Movimientos**
- **⏸️ Pausar Operaciones:** No más entradas/salidas
- **📊 Estado Actual:** Snapshot del sistema
- **🔔 Notificar Equipo:** Avisar sobre inventario
- **📋 Imprimir Listas:** Formatos de conteo

#### **Proceso de Conteo:**

**📋 Lista de Conteo**
- **📦 Producto:** Nombre y SKU
- **📍 Ubicación:** Dónde debe estar
- **📊 Stock Sistema:** Cantidad registrada
- **🔢 Conteo Físico:** Campo para anotar realidad
- **📝 Observaciones:** Comentarios especiales

**🔍 Conteo por Sectores**
- **📍 Área Asignada:** Zona específica de responsabilidad
- **📦 Producto por Producto:** Revisión sistemática
- **🔢 Anotar Cantidades:** Registrar lo encontrado
- **❓ Marcar Dudas:** Items para revisar

#### **Botones Durante Conteo:**

**📱 Registro Digital**
- **🔤 Buscar SKU:** Localizar producto rápidamente
- **🔢 Ingresar Cantidad:** Anotar conteo real
- **📝 Agregar Nota:** Observaciones importantes
- **✅ Confirmar Item:** Marcar como contado

**🔍 Herramientas de Conteo**
- **📊 Ver Diferencias:** Comparar sistema vs físico
- **⚠️ Alertar Discrepancias:** Diferencias significativas
- **📷 Fotografiar:** Evidencia de problemas
- **🔄 Recontar:** Verificar items dudosos

### **Ajustes de Inventario**

#### **Análisis de Diferencias:**

**📊 Reporte de Discrepancias**
- **📈 Sobrantes:** Más físico que sistema
- **📉 Faltantes:** Menos físico que sistema
- **💰 Valor Impacto:** Monto de las diferencias
- **📊 % Diferencia:** Porcentaje de variación

**🔍 Investigación**
- **📅 Revisar Movimientos:** Transacciones recientes
- **👥 Consultar Equipo:** Verificar con colegas
- **📄 Buscar Documentos:** Evidencia de movimientos
- **🔄 Recontar Items:** Verificar conteo dudoso

#### **Procesar Ajustes:**

**✅ Ajustes Aprobados**
- **📈 Entrada por Sobrante:** Registrar stock adicional
- **📉 Salida por Faltante:** Descontar diferencias
- **📝 Motivo Ajuste:** Explicación de la diferencia
- **👨‍💼 Autorización:** Supervisor que aprueba

**📄 Documentación**
- **📋 Acta de Inventario:** Documento oficial
- **👥 Firmas:** Responsables del proceso
- **📅 Fecha/Hora:** Momento del ajuste
- **💰 Impacto Financiero:** Valor de ajustes

#### **Botones de Ajuste:**

**📊 Procesar Diferencias**
- **✅ Ajustar Automático:** Aplicar todas las diferencias
- **🔍 Revisar Item por Item:** Ajuste selectivo
- **❌ Descartar Menores:** Ignorar diferencias pequeñas
- **📧 Notificar Gerencia:** Reportar ajustes significativos

### **Alertas de Stock**

#### **Configuración de Alertas:**

**⚠️ Niveles de Alerta**
- **📉 Stock Mínimo:** Nivel de reorden
- **📈 Stock Máximo:** Límite de sobrestock
- **❌ Sin Stock:** Productos agotados
- **📅 Próximo Vencimiento:** Items con fecha límite

**🔔 Tipos de Notificación**
- **📧 Email:** Correo automático
- **📱 SMS:** Mensaje de texto
- **🔔 Sistema:** Notificación en pantalla
- **📊 Dashboard:** Widget de alertas

#### **Gestión de Alertas:**

**📋 Lista de Alertas Activas**
- **📦 Producto:** Item con alerta
- **⚠️ Tipo Alerta:** Qué tipo de problema
- **📊 Stock Actual:** Cantidad disponible
- **📅 Desde:** Cuándo se activó la alerta
- **🎯 Acción Requerida:** Qué hacer

**🔄 Acciones Correctivas**
- **🛒 Generar Orden Compra:** Solicitar reposición
- **📞 Contactar Proveedor:** Llamar para urgente
- **🔄 Transferir Stock:** Traer de otra bodega
- **💰 Ajustar Precios:** Promocionar para rotar

---

## 🔄 **GESTIÓN DE DEVOLUCIONES**

### **Recepción de Devoluciones**

**🔗 Acceso:** Inventario → Devoluciones → "📥 Recibir Devoluciones"

#### **Lista de Devoluciones Pendientes:**

**📋 Vista Principal**
- **📄 Número Devolución:** Identificador único
- **👤 Cliente:** Nombre del cliente
- **🚚 Repartidor:** Quien devuelve
- **📅 Fecha Creación:** Cuándo se registró
- **📦 Cantidad Items:** Productos a recibir
- **💰 Valor Total:** Monto involucrado

**🔍 Filtros de Trabajo**
- **📅 Por Fecha:** Devoluciones del día
- **👤 Por Repartidor:** Filtrar por quien devuelve
- **🏷️ Por Motivo:** Razón de la devolución
- **⏰ Por Urgencia:** Priorizar por tiempo

#### **Estados de Devolución:**

**⏳ Pendiente**
- **🚚 En Ruta:** Repartidor viene con productos
- **📋 Registrada:** Sistema tiene la información
- **⏰ Esperando:** Bodeguero debe procesar

**🔄 Parcial**
- **📦 Algunos Recibidos:** Parte ya procesada
- **⏳ Pendientes:** Faltan items por recibir
- **📊 Progreso:** Porcentaje completado

**✅ Completa**
- **📦 Todo Recibido:** Todos los productos procesados
- **📊 Stock Actualizado:** Inventario ya ajustado
- **✅ Cerrada:** Proceso terminado

### **Procesar Devolución Individual**

#### **Ver Detalle de Devolución:**

**1. 👁️ Información General**
- **📄 Número:** Identificador único
- **👤 Cliente:** Datos del cliente original
- **🚚 Repartidor:** Quien efectúa la devolución
- **📍 Dirección:** Donde no se pudo entregar
- **🏷️ Motivo:** Razón de la devolución
- **📅 Fecha/Hora:** Cuándo se creó

**2. 📦 Lista de Productos**
- **📦 Producto:** Nombre y descripción
- **🔢 Cantidad:** Unidades a devolver
- **💰 Precio Unitario:** Valor del producto
- **💰 Subtotal:** Valor total del item
- **🏷️ Estado:** Pendiente/Recibido/Rechazado

#### **Botones de Procesamiento:**

**✅ Recibir Item**
- **🔢 Cantidad a Recibir:** Unidades que llegan
- **👁️ Inspeccionar Estado:** Verificar condición
- **📝 Observaciones:** Comentarios sobre el producto
- **✅ Confirmar Recepción:** Procesar entrada

**❌ Rechazar Item**
- **📝 Motivo Rechazo:** Por qué no se acepta
- **📷 Fotografiar:** Evidencia del problema
- **📧 Notificar:** Avisar a repartidor y administración
- **📄 Documento:** Crear nota de rechazo

**🔄 Recibir Todos**
- **⚡ Procesamiento Masivo:** Todos los items de una vez
- **✅ Confirmación Global:** Un solo botón para todo
- **📊 Actualización Completa:** Stock de todos los productos
- **🎯 Ahorro Tiempo:** Proceso más eficiente

### **Control de Calidad en Devoluciones**

#### **Inspección de Productos Devueltos:**

**🔍 Estados Posibles**
- **🆕 Como Nuevo:** Perfecto estado, puede revenderse
- **⚠️ Con Observaciones:** Pequeños defectos, revisar
- **❌ Dañado:** No apto para venta
- **🗑️ Para Desecho:** Producto perdido totalmente

**📝 Registro de Condición**
- **📷 Fotografiar:** Evidencia del estado
- **📝 Descripción Detallada:** Qué se observa
- **🏷️ Clasificar:** Según estado encontrado
- **📍 Ubicar:** Dónde almacenar según condición

#### **Acciones por Estado:**

**🆕 Productos en Buen Estado**
- **📦 Retornar a Stock:** Agregar al inventario normal
- **📍 Ubicación Normal:** Estante regular
- **✅ Disponible Venta:** Inmediatamente vendible
- **📊 Actualizar Sistema:** Sumar al stock

**⚠️ Productos con Observaciones**
- **🏷️ Etiquetar Especial:** Marcar condición
- **📍 Área Separada:** Zona de productos observados
- **👨‍💼 Revisar con Supervisor:** Decidir destino
- **💰 Posible Descuento:** Vender con rebaja

**❌ Productos Dañados**
- **🚫 No Retornar a Stock:** No sumar al inventario
- **📍 Área de Daños:** Separar físicamente
- **📄 Reportar Pérdida:** Documento contable
- **🗑️ Decidir Destino:** Reparar, donar o desechar

### **Reportes de Devoluciones**

#### **Dashboard de Devoluciones:**

**📊 Métricas Principales**
- **📈 Total Devoluciones:** Cantidad procesada
- **⏳ Pendientes:** Por procesar
- **💰 Valor Involucrado:** Monto total
- **📊 Tasa Recuperación:** % productos recuperables

**📈 Análisis de Tendencias**
- **📅 Por Período:** Devoluciones por día/semana
- **🏷️ Por Motivo:** Principales causas
- **👤 Por Repartidor:** Quién tiene más devoluciones
- **📦 Por Producto:** Items más devueltos

#### **Botones de Reporte:**

**📊 Ver Estadísticas**
- **📈 Gráficos:** Visualización de datos
- **📋 Tablas Detalladas:** Información específica
- **🔍 Filtros:** Personalizar vista
- **📅 Período:** Seleccionar rango de fechas

**📄 Exportar Datos**
- **📊 Excel:** Hoja de cálculo
- **📄 PDF:** Documento imprimible
- **📧 Email:** Enviar por correo
- **📱 WhatsApp:** Compartir rápido

---

## 📊 **REPORTES DE BODEGA**

### **Reportes de Inventario**

**🔗 Acceso:** Reportes → "📦 Inventario"

#### **Tipos de Reportes:**

**📊 Stock Actual**
- **📋 Lista Completa:** Todos los productos
- **💰 Valorización:** Stock valorizado
- **📍 Por Ubicación:** Stock por sector/estante
- **⚠️ Alertas:** Productos bajo mínimo

**🔄 Movimientos**
- **📥 Entradas:** Ingresos de mercancía
- **📤 Salidas:** Despachos y ajustes
- **📊 Resumen:** Totales por período
- **📈 Tendencias:** Análisis temporal

**📋 Rotación**
- **🏆 Más Vendidos:** Productos top
- **🐌 Baja Rotación:** Productos lentos
- **📊 ABC:** Clasificación por importancia
- **💰 Impacto Financiero:** Valor involucrado

#### **Filtros de Reporte:**

**📅 Período**
- **📊 Diario:** Movimientos del día
- **🗓️ Semanal:** Última semana
- **📅 Mensual:** Mes actual
- **📈 Trimestral:** Últimos 3 meses
- **🎯 Personalizado:** Rango específico

**📦 Productos**
- **📁 Por Categoría:** Tipo de producto
- **🏷️ Por Marca:** Fabricante específico
- **👤 Por Proveedor:** Origen de mercancía
- **📍 Por Ubicación:** Sector de bodega

### **Reportes de Productividad**

#### **Rendimiento del Bodeguero:**

**📊 Métricas Personales**
- **📦 Pedidos Alistados:** Cantidad procesada
- **⏰ Tiempo Promedio:** Duración por pedido
- **✅ Precisión:** % sin errores
- **📈 Mejora:** Evolución en el tiempo

**🏆 Comparación con Equipo**
- **📊 Ranking:** Posición entre bodegueros
- **📈 Top Performers:** Mejores del período
- **🎯 Metas:** Objetivos vs logros
- **📚 Oportunidades:** Áreas de mejora

#### **Reportes de Eficiencia:**

**⏰ Tiempos de Proceso**
- **📦 Alistamiento:** Tiempo por pedido
- **📥 Recepción:** Duración por entrada
- **🔄 Transferencias:** Tiempo de procesamiento
- **📊 Inventarios:** Duración de conteos

**🎯 Cumplimiento de Metas**
- **📊 Objetivos Diarios:** Meta vs logrado
- **📈 Tendencia:** Mejora o deterioro
- **🏆 Logros:** Metas alcanzadas
- **⚠️ Alertas:** Cuando está por debajo

### **Exportación y Distribución**

#### **Formatos Disponibles:**

**📊 Excel**
- **📋 Datos Crudos:** Para análisis
- **📈 Gráficos:** Visualización incluida
- **🔍 Filtros:** Funcionalidad de Excel
- **💾 Guardar Local:** Archivo descargable

**📄 PDF**
- **📋 Reporte Ejecutivo:** Presentación formal
- **🖨️ Listo Imprimir:** Formato físico
- **📧 Compartir:** Fácil distribución
- **📱 Ver Móvil:** Compatible dispositivos

#### **Programación Automática:**

**📅 Reportes Programados**
- **🌅 Diarios:** Envío automático cada mañana
- **🗓️ Semanales:** Resumen cada lunes
- **📅 Mensuales:** Reporte fin de mes
- **📧 Destinatarios:** Lista de distribución

**🔔 Alertas Inteligentes**
- **⚠️ Stock Crítico:** Cuando hay problemas
- **📈 Metas Alcanzadas:** Celebrar logros
- **❌ Errores Sistema:** Notificar problemas
- **📊 Cambios Importantes:** Variaciones significativas

---

## 🆘 **SOLUCIÓN DE PROBLEMAS**

### **Problemas de Inventario**

#### **❌ Error: "Stock Negativo"**

**🔍 Causas Posibles:**
- Venta sin stock suficiente
- Error en registro de entradas
- Transferencia no confirmada
- Ajuste incorrecto de inventario

**✅ Soluciones:**
1. **📊 Revisar Movimientos:** Ver últimas transacciones
2. **🔍 Buscar Error:** Identificar movimiento incorrecto
3. **⚖️ Ajuste Manual:** Corregir stock con autorización
4. **📞 Escalar Problema:** Notificar supervisor si persiste

#### **❌ Error: "Producto No Encontrado en Ubicación"**

**🔍 Investigación:**
1. **🔍 Búsqueda Física:** Revisar estantes cercanos
2. **📊 Consultar Sistema:** Ver última ubicación registrada
3. **👥 Preguntar Colegas:** Verificar con otros bodegueros
4. **📱 Revisar Movimientos:** Transacciones recientes

**✅ Acciones:**
1. **📍 Actualizar Ubicación:** Si se encuentra en otro lugar
2. **⚖️ Ajustar Stock:** Si no se encuentra físicamente
3. **📝 Reportar:** Documentar discrepancia
4. **🔄 Proceso Búsqueda:** Establecer protocolo

### **Problemas de Sistema**

#### **❌ "Error de Conexión"**

**✅ Pasos Inmediatos:**
1. **🌐 Verificar Internet:** Comprobar conectividad
2. **🔄 Refrescar Página:** Recargar navegador
3. **💾 Verificar Trabajo:** Comprobar si se guardó
4. **📞 Reportar:** Contactar soporte técnico

#### **❌ "Sesión Expirada"**

**✅ Procedimiento:**
1. **🔐 Volver a Iniciar Sesión:** Reautenticarse
2. **💾 Verificar Borradores:** Revisar trabajo no guardado
3. **⚠️ Prevenir:** Guardar frecuentemente
4. **📱 Configurar Recordatorios:** Alertas para guardar

### **Problemas Operativos**

#### **🚨 Emergencia: Producto Dañado Encontrado**

**⚡ Acción Inmediata:**
1. **🚫 Separar Producto:** Apartar inmediatamente
2. **🏷️ Etiquetar:** Marcar como dañado
3. **📷 Fotografiar:** Evidencia del daño
4. **📝 Reportar:** Notificar supervisor inmediatamente

#### **⚠️ Discrepancia Mayor en Inventario**

**📊 Protocolo:**
1. **🔍 Recontar:** Verificar múltiples veces
2. **👥 Testigo:** Involucrar otro bodeguero
3. **📝 Documentar:** Registrar diferencia exacta
4. **👨‍💼 Escalar:** Notificar gerencia inmediatamente

### **Contactos de Emergencia**

#### **🆘 Soporte Técnico**
- **📞 Interno:** Ext. [número]
- **📧 Email:** soporte@[empresa].com
- **💬 Chat:** Sistema interno
- **⏰ Horario:** 24/7

#### **👨‍💼 Supervisor de Bodega**
- **📞 Directo:** [número supervisor]
- **📧 Email:** bodega@[empresa].com
- **📱 WhatsApp:** [número emergencias]
- **🏢 Oficina:** [ubicación]

#### **🚨 Emergencias**
- **🔥 Seguridad:** [número seguridad]
- **🏥 Primeros Auxilios:** [número primeros auxilios]
- **🚨 Gerencia:** [número gerencia]
- **📞 Línea Directa:** [número emergencia]

---

## 📚 **MEJORES PRÁCTICAS**

### **🎯 Eficiencia en el Trabajo**

#### **Organización Diaria:**

**🌅 Inicio del Turno**
1. **📊 Revisar Dashboard:** Estado general
2. **📅 Ver Agenda:** Tareas programadas
3. **🔔 Revisar Alertas:** Problemas pendientes
4. **📦 Priorizar Urgentes:** Pedidos críticos

**🕐 Durante el Turno**
1. **⏰ Cumplir Horarios:** Entregas programadas
2. **💾 Guardar Frecuentemente:** Evitar pérdida de datos
3. **📝 Documentar Todo:** Mantener registros
4. **🔄 Comunicar Problemas:** Reportar inmediatamente

**🌅 Final del Turno**
1. **📊 Completar Pendientes:** Finalizar tareas
2. **🔐 Cerrar Sesión:** Seguridad del sistema
3. **📝 Reporte Diario:** Resumen de actividades
4. **🧹 Orden Físico:** Mantener bodega organizada

### **🔒 Seguridad y Precisión**

#### **Control de Calidad:**

**✅ Verificaciones Constantes**
- **🔢 Contar Siempre:** No asumir cantidades
- **👁️ Inspeccionar Visual:** Estado de productos
- **📝 Documentar Anomalías:** Registrar problemas
- **🔄 Doble Verificación:** Revisar trabajo importante

**🎯 Precisión en Registros**
- **📊 Datos Exactos:** Cantidades correctas
- **📅 Fechas Precisas:** Momentos exactos
- **📝 Observaciones Clara:** Comentarios útiles
- **👤 Responsabilidad:** Firmar trabajo realizado

### **🤝 Trabajo en Equipo**

#### **Comunicación Efectiva:**

**📞 Reportar Proactivamente**
- **⚠️ Problemas Inmediatos:** No esperar
- **📊 Cambios Importantes:** Informar novedades
- **🆘 Solicitar Ayuda:** Cuando sea necesario
- **💡 Sugerir Mejoras:** Ideas constructivas

**👥 Colaboración**
- **🤝 Apoyar Colegas:** Trabajo en equipo
- **📚 Compartir Conocimiento:** Enseñar a otros
- **🎓 Seguir Aprendiendo:** Capacitación continua
- **🏆 Celebrar Logros:** Reconocer éxitos

---

**📝 Nota:** Este manual debe consultarse regularmente. Manténgase actualizado con nuevas funcionalidades.

**🔄 Última Actualización:** Octubre 2025