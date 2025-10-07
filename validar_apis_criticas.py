import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from django.test import Client
from accounts.models import User
import json

print('🔍 VALIDACIÓN COMPLETA DE APIs CRÍTICAS')
print('=' * 60)

# Autenticar
client = Client()
user = User.objects.filter(is_superuser=True).first()
client.force_login(user)
print(f'✅ Usuario autenticado: {user.username} (role: {user.role})')

# APIs críticas a validar (URLs reales del sistema)
apis_criticas = [
    # Dashboard páginas principales
    ('/accounts/dashboard/', 'Dashboard principal'),
    ('/ventas/', 'Dashboard ventas'),
    ('/analytics/', 'Dashboard analytics'),
    ('/inventario/', 'Dashboard inventario'),
    
    # APIs JSON de ventas
    ('/ventas/api/productos/', 'API búsqueda productos'),
    ('/ventas/api/clientes/', 'API búsqueda clientes'),
    ('/ventas/api/pedidos/pendientes/', 'API pedidos pendientes'),
    ('/ventas/api/estadisticas/ventas/', 'API estadísticas ventas'),
    ('/ventas/api/verificar-stock/', 'API verificar stock'),
    
    # APIs JSON de inventario
    ('/inventario/api/subcategorias/', 'API subcategorías'),
    ('/inventario/api/stock/', 'API stock'),
    ('/inventario/api/generar-recomendaciones/', 'API recomendaciones'),
    
    # APIs de analytics
    ('/analytics/api/prediccion/30/', 'API predicción producto'),
]

print()
print('🎯 PROBANDO APIs CRÍTICAS:')
print('-' * 40)

success_count = 0
total_apis = len(apis_criticas)

for url, descripcion in apis_criticas:
    try:
        response = client.get(url)
        
        if response.status_code == 200:
            content_type = response.get('Content-Type', '')
            
            if 'application/json' in content_type:
                try:
                    data = response.json()
                    print(f'✅ {descripcion}: JSON válido ({len(str(data))} chars)')
                    success_count += 1
                except json.JSONDecodeError:
                    print(f'❌ {descripcion}: JSON inválido')
            elif 'text/html' in content_type:
                print(f'✅ {descripcion}: HTML cargado ({len(response.content)} bytes)')
                success_count += 1
            else:
                print(f'⚠️ {descripcion}: Respuesta OK pero tipo inesperado ({content_type})')
                success_count += 1
                
        elif response.status_code == 302:
            print(f'🔄 {descripcion}: Redirección (posible flujo válido)')
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
print('📊 RESUMEN APIs CRÍTICAS:')
print('=' * 40)
print(f'✅ APIs funcionando: {success_count}/{total_apis}')
print(f'📈 Porcentaje de éxito: {(success_count/total_apis)*100:.1f}%')

if success_count >= total_apis * 0.8:
    print('✅ Sistema API en buen estado')
elif success_count >= total_apis * 0.6:
    print('⚠️ Sistema API con problemas menores')
else:
    print('❌ Sistema API requiere atención')

print()
print('🔧 PRÓXIMOS PASOS:')
print('   □ Validar formularios principales')
print('   □ Probar flujos de trabajo completos') 
print('   □ Verificar permisos por roles')
print('   □ Validar sistema de inventario')
print('   □ Comprobar integridad de datos')