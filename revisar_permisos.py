import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from accounts.models import User

print('🔍 REVISANDO PERMISOS DE USUARIO ADMIN')
print('=' * 50)

user = User.objects.filter(is_superuser=True).first()
if user:
    print(f'👤 Usuario: {user.username}')
    print(f'🔐 Is superuser: {user.is_superuser}')
    
    # Probar métodos de permisos
    try:
        print(f'👑 Is admin: {user.is_admin_user()}')
    except Exception as e:
        print(f'👑 Is admin: Error - {e}')
    
    try:
        print(f'🏪 Can create sales: {user.can_create_sales()}')
    except Exception as e:
        print(f'🏪 Can create sales: Error - {e}')
    
    if hasattr(user, 'role'):
        print(f'💼 Role: {user.role}')
    else:
        print('💼 Role: No tiene atributo role')
else:
    print('❌ No hay usuarios superuser')