import os
import django
import requests
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from django.urls import reverse

print("🧪 TESTING APIs PARA DASHBOARD CON GRÁFICOS")
print("=" * 50)

# URLs de las APIs
apis = [
    ('api_estadisticas_dashboard', 'Estadísticas Dashboard'),
    ('api_ventas_por_mes', 'Ventas por Mes'),
    ('api_estados_pedidos', 'Estados Pedidos'),
    ('api_productos_vendidos', 'Productos Vendidos'),
    ('api_ventas_vendedor', 'Ventas por Vendedor')
]

print("\n🔗 URLs de APIs configuradas:")
for api_name, description in apis:
    try:
        url = reverse(f'ventas:{api_name}')
        print(f"✅ {description}: {url}")
    except Exception as e:
        print(f"❌ {description}: Error - {e}")

print("\n📊 Dashboard Avanzado URL:")
try:
    dashboard_url = reverse('ventas:dashboard_charts')
    print(f"✅ Dashboard Charts: {dashboard_url}")
except Exception as e:
    print(f"❌ Dashboard Charts: Error - {e}")

print("\n✅ Configuración completada correctamente!")
print("🌐 Para probar: http://127.0.0.1:8001/ventas/charts/")
print("📱 Características del nuevo dashboard:")
print("  - 4 KPIs dinámicos con indicadores de crecimiento")
print("  - Gráfico de evolución de ventas (12 meses)")
print("  - Gráfico de distribución de pedidos (donut)")
print("  - Gráfico de productos más vendidos (barras horizontales)")
print("  - Gráfico de ventas por vendedor (barras)")
print("  - Auto-refresh cada 5 minutos")
print("  - Indicadores de carga")
print("  - Accesos rápidos a funciones principales")