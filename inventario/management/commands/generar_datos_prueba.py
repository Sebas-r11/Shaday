from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from inventario.models import Categoria, Subcategoria, Producto, Bodega, Stock
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Genera datos de prueba iniciales para el sistema'

    def handle(self, *args, **options):
        self.stdout.write("Generando datos de prueba...")
        
        # Crear bodega principal
        bodega_principal, created = Bodega.objects.get_or_create(
            nombre="Bodega Principal",
            defaults={
                'direccion': 'Calle Principal #123, Bogotá',
                'telefono': '601-2345678',
                'es_principal': True
            }
        )
        
        # Crear categorías
        cat_papeleria, created = Categoria.objects.get_or_create(
            nombre="Papelería",
            defaults={'descripcion': 'Productos de papelería y oficina'}
        )
        
        cat_aseo, created = Categoria.objects.get_or_create(
            nombre="Aseo",
            defaults={'descripcion': 'Productos de aseo y limpieza'}
        )
        
        # Crear subcategorías para Papelería
        subcat_cuadernos, created = Subcategoria.objects.get_or_create(
            categoria=cat_papeleria,
            nombre="Cuadernos",
            defaults={'descripcion': 'Cuadernos y libretas'}
        )
        
        subcat_lapices, created = Subcategoria.objects.get_or_create(
            categoria=cat_papeleria,
            nombre="Lápices y Bolígrafos",
            defaults={'descripcion': 'Instrumentos de escritura'}
        )
        
        subcat_carpetas, created = Subcategoria.objects.get_or_create(
            categoria=cat_papeleria,
            nombre="Carpetas",
            defaults={'descripcion': 'Carpetas y archivadores'}
        )
        
        # Crear subcategorías para Aseo
        subcat_detergentes, created = Subcategoria.objects.get_or_create(
            categoria=cat_aseo,
            nombre="Detergentes",
            defaults={'descripcion': 'Detergentes y jabones'}
        )
        
        subcat_desinfectantes, created = Subcategoria.objects.get_or_create(
            categoria=cat_aseo,
            nombre="Desinfectantes",
            defaults={'descripcion': 'Desinfectantes y antibacteriales'}
        )
        
        # Productos de Papelería
        productos_papeleria = [
            {
                'codigo': '000001',
                'nombre': 'Cuaderno Universitario 100 hojas',
                'categoria': cat_papeleria,
                'subcategoria': subcat_cuadernos,
                'costo_promedio': Decimal('2500.00'),
                'precio_minorista': Decimal('3500.00'),
                'precio_mayorista': Decimal('3000.00'),
                'stock_minimo': 50,
                'stock_inicial': 150
            },
            {
                'codigo': '000002',
                'nombre': 'Cuaderno Argollado A4',
                'categoria': cat_papeleria,
                'subcategoria': subcat_cuadernos,
                'costo_promedio': Decimal('4000.00'),
                'precio_minorista': Decimal('5500.00'),
                'precio_mayorista': Decimal('4800.00'),
                'stock_minimo': 30,
                'stock_inicial': 80
            },
            {
                'codigo': '000003',
                'nombre': 'Bolígrafo BIC Azul',
                'categoria': cat_papeleria,
                'subcategoria': subcat_lapices,
                'costo_promedio': Decimal('800.00'),
                'precio_minorista': Decimal('1200.00'),
                'precio_mayorista': Decimal('1000.00'),
                'stock_minimo': 100,
                'stock_inicial': 500
            },
            {
                'codigo': '000004',
                'nombre': 'Lápiz HB Faber Castell',
                'categoria': cat_papeleria,
                'subcategoria': subcat_lapices,
                'costo_promedio': Decimal('1000.00'),
                'precio_minorista': Decimal('1500.00'),
                'precio_mayorista': Decimal('1300.00'),
                'stock_minimo': 200,
                'stock_inicial': 300
            },
            {
                'codigo': '000005',
                'nombre': 'Carpeta Colgante Tamaño Oficio',
                'categoria': cat_papeleria,
                'subcategoria': subcat_carpetas,
                'costo_promedio': Decimal('1500.00'),
                'precio_minorista': Decimal('2200.00'),
                'precio_mayorista': Decimal('1900.00'),
                'stock_minimo': 25,
                'stock_inicial': 60
            }
        ]
        
        # Productos de Aseo
        productos_aseo = [
            {
                'codigo': '000006',
                'nombre': 'Detergente en Polvo 1kg',
                'categoria': cat_aseo,
                'subcategoria': subcat_detergentes,
                'costo_promedio': Decimal('3200.00'),
                'precio_minorista': Decimal('4500.00'),
                'precio_mayorista': Decimal('4000.00'),
                'stock_minimo': 40,
                'stock_inicial': 120
            },
            {
                'codigo': '000007',
                'nombre': 'Jabón Líquido Antibacterial 500ml',
                'categoria': cat_aseo,
                'subcategoria': subcat_detergentes,
                'costo_promedio': Decimal('2800.00'),
                'precio_minorista': Decimal('4000.00'),
                'precio_mayorista': Decimal('3500.00'),
                'stock_minimo': 30,
                'stock_inicial': 80
            },
            {
                'codigo': '000008',
                'nombre': 'Desinfectante Multiusos 1L',
                'categoria': cat_aseo,
                'subcategoria': subcat_desinfectantes,
                'costo_promedio': Decimal('3500.00'),
                'precio_minorista': Decimal('5000.00'),
                'precio_mayorista': Decimal('4300.00'),
                'stock_minimo': 20,
                'stock_inicial': 50
            },
            {
                'codigo': '000009',
                'nombre': 'Alcohol Antiséptico 70% - 250ml',
                'categoria': cat_aseo,
                'subcategoria': subcat_desinfectantes,
                'costo_promedio': Decimal('2000.00'),
                'precio_minorista': Decimal('3000.00'),
                'precio_mayorista': Decimal('2600.00'),
                'stock_minimo': 50,
                'stock_inicial': 100
            },
            {
                'codigo': '000010',
                'nombre': 'Limpiador de Vidrios 500ml',
                'categoria': cat_aseo,
                'subcategoria': subcat_desinfectantes,
                'costo_promedio': Decimal('2500.00'),
                'precio_minorista': Decimal('3500.00'),
                'precio_mayorista': Decimal('3100.00'),
                'stock_minimo': 25,
                'stock_inicial': 45
            }
        ]
        
        # Crear productos y stock inicial
        todos_productos = productos_papeleria + productos_aseo
        
        for producto_data in todos_productos:
            stock_inicial = producto_data.pop('stock_inicial')
            
            producto, created = Producto.objects.get_or_create(
                codigo=producto_data['codigo'],
                defaults=producto_data
            )
            
            if created:
                self.stdout.write(f"  ✓ Producto creado: {producto.codigo} - {producto.nombre}")
                
                # Crear stock inicial
                stock, stock_created = Stock.objects.get_or_create(
                    producto=producto,
                    bodega=bodega_principal,
                    defaults={'cantidad': stock_inicial}
                )
                
                if stock_created:
                    self.stdout.write(f"    Stock inicial: {stock_inicial} unidades")
        
        # Crear usuarios de ejemplo
        self.create_sample_users()
        
        self.stdout.write(
            self.style.SUCCESS(f'Datos de prueba generados exitosamente!')
        )
        self.stdout.write(f"  • {Categoria.objects.count()} categorías")
        self.stdout.write(f"  • {Subcategoria.objects.count()} subcategorías")
        self.stdout.write(f"  • {Producto.objects.count()} productos")
        self.stdout.write(f"  • {Bodega.objects.count()} bodega(s)")
        self.stdout.write(f"  • {User.objects.count()} usuario(s)")
    
    def create_sample_users(self):
        """Crear usuarios de ejemplo para cada rol"""
        usuarios_ejemplo = [
            {
                'username': 'vendedor1',
                'email': 'vendedor1@reyes.com',
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'role': 'vendedor',
                'documento': '12345678',
                'telefono': '3101234567'
            },
            {
                'username': 'bodeguero1',
                'email': 'bodega1@reyes.com',
                'first_name': 'María',
                'last_name': 'González',
                'role': 'bodega',
                'documento': '87654321',
                'telefono': '3109876543'
            },
            {
                'username': 'repartidor1',
                'email': 'reparto1@reyes.com',
                'first_name': 'Carlos',
                'last_name': 'Rodríguez',
                'role': 'repartidor',
                'documento': '11223344',
                'telefono': '3201122334'
            }
        ]
        
        for user_data in usuarios_ejemplo:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            
            if created:
                user.set_password('123456')  # Contraseña temporal
                user.save()
                self.stdout.write(f"  ✓ Usuario creado: {user.username} ({user.get_role_display()})")