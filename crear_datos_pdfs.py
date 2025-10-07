#!/usr/bin/env python
"""
Crear datos de prueba para PDFs y templates básicos
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from datetime import datetime
from decimal import Decimal

def crear_datos_completos_pdf():
    """Crea datos completos necesarios para probar PDFs"""
    print("🛠️ CREANDO DATOS COMPLETOS PARA PDFs")
    
    try:
        from ventas.models import Cliente, Pedido, Factura, ItemPedido
        from inventario.models import Categoria, Subcategoria, Producto
        from accounts.models import User
        
        # 1. Crear usuario vendedor
        vendedor, created = User.objects.get_or_create(
            username='vendedor_pdf',
            defaults={
                'email': 'vendedor@pdf.com',
                'first_name': 'Vendedor',
                'last_name': 'PDF Test'
            }
        )
        if hasattr(vendedor, 'role'):
            vendedor.role = 'vendedor'
            vendedor.save()
        if created:
            print("✅ Usuario vendedor creado")
        
        # 2. Crear categoría y subcategoría
        categoria, created = Categoria.objects.get_or_create(
            nombre='Electrónicos PDF',
            defaults={'activa': True}
        )
        if created:
            print("✅ Categoría creada")
            
        subcategoria, created = Subcategoria.objects.get_or_create(
            nombre='Smartphones PDF',
            categoria=categoria,
            defaults={'activa': True}
        )
        if created:
            print("✅ Subcategoría creada")
        
        # 3. Crear productos
        productos_data = [
            ('PROD-001', 'iPhone 15 Test', 1200.00),
            ('PROD-002', 'Samsung Galaxy Test', 900.00),
            ('PROD-003', 'Xiaomi Test', 400.00),
        ]
        
        productos_creados = []
        for codigo, nombre, precio in productos_data:
            producto, created = Producto.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nombre': nombre,
                    'categoria': categoria,
                    'subcategoria': subcategoria,
                    'precio_minorista': Decimal(str(precio)),
                    'precio_mayorista': Decimal(str(precio * 0.8)),
                    'costo_promedio': Decimal(str(precio * 0.6)),
                    'activo': True
                }
            )
            productos_creados.append(producto)
            if created:
                print(f"✅ Producto {codigo} creado")
        
        # 4. Crear cliente
        cliente, created = Cliente.objects.get_or_create(
            numero_documento='12345678',
            defaults={
                'nombre_completo': 'Cliente Test PDF SA',
                'telefono': '3001234567',
                'direccion': 'Calle 123 #45-67',
                'ciudad': 'Bogotá',
                'activo': True
            }
        )
        if created:
            print("✅ Cliente creado")
        
        # 5. Crear pedido
        pedido, created = Pedido.objects.get_or_create(
            cliente=cliente,
            defaults={
                'numero': 'PED-001',
                'asignado_a': vendedor,
                'estado': 'pendiente',
                'total': Decimal('2500.00')
            }
        )
        if created:
            print("✅ Pedido creado")
            
            # Agregar items al pedido
            for i, producto in enumerate(productos_creados[:2]):  # Solo 2 productos
                ItemPedido.objects.get_or_create(
                    pedido=pedido,
                    producto=producto,
                    defaults={
                        'cantidad': i + 1,
                        'precio_unitario': producto.precio_minorista
                    }
                )
            print("✅ Items de pedido creados")
        
        # 6. Crear factura
        factura, created = Factura.objects.get_or_create(
            cliente=cliente,
            defaults={
                'numero': 'F-001',
                'total': Decimal('2500.00'),
                'estado': 'pendiente'
            }
        )
        if created:
            print("✅ Factura creada")
        
        print(f"\n🎯 DATOS CREADOS EXITOSAMENTE:")
        print(f"📦 Productos: {len(productos_creados)}")
        print(f"👤 Cliente: {cliente.nombre_completo}")
        print(f"📋 Pedido ID: {pedido.id}")
        print(f"🧾 Factura ID: {factura.id}")
        
        return {
            'pedido': pedido,
            'factura': factura,
            'cliente': cliente,
            'productos': productos_creados
        }
        
    except Exception as e:
        print(f"❌ Error creando datos: {e}")
        import traceback
        traceback.print_exc()
        return None

def crear_template_pdf_basico():
    """Crea un template PDF básico para pedidos"""
    print("\n📄 CREANDO TEMPLATE PDF BÁSICO")
    
    # Crear directorio si no existe
    pdf_dir = 'templates/ventas/pdf'
    os.makedirs(pdf_dir, exist_ok=True)
    
    template_pedido = '''{% load static %}
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Pedido #{{ pedido.id }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }
        .info-section { margin-bottom: 20px; }
        .items-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        .items-table th, .items-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .items-table th { background-color: #f2f2f2; }
        .total-section { text-align: right; font-weight: bold; font-size: 18px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>PEDIDO #{{ pedido.id }}</h1>
        <p>Fecha: {{ pedido.fecha_creacion|date:"d/m/Y" }}</p>
    </div>

    <div class="info-section">
        <h3>Información del Cliente</h3>
        <p><strong>Cliente:</strong> {{ pedido.cliente.nombre_completo }}</p>
        <p><strong>Documento:</strong> {{ pedido.cliente.numero_documento }}</p>
        <p><strong>Teléfono:</strong> {{ pedido.cliente.telefono }}</p>
        {% if pedido.cliente.direccion %}
        <p><strong>Dirección:</strong> {{ pedido.cliente.direccion }}</p>
        {% endif %}
    </div>

    <div class="info-section">
        <h3>Detalles del Pedido</h3>
        <p><strong>Estado:</strong> {{ pedido.get_estado_display }}</p>
        <p><strong>Vendedor:</strong> {{ pedido.asignado_a.get_full_name|default:pedido.asignado_a.username }}</p>
        {% if pedido.observaciones %}
        <p><strong>Observaciones:</strong> {{ pedido.observaciones }}</p>
        {% endif %}
    </div>

    <table class="items-table">
        <thead>
            <tr>
                <th>Producto</th>
                <th>Cantidad</th>
                <th>Precio Unit.</th>
                <th>Subtotal</th>
            </tr>
        </thead>
        <tbody>
            {% for item in pedido.items.all %}
            <tr>
                <td>{{ item.producto.codigo }} - {{ item.producto.nombre }}</td>
                <td>{{ item.cantidad }}</td>
                <td>${{ item.precio_unitario|floatformat:2 }}</td>
                <td>${{ item.subtotal|floatformat:2 }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="total-section">
        <p>TOTAL: ${{ pedido.total|floatformat:2 }}</p>
    </div>

    <div style="margin-top: 50px; text-align: center; color: #666;">
        <p>Documento generado automáticamente - {{ "now"|date:"d/m/Y H:i" }}</p>
    </div>
</body>
</html>'''

    # Guardar template
    with open(f'{pdf_dir}/pedido.html', 'w', encoding='utf-8') as f:
        f.write(template_pedido)
    
    print(f"✅ Template PDF pedido creado: {pdf_dir}/pedido.html")

def main():
    """Función principal"""
    print("🚀 CONFIGURACIÓN COMPLETA DE PDFs")
    print("="*50)
    
    # Crear datos de prueba
    datos = crear_datos_completos_pdf()
    
    # Crear template básico
    crear_template_pdf_basico()
    
    if datos:
        print(f"\n✅ CONFIGURACIÓN COMPLETA")
        print(f"📋 Pedido creado con ID: {datos['pedido'].id}")
        print(f"🧾 Factura creada con ID: {datos['factura'].id}")
        print(f"📄 Template PDF básico creado")
        print(f"\n🔗 URLs para probar:")
        print(f"   /ventas/pedidos/{datos['pedido'].id}/imprimir/")
        print(f"   /ventas/facturas/{datos['factura'].id}/imprimir/")
    else:
        print("❌ Error en la configuración")

if __name__ == "__main__":
    main()