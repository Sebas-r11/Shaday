import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from django.test import Client
from accounts.models import User
from ventas.models import Cliente, Pedido, Factura
from inventario.models import Producto
from decimal import Decimal

print('🔍 VALIDACIÓN DE FLUJOS DE TRABAJO COMPLETOS')
print('=' * 60)

# Autenticar como admin
client = Client()
user = User.objects.filter(is_superuser=True).first()
client.force_login(user)
print(f'✅ Usuario autenticado: {user.username}')

print()
print('🎯 PROBANDO FLUJO COMPLETO: Cliente → Pedido → Factura → PDF')
print('-' * 60)

success_steps = 0
total_steps = 7

# PASO 1: Verificar datos existentes
print('📋 PASO 1: Verificando datos existentes')
clientes = Cliente.objects.all()
productos = Producto.objects.all()
pedidos = Pedido.objects.all()
facturas = Factura.objects.all()

print(f'   📊 Clientes: {clientes.count()}')
print(f'   📦 Productos: {productos.count()}')
print(f'   📋 Pedidos: {pedidos.count()}')
print(f'   🧾 Facturas: {facturas.count()}')

if clientes.exists() and productos.exists():
    print('   ✅ Datos base disponibles para flujo completo')
    success_steps += 1
else:
    print('   ❌ Faltan datos base para el flujo')

# PASO 2: Crear nuevo cliente programáticamente
print()
print('📋 PASO 2: Creando nuevo cliente')
try:
    nuevo_cliente = Cliente.objects.create(
        tipo_documento='CC',
        numero_documento='99887766',
        nombre_completo='Cliente Flujo Completo SAS',
        telefono='3001112233',
        direccion='Av. Principal #123-456',
        ciudad='Bogotá',
        tipo_cliente='mayorista',
        limite_credito=Decimal('50000.00'),
        dias_credito=30
    )
    print(f'   ✅ Cliente creado: {nuevo_cliente.nombre_completo} (ID: {nuevo_cliente.id})')
    success_steps += 1
except Exception as e:
    print(f'   ❌ Error creando cliente: {str(e)[:60]}...')

# PASO 3: Crear nuevo pedido programáticamente
print()
print('📋 PASO 3: Creando nuevo pedido')
try:
    if 'nuevo_cliente' in locals():
        nuevo_pedido = Pedido.objects.create(
            numero=f'PED-FLUJO-{nuevo_cliente.id}',
            cliente=nuevo_cliente,
            estado='pendiente',
            total=Decimal('25000.00'),
            asignado_a=user
        )
        print(f'   ✅ Pedido creado: {nuevo_pedido.numero} (ID: {nuevo_pedido.id})')
        success_steps += 1
    else:
        print('   ❌ No se pudo crear pedido (cliente no disponible)')
except Exception as e:
    print(f'   ❌ Error creando pedido: {str(e)[:60]}...')

# PASO 4: Agregar items al pedido
print()
print('📋 PASO 4: Agregando items al pedido')
try:
    if 'nuevo_pedido' in locals() and productos.exists():
        from ventas.models import ItemPedido
        producto_test = productos.first()
        
        item_pedido = ItemPedido.objects.create(
            pedido=nuevo_pedido,
            producto=producto_test,
            cantidad=5,
            precio_unitario=Decimal('5000.00')
        )
        print(f'   ✅ Item agregado al pedido (Cantidad: {item_pedido.cantidad})')
        success_steps += 1
    else:
        print('   ❌ No se pueden agregar items (pedido o productos no disponibles)')
except Exception as e:
    print(f'   ❌ Error agregando items: {str(e)[:60]}...')

# PASO 5: Convertir pedido a factura
print()
print('📋 PASO 5: Convirtiendo pedido a factura')
try:
    if 'nuevo_pedido' in locals():
        nueva_factura = Factura.objects.create(
            numero=f'FACT-FLUJO-{nuevo_pedido.id}',
            cliente=nuevo_pedido.cliente,
            estado='pendiente',
            total=nuevo_pedido.total
        )
        print(f'   ✅ Factura creada: {nueva_factura.numero} (ID: {nueva_factura.id})')
        success_steps += 1
    else:
        print('   ❌ No se pudo crear factura (pedido no disponible)')
except Exception as e:
    print(f'   ❌ Error creando factura: {str(e)[:60]}...')

# PASO 6: Generar PDF del pedido
print()
print('📋 PASO 6: Generando PDF del pedido')
try:
    if 'nuevo_pedido' in locals():
        url_pdf_pedido = f'/ventas/pedidos/{nuevo_pedido.id}/imprimir/'
        response = client.get(url_pdf_pedido)
        
        if response.status_code == 200 and response.get('Content-Type', '').startswith('application/pdf'):
            print(f'   ✅ PDF pedido generado correctamente ({len(response.content)} bytes)')
            success_steps += 1
        else:
            print(f'   ❌ Error generando PDF pedido: Status {response.status_code}')
    else:
        print('   ❌ No se puede generar PDF (pedido no disponible)')
except Exception as e:
    print(f'   ❌ Error en PDF pedido: {str(e)[:60]}...')

# PASO 7: Generar PDF de la factura
print()
print('📋 PASO 7: Generando PDF de la factura')
try:
    if 'nueva_factura' in locals():
        url_pdf_factura = f'/ventas/facturas/{nueva_factura.id}/imprimir/'
        response = client.get(url_pdf_factura)
        
        if response.status_code == 200 and response.get('Content-Type', '').startswith('application/pdf'):
            print(f'   ✅ PDF factura generado correctamente ({len(response.content)} bytes)')
            success_steps += 1
        else:
            print(f'   ❌ Error generando PDF factura: Status {response.status_code}')
    else:
        print('   ❌ No se puede generar PDF (factura no disponible)')
except Exception as e:
    print(f'   ❌ Error en PDF factura: {str(e)[:60]}...')

print()
print('📊 RESUMEN DEL FLUJO COMPLETO:')
print('=' * 40)
print(f'✅ Pasos completados: {success_steps}/{total_steps}')
print(f'📈 Éxito del flujo: {(success_steps/total_steps)*100:.1f}%')

if success_steps >= total_steps * 0.9:
    print('🎉 ¡FLUJO DE TRABAJO COMPLETAMENTE FUNCIONAL!')
elif success_steps >= total_steps * 0.7:
    print('✅ Flujo de trabajo en buen estado')
elif success_steps >= total_steps * 0.5:
    print('⚠️ Flujo de trabajo con problemas menores')
else:
    print('❌ Flujo de trabajo requiere atención')

# Mostrar IDs para referencia futura
if 'nuevo_cliente' in locals():
    print(f'📝 Cliente ID: {nuevo_cliente.id} - {nuevo_cliente.nombre_completo}')
if 'nuevo_pedido' in locals():
    print(f'📝 Pedido ID: {nuevo_pedido.id} - {nuevo_pedido.numero}')
if 'nueva_factura' in locals():
    print(f'📝 Factura ID: {nueva_factura.id} - {nueva_factura.numero}')

print()
print('🔧 PRÓXIMOS PASOS:')
print('   □ Verificar permisos por roles')
print('   □ Validar sistema de inventario')
print('   □ Comprobar integridad de datos')