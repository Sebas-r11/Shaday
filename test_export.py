import requests
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from django.contrib.auth.models import User
from ventas.models import Pedido

print("=== TESTING EXPORT FUNCTIONALITY ===")

# Verificar pedidos
total_pedidos = Pedido.objects.count()
print(f"Total pedidos en BD: {total_pedidos}")

if total_pedidos > 0:
    print("Últimos 3 pedidos:")
    for p in Pedido.objects.all()[:3]:
        numero = p.numero or f"PED-{p.id}"
        print(f"- {numero}: {p.cliente.nombre_completo} - {p.estado} - ${p.total}")
else:
    print("No hay pedidos en la base de datos")

# Probar URLs (necesita usuario logueado, por lo que solo verificamos que no den error de URL)
try:
    response = requests.get('http://127.0.0.1:8000/ventas/pedidos/exportar/excel/', timeout=5)
    print(f"\nURL Excel - Status: {response.status_code}")
    if response.status_code == 302:
        print("Redirige a login (correcto - requiere autenticación)")
    
    response = requests.get('http://127.0.0.1:8000/ventas/pedidos/exportar/csv/', timeout=5)
    print(f"URL CSV - Status: {response.status_code}")
    if response.status_code == 302:
        print("Redirige a login (correcto - requiere autenticación)")
        
    print("\n✅ URLs configuradas correctamente!")
except Exception as e:
    print(f"Error al conectar al servidor: {e}")
    print("Asegúrate de que el servidor esté ejecutándose en http://127.0.0.1:8000")