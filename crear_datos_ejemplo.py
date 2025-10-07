#!/usr/bin/env python
"""
Generador de datos de ejemplo - Sistema ERP Distribuciones Shaddai
Crea datos básicos para desarrollo y testing sin información sensible
"""
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

def create_sample_data():
    """Crea datos de ejemplo para desarrollo"""
    print("🔧 GENERANDO DATOS DE EJEMPLO")
    print("Sistema ERP - Distribuciones Shaddai")
    print("=" * 50)
    
    try:
        # Importar modelos
        from django.contrib.auth import get_user_model
        from ventas.models import Cliente
        from inventario.models import Producto, Categoria, Subcategoria, Bodega, Stock
        
        User = get_user_model()
        
        print("📊 Creando datos básicos...")
        
        # 1. Crear usuario admin de ejemplo
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@ejemplo.com',
                password='admin123',
                first_name='Administrador',
                last_name='Sistema'
            )
            print("   ✅ Usuario admin creado (admin/admin123)")
        else:
            print("   ℹ️  Usuario admin ya existe")
        
        # 2. Crear categorías de ejemplo
        categorias_ejemplo = [
            'Electrónicos',
            'Ropa y Accesorios',
            'Hogar y Jardín',
            'Deportes',
            'Libros'
        ]
        
        for cat_nombre in categorias_ejemplo:
            categoria, created = Categoria.objects.get_or_create(
                nombre=cat_nombre,
                defaults={'descripcion': f'Categoría de {cat_nombre.lower()}'}
            )
            if created:
                print(f"   ✅ Categoría creada: {cat_nombre}")
        
        # 3. Crear subcategorías de ejemplo
        subcategorias_ejemplo = [
            ('Electrónicos', 'Smartphones'),
            ('Electrónicos', 'Laptops'),
            ('Ropa y Accesorios', 'Camisas'),
            ('Hogar y Jardín', 'Decoración'),
            ('Deportes', 'Fútbol')
        ]
        
        for cat_nombre, subcat_nombre in subcategorias_ejemplo:
            try:
                categoria = Categoria.objects.get(nombre=cat_nombre)
                subcategoria, created = Subcategoria.objects.get_or_create(
                    nombre=subcat_nombre,
                    categoria=categoria,
                    defaults={'descripcion': f'Subcategoría de {subcat_nombre.lower()}'}
                )
                if created:
                    print(f"   ✅ Subcategoría creada: {subcat_nombre}")
            except Categoria.DoesNotExist:
                pass
        
        # 4. Crear bodegas de ejemplo
        bodegas_ejemplo = [
            ('Bodega Principal', 'Calle 123 #45-67, Centro de Distribución'),
            ('Bodega Secundaria', 'Carrera 78 #90-12, Bodega de Overflow')
        ]
        
        for nombre, direccion in bodegas_ejemplo:
            bodega, created = Bodega.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'direccion': direccion,
                    'activa': True,
                    'es_principal': nombre == 'Bodega Principal'
                }
            )
            if created:
                print(f"   ✅ Bodega creada: {nombre}")
        
        # 5. Crear clientes de ejemplo
        clientes_ejemplo = [
            {
                'nombre_completo': 'Empresa Demo S.A.S',
                'numero_documento': '900123456-1',
                'tipo_documento': 'NIT',
                'telefono': '1234567890',
                'ciudad': 'Bogotá',
                'direccion': 'Calle 123 #45-67'
            },
            {
                'nombre_completo': 'Comercial Ejemplo Ltda',
                'numero_documento': '800987654-2',
                'tipo_documento': 'NIT',
                'telefono': '0987654321',
                'ciudad': 'Medellín',
                'direccion': 'Carrera 78 #90-12'
            }
        ]
        
        for cliente_data in clientes_ejemplo:
            cliente, created = Cliente.objects.get_or_create(
                numero_documento=cliente_data['numero_documento'],
                defaults=cliente_data
            )
            if created:
                print(f"   ✅ Cliente creado: {cliente_data['nombre_completo']}")
        
        # 6. Crear productos de ejemplo
        productos_ejemplo = [
            {
                'codigo': 'PROD001',
                'nombre': 'Producto Demo 1',
                'descripcion': 'Producto de ejemplo para testing',
                'precio_minorista': Decimal('100000.00'),
                'precio_mayorista': Decimal('85000.00'),
                'categoria': 'Electrónicos'
            },
            {
                'codigo': 'PROD002',
                'nombre': 'Producto Demo 2',
                'descripcion': 'Segundo producto de ejemplo',
                'precio_minorista': Decimal('75000.00'),
                'precio_mayorista': Decimal('65000.00'),
                'categoria': 'Ropa y Accesorios'
            },
            {
                'codigo': 'PROD003',
                'nombre': 'Producto Demo 3',
                'descripcion': 'Tercer producto de ejemplo',
                'precio_minorista': Decimal('50000.00'),
                'precio_mayorista': Decimal('42000.00'),
                'categoria': 'Hogar y Jardín'
            }
        ]
        
        for prod_data in productos_ejemplo:
            try:
                categoria = Categoria.objects.get(nombre=prod_data['categoria'])
                # Buscar una subcategoría de esa categoría
                subcategoria = Subcategoria.objects.filter(categoria=categoria).first()
                
                producto, created = Producto.objects.get_or_create(
                    codigo=prod_data['codigo'],
                    defaults={
                        'nombre': prod_data['nombre'],
                        'descripcion': prod_data['descripcion'],
                        'precio_minorista': prod_data['precio_minorista'],
                        'precio_mayorista': prod_data['precio_mayorista'],
                        'categoria': categoria,
                        'subcategoria': subcategoria,
                        'activo': True
                    }
                )
                if created:
                    print(f"   ✅ Producto creado: {prod_data['nombre']}")
                    
                    # Crear stock inicial
                    bodega_principal = Bodega.objects.filter(es_principal=True).first()
                    if bodega_principal:
                        stock, stock_created = Stock.objects.get_or_create(
                            producto=producto,
                            bodega=bodega_principal,
                            defaults={
                                'cantidad': 100
                            }
                        )
                        if stock_created:
                            print(f"     📦 Stock inicial creado: 100 unidades")
                            
            except Categoria.DoesNotExist:
                print(f"   ⚠️  Categoría no encontrada para {prod_data['nombre']}")
        
        print()
        print("=" * 50)
        print("✅ DATOS DE EJEMPLO CREADOS EXITOSAMENTE")
        print()
        print("📋 Datos creados:")
        print(f"   👤 Usuarios: {User.objects.count()}")
        print(f"   📁 Categorías: {Categoria.objects.count()}")
        print(f"   📂 Subcategorías: {Subcategoria.objects.count()}")
        print(f"   🏪 Bodegas: {Bodega.objects.count()}")
        print(f"   👥 Clientes: {Cliente.objects.count()}")
        print(f"   📦 Productos: {Producto.objects.count()}")
        print(f"   📊 Stock: {Stock.objects.count()}")
        print()
        print("🔑 Credenciales de acceso:")
        print("   Usuario: admin")
        print("   Contraseña: admin123")
        print()
        print("🌐 Para acceder al sistema:")
        print("   python manage.py runserver")
        print("   http://127.0.0.1:8000/admin/")
        
    except Exception as e:
        print(f"❌ Error creando datos: {str(e)}")
        return False
    
    return True

def reset_database():
    """Resetea la base de datos (opcional)"""
    print("⚠️  RESETEO DE BASE DE DATOS")
    print("=" * 50)
    
    response = input("¿Estás seguro de que quieres resetear la base de datos? (s/n): ")
    
    if response.lower() in ['s', 'si', 'sí', 'y', 'yes']:
        try:
            import os
            if os.path.exists('db.sqlite3'):
                os.remove('db.sqlite3')
                print("   ✅ Base de datos eliminada")
            
            # Recrear migraciones
            os.system('python manage.py migrate')
            print("   ✅ Migraciones aplicadas")
            
            return True
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False
    else:
        print("   ℹ️  Operación cancelada")
        return False

if __name__ == '__main__':
    print("🚀 CONFIGURADOR DE DATOS - SISTEMA ERP")
    print("Distribuciones Shaddai")
    print("=" * 50)
    
    if '--reset' in sys.argv:
        if reset_database():
            create_sample_data()
    else:
        create_sample_data()