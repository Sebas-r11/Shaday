import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from django.test import Client
from accounts.models import User
from ventas.models import Pedido

print('🔍 DIAGNÓSTICO DETALLADO PEDIDO PDF')
print('=' * 50)

# Verificar que el pedido existe
try:
    pedido = Pedido.objects.get(id=49)
    print(f'📋 Pedido encontrado: {pedido.numero}')
    print(f'   Cliente: {pedido.cliente.nombre_completo}')
    print(f'   Asignado a: {pedido.asignado_a}')
    print(f'   Estado: {pedido.estado}')
except Exception as e:
    print(f'❌ Error buscando pedido: {e}')
    exit()

# Autenticar
client = Client()
user = User.objects.filter(is_superuser=True).first()
client.force_login(user)
print(f'✅ Autenticado como: {user.username} (role: {user.role})')

# Probar URL con follow=False para ver redirección
url = '/ventas/pedidos/49/imprimir/'
response = client.get(url, follow=False)
print(f'📡 Respuesta: Status {response.status_code}')
if response.status_code == 302:
    location = response.get('Location', 'unknown')
    print(f'🔄 Redirección a: {location}')
elif response.status_code == 403:
    print('🚫 Acceso denegado')
    content = response.content.decode()[:200]
    print(f'   Content: {content}')
elif response.status_code == 200:
    content_type = response.get('Content-Type', '')
    print(f'✅ Respuesta OK - Content-Type: {content_type}')
    print(f'   Tamaño: {len(response.content)} bytes')
else:
    print(f'❌ Error inesperado: {response.status_code}')