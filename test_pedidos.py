from ventas.models import Pedido
print(f'Total pedidos: {Pedido.objects.count()}')
print('Últimos 3:')
for p in Pedido.objects.all()[:3]:
    numero = p.numero or f"PED-{p.id}"
    print(f'- {numero}: {p.cliente.nombre_completo} - {p.estado} - ${p.total}')