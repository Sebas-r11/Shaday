import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from django.test import Client
from accounts.models import User

print('🔍 VALIDACIÓN DE PERMISOS Y ROLES')
print('=' * 60)

# Obtener usuarios de diferentes roles
usuarios_por_rol = {}
for role in ['superadmin', 'admin', 'vendedor', 'bodeguero']:
    usuario = User.objects.filter(role=role).first()
    if usuario:
        usuarios_por_rol[role] = usuario

print('👥 USUARIOS DISPONIBLES POR ROL:')
for role, usuario in usuarios_por_rol.items():
    if usuario:
        print(f'   {role}: {usuario.username} (ID: {usuario.id})')

if not usuarios_por_rol:
    print('   ❌ No hay usuarios con roles específicos para probar')
    exit()

print()
print('🎯 PROBANDO PERMISOS POR ROL:')
print('-' * 40)

# URLs críticas para probar permisos
urls_criticas = [
    # Administración
    ('/accounts/usuarios/', 'Gestión Usuarios', ['superadmin', 'admin']),
    ('/accounts/usuarios/crear/', 'Crear Usuario', ['superadmin', 'admin']),
    
    # Ventas
    ('/ventas/', 'Dashboard Ventas', ['superadmin', 'admin', 'vendedor']),
    ('/ventas/clientes/', 'Listar Clientes', ['superadmin', 'admin', 'vendedor']),
    ('/ventas/pedidos/', 'Listar Pedidos', ['superadmin', 'admin', 'vendedor']),
    
    # Inventario
    ('/inventario/', 'Dashboard Inventario', ['superadmin', 'admin', 'bodeguero']),
    ('/inventario/productos/', 'Listar Productos', ['superadmin', 'admin', 'bodeguero']),
    ('/inventario/movimientos/', 'Movimientos Stock', ['superadmin', 'admin', 'bodeguero']),
    
    # Analytics
    ('/analytics/', 'Dashboard Analytics', ['superadmin', 'admin']),
]

success_count = 0
total_tests = 0

for url, descripcion, roles_permitidos in urls_criticas:
    print()
    print(f'📋 Probando: {descripcion} ({url})')
    
    for role, usuario in usuarios_por_rol.items():
        if usuario:
            client = Client()
            client.force_login(usuario)
            
            try:
                response = client.get(url)
                
                if role in roles_permitidos:
                    # Debería tener acceso
                    if response.status_code in [200, 302]:
                        print(f'   ✅ {role}: Acceso permitido (Status: {response.status_code})')
                        success_count += 1
                    elif response.status_code == 403:
                        print(f'   ❌ {role}: Acceso denegado incorrectamente (403)')
                    else:
                        print(f'   ⚠️ {role}: Status inesperado ({response.status_code})')
                        success_count += 0.5  # Medio punto por respuesta inesperada
                else:
                    # No debería tener acceso
                    if response.status_code == 403:
                        print(f'   ✅ {role}: Acceso denegado correctamente (403)')
                        success_count += 1
                    elif response.status_code in [200, 302]:
                        print(f'   ❌ {role}: Acceso permitido incorrectamente (Status: {response.status_code})')
                    else:
                        print(f'   ⚠️ {role}: Status inesperado ({response.status_code})')
                        success_count += 0.5  # Medio punto
                
                total_tests += 1
                
            except Exception as e:
                print(f'   ❌ {role}: Error - {str(e)[:50]}...')
                total_tests += 1

print()
print('🔍 PROBANDO MÉTODOS DE PERMISOS:')
print('-' * 40)

for role, usuario in usuarios_por_rol.items():
    if usuario:
        print()
        print(f'👤 Usuario {role} ({usuario.username}):')
        
        # Métodos de permisos a probar
        metodos_permisos = [
            'can_create_sales',
            'can_manage_inventory', 
            'can_adjust_inventory',
            'can_view_analytics',
            'can_manage_users',
            'is_admin_user',
            'is_superuser'
        ]
        
        for metodo in metodos_permisos:
            try:
                if hasattr(usuario, metodo):
                    resultado = getattr(usuario, metodo)()
                    if callable(resultado):
                        resultado = resultado()
                    print(f'   {metodo}: {resultado}')
                else:
                    print(f'   {metodo}: No disponible')
            except Exception as e:
                print(f'   {metodo}: Error - {str(e)[:30]}...')

print()
print('📊 RESUMEN DE PERMISOS:')
print('=' * 40)
print(f'✅ Pruebas exitosas: {success_count}/{total_tests}')
if total_tests > 0:
    print(f'📈 Porcentaje de éxito: {(success_count/total_tests)*100:.1f}%')

    if success_count >= total_tests * 0.8:
        print('✅ Sistema de permisos en buen estado')
    elif success_count >= total_tests * 0.6:
        print('⚠️ Sistema de permisos con problemas menores')
    else:
        print('❌ Sistema de permisos requiere atención')
else:
    print('❌ No se pudieron realizar pruebas de permisos')

print()
print('🔧 PRÓXIMOS PASOS:')
print('   □ Validar sistema de inventario')
print('   □ Comprobar integridad de datos')