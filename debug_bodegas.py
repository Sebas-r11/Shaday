from inventario.models import Bodega
for b in Bodega.objects.all():
    print(f"Nombre: {b.nombre}, Activa: {b.activa}, Principal: {b.es_principal}, Link: '{b.link_ubicacion}'")
    if b.activa and b.link_ubicacion and b.link_ubicacion.strip():
        print('>> Esta bodega debería aparecer en el selector.')
    else:
        print('>> Esta bodega NO cumple los filtros.')
