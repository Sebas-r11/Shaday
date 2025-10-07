# 🛒 CÓMO CREAR UN PEDIDO DESDE CERO

## 📋 Requisitos Previos

Antes de crear un pedido, necesitas tener:

- ✅ **Cliente existente** en el sistema
- ✅ **Producto(s) existentes** y activos
- ✅ **Bodega configurada** para despacho
- ✅ **Usuario vendedor** con permisos

---

## 🎯 MÉTODO ACTUAL RECOMENDADO (Interfaz Web)

### Opción 1: Via Cotización → Pedido ⭐ **RECOMENDADO**

```
1. 📝 Crear cotización
   └─ http://127.0.0.1:8000/ventas/cotizaciones/nueva/

2. ✅ Llenar datos:
   ├─ Seleccionar cliente
   ├─ Agregar productos
   ├─ Establecer cantidades y precios
   └─ Guardar cotización

3. 🔄 Convertir a pedido:
   ├─ Ir al detalle de la cotización
   └─ Hacer clic en "Convertir a Pedido"

4. ✅ Pedido creado automáticamente
```

**🌟 Ventajas:**
- ✓ Interfaz web completa
- ✓ Validaciones automáticas
- ✓ Trazabilidad total
- ✓ Aprobación del cliente
- ✓ Cálculos automáticos

---

## 🔧 MÉTODO DIRECTO (Código/API)

### Paso a Paso en Django

```python
from ventas.models import Cliente, Pedido, ItemPedido
from inventario.models import Producto, Bodega
from accounts.models import User
from decimal import Decimal

# 1. OBTENER DATOS NECESARIOS
cliente = Cliente.objects.get(id=7)  # ID del cliente
vendedor = User.objects.get(username='admin')  # Usuario vendedor
bodega = Bodega.objects.first()  # Primera bodega disponible

# 2. CREAR EL PEDIDO
pedido = Pedido.objects.create(
    cliente=cliente,
    vendedor=vendedor,
    bodega=bodega,
    estado='borrador',
    observaciones="Pedido creado directamente"
)

# 3. AGREGAR PRODUCTOS
producto1 = Producto.objects.get(id=1)
ItemPedido.objects.create(
    pedido=pedido,
    producto=producto1,
    cantidad=Decimal('2'),
    precio_unitario=producto1.precio_minorista
)

producto2 = Producto.objects.get(id=2)
ItemPedido.objects.create(
    pedido=pedido,
    producto=producto2,
    cantidad=Decimal('1'),
    precio_unitario=producto2.precio_minorista
)

# 4. CALCULAR TOTALES
pedido.calcular_totales()

print(f"Pedido {pedido.numero} creado - Total: ${pedido.total}")
```

---

## 📊 EJEMPLO REAL EJECUTADO

**Resultado del script de demostración:**

```
✅ PEDIDO CREADO EXITOSAMENTE:
   🔢 Número de pedido: 001015
   👤 Cliente: Ana Torres López
   💵 Total: $21,420.00
   📦 Items: 2 productos
   🔄 Estado: borrador

📋 DETALLE DE ITEMS:
   1. Cuaderno Universitario 100 hojas
      📦 Cantidad: 2 × $3,500.00 = $7,000.00
      
   2. Cuaderno Argollado A4  
      📦 Cantidad: 2 × $5,500.00 = $11,000.00

💰 TOTALES:
   Subtotal: $18,000.00
   Impuestos (19% IVA): $3,420.00
   TOTAL: $21,420.00
```

---

## 🔄 Estados del Pedido

| Estado | Descripción | Acciones |
|--------|-------------|----------|
| **📝 borrador** | Pedido en construcción | Editar items, precios |
| **⏳ pendiente** | Confirmado, esperando alistamiento | Reserva stock automática |
| **🔄 proceso** | En alistamiento por bodega | Bodeguero preparando |
| **✅ completado** | Listo para entrega | Crear entrega |
| **❌ cancelado** | Pedido cancelado | Libera stock reservado |

---

## 🌐 URLs Importantes

| Función | URL |
|---------|-----|
| 📋 Lista de pedidos | `/ventas/pedidos/` |
| 📝 Nueva cotización | `/ventas/cotizaciones/nueva/` |
| 👥 Lista de clientes | `/ventas/clientes/` |
| 📦 Lista de productos | `/inventario/productos/` |
| 🏢 Dashboard ventas | `/ventas/` |

---

## ⚠️ Estado Actual del Sistema

### ✅ Funcionalidades Disponibles:
- **Conversión Cotización → Pedido** (Completa)
- **Creación directa por código** (Funcional)
- **Gestión de estados** (Completa)
- **Cálculos automáticos** (Operativo)
- **Reserva de stock** (Automática)

### 📝 Pendientes por Implementar:
- **Vista `PedidoCreateView`** para interfaz web directa
- **Formulario web** para creación de pedidos
- **Template** de creación de pedidos
- **Validación de stock** en tiempo real

---

## 🎯 Recomendación Final

**Para uso inmediato:** Usa el método de **Cotización → Pedido** que está completamente funcional en la interfaz web.

**Para desarrollo futuro:** Implementar la vista directa `PedidoCreateView` para mayor flexibilidad.

**Para automatización:** Usar el método directo por código/API mostrado arriba.

---

## 📞 Soporte

Si necesitas implementar la creación directa de pedidos en la interfaz web, los archivos principales a crear/modificar serían:

1. **`ventas/views.py`** - Agregar `PedidoCreateView`
2. **`ventas/forms.py`** - Crear `PedidoForm`
3. **`templates/ventas/pedido_form.html`** - Template del formulario
4. **`ventas/urls.py`** - Agregar URL para creación

¿Te gustaría que implemente alguna de estas funcionalidades?