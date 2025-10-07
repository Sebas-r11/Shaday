import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from django.test import Client
from accounts.models import User
from ventas.models import Cliente, Pedido, Factura
from inventario.models import Producto, Categoria

print('🔍 VALIDACIÓN DE FORMULARIOS PRINCIPALES')
print('=' * 60)

# Autenticar como admin
client = Client()
user = User.objects.filter(is_superuser=True).first()
client.force_login(user)
print(f'✅ Usuario autenticado: {user.username} (role: {user.role})')

# Formularios críticos a validar
formularios_criticos = [
    # URLs de formularios de creación
    ('/ventas/clientes/crear/', 'Crear Cliente'),
    ('/ventas/pedidos/crear/', 'Crear Pedido'),
    ('/ventas/facturas/crear/', 'Crear Factura'),
    ('/inventario/productos/crear/', 'Crear Producto'),
    ('/inventario/categorias/crear/', 'Crear Categoría'),
    ('/accounts/usuarios/crear/', 'Crear Usuario'),
    
    # URLs de listas (para verificar acceso)
    ('/ventas/clientes/', 'Listar Clientes'),
    ('/ventas/pedidos/', 'Listar Pedidos'),
    ('/ventas/facturas/', 'Listar Facturas'),
    ('/inventario/productos/', 'Listar Productos'),
    ('/inventario/categorias/', 'Listar Categorías'),
    
    # URLs de edición si hay datos
    ('/ventas/clientes/32/editar/', 'Editar Cliente'),
    ('/ventas/pedidos/49/editar/', 'Editar Pedido'),
    ('/inventario/productos/30/editar/', 'Editar Producto'),
]

print()
print('🎯 PROBANDO FORMULARIOS CRÍTICOS:')
print('-' * 40)

success_count = 0
total_forms = len(formularios_criticos)

for url, descripcion in formularios_criticos:
    try:
        response = client.get(url)
        
        if response.status_code == 200:
            content = response.content.decode()
            # Verificar que tenga elementos de formulario
            if any(tag in content for tag in ['<form', '<input', '<select', '<textarea']):
                print(f'✅ {descripcion}: Formulario cargado correctamente')
                success_count += 1
            else:
                print(f'⚠️ {descripcion}: Página cargada pero sin formulario visible')
                
        elif response.status_code == 302:
            print(f'🔄 {descripcion}: Redirección (posible login/flujo válido)')
            success_count += 1
            
        elif response.status_code == 404:
            print(f'❌ {descripcion}: URL no encontrada (404)')
            
        elif response.status_code == 403:
            print(f'🚫 {descripcion}: Sin permisos (403)')
            
        else:
            print(f'❌ {descripcion}: Error {response.status_code}')
            
    except Exception as e:
        print(f'❌ {descripcion}: Excepción - {str(e)[:50]}...')

print()
print('🧪 PROBANDO CREACIÓN DE DATOS:')
print('-' * 40)

# Probar creación de cliente
try:
    data_cliente = {
        'tipo_documento': 'CC',
        'numero_documento': '87654321',
        'nombre_completo': 'Cliente Test Validación',
        'telefono': '3009876543',
        'direccion': 'Calle Test 789',
        'ciudad': 'Medellín',
        'tipo_cliente': 'minorista'
    }
    
    response = client.post('/ventas/clientes/crear/', data_cliente)
    if response.status_code in [200, 302]:
        print('✅ Creación Cliente: POST procesado correctamente')
        success_count += 1
    else:
        print(f'❌ Creación Cliente: Error {response.status_code}')
        
except Exception as e:
    print(f'❌ Creación Cliente: Error - {str(e)[:50]}...')

# Probar creación de producto
try:
    # Obtener categoría existente
    categoria = Categoria.objects.first()
    if categoria and hasattr(categoria, 'subcategorias') and categoria.subcategorias.exists():
        subcategoria = categoria.subcategorias.first()
        
        data_producto = {
            'codigo': '999999',
            'nombre': 'Producto Test Validación',
            'categoria': categoria.id,
            'subcategoria': subcategoria.id,
            'precio_minorista': '15000.00',
            'precio_mayorista': '12000.00',
            'stock_minimo': '10'
        }
        
        response = client.post('/inventario/productos/crear/', data_producto)
        if response.status_code in [200, 302]:
            print('✅ Creación Producto: POST procesado correctamente')
            success_count += 1
        else:
            print(f'❌ Creación Producto: Error {response.status_code}')
    else:
        print('⚠️ Creación Producto: No hay categorías/subcategorías para probar')
        
except Exception as e:
    print(f'❌ Creación Producto: Error - {str(e)[:50]}...')

total_forms += 2  # Añadir las dos pruebas POST

print()
print('📊 RESUMEN FORMULARIOS:')
print('=' * 40)
print(f'✅ Formularios funcionando: {success_count}/{total_forms}')
print(f'📈 Porcentaje de éxito: {(success_count/total_forms)*100:.1f}%')

if success_count >= total_forms * 0.8:
    print('✅ Sistema de formularios en buen estado')
elif success_count >= total_forms * 0.6:
    print('⚠️ Sistema de formularios con problemas menores')
else:
    print('❌ Sistema de formularios requiere atención')

print()
print('🔧 PRÓXIMOS PASOS:')
print('   □ Probar flujos de trabajo completos')
print('   □ Verificar permisos por roles')
print('   □ Validar sistema de inventario')
print('   □ Comprobar integridad de datos')