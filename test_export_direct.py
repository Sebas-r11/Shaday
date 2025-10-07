import os
import django
from io import BytesIO

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from ventas.views import exportar_pedidos_excel, exportar_pedidos_csv
from ventas.models import Pedido

User = get_user_model()

print("=== TEST FUNCIONALIDAD EXPORTACIÓN ===")

# Verificar datos
total_pedidos = Pedido.objects.count()
print(f"Total pedidos: {total_pedidos}")

# Crear usuario de prueba para el request
factory = RequestFactory()
try:
    user = User.objects.filter(is_staff=True).first()
    if not user:
        print("No hay usuarios staff, creando uno...")
        user = User.objects.create_user('testuser', 'test@test.com', 'password')
        user.is_staff = True
        user.save()
    
    print(f"Usuario de prueba: {user.username}")
    
    # Test exportación Excel
    request = factory.get('/ventas/pedidos/exportar/excel/')
    request.user = user
    
    print("\n--- Probando exportación Excel ---")
    try:
        response = exportar_pedidos_excel(request)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.get('Content-Type', 'No definido')}")
        print(f"Content-Disposition: {response.get('Content-Disposition', 'No definido')}")
        print(f"Tamaño del archivo: {len(response.content)} bytes")
        
        if len(response.content) > 0:
            print("✅ Excel generado exitosamente!")
        else:
            print("❌ Excel vacío")
    except Exception as e:
        print(f"❌ Error en Excel: {e}")
    
    # Test exportación CSV
    print("\n--- Probando exportación CSV ---")
    try:
        response = exportar_pedidos_csv(request)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.get('Content-Type', 'No definido')}")
        print(f"Content-Disposition: {response.get('Content-Disposition', 'No definido')}")
        print(f"Tamaño del archivo: {len(response.content)} bytes")
        
        if len(response.content) > 0:
            print("✅ CSV generado exitosamente!")
            # Mostrar primeras líneas del CSV
            content = response.content.decode('utf-8')
            lines = content.split('\n')[:3]
            print("Primeras líneas del CSV:")
            for i, line in enumerate(lines, 1):
                print(f"  {i}: {line}")
        else:
            print("❌ CSV vacío")
    except Exception as e:
        print(f"❌ Error en CSV: {e}")

except Exception as e:
    print(f"Error general: {e}")

print("\n=== FIN DEL TEST ===")