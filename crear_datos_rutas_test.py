#!/usr/bin/env python
"""
Script para crear datos de prueba para el módulo de rutas
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from accounts.models import User
from django.contrib.auth.models import Group
from ventas.models import Cliente
from rutas.models import AsignacionCliente, VisitaCliente
from datetime import datetime, timedelta
from django.utils import timezone

def crear_datos_prueba():
    print("🚀 Creando datos de prueba para el módulo de rutas...")
    
    # 1. Crear grupo vendedor si no existe
    grupo_vendedor, created = Group.objects.get_or_create(name='vendedor')
    if created:
        print("✅ Grupo 'vendedor' creado")
    else:
        print("ℹ️  Grupo 'vendedor' ya existe")
    
    # 2. Crear usuarios vendedores de prueba
    vendedores_data = [
        {
            'username': 'vendedor1',
            'first_name': 'Carlos',
            'last_name': 'Rodríguez',
            'email': 'carlos.rodriguez@distribucioneshaddai.com',
            'password': 'vendedor123'
        },
        {
            'username': 'vendedor2', 
            'first_name': 'Ana',
            'last_name': 'García',
            'email': 'ana.garcia@distribucioneshaddai.com',
            'password': 'vendedor123'
        },
        {
            'username': 'vendedor3',
            'first_name': 'Miguel',
            'last_name': 'López',
            'email': 'miguel.lopez@distribucioneshaddai.com',
            'password': 'vendedor123'
        }
    ]
    
    vendedores_creados = []
    for vendor_data in vendedores_data:
        vendedor, created = User.objects.get_or_create(
            username=vendor_data['username'],
            defaults={
                'first_name': vendor_data['first_name'],
                'last_name': vendor_data['last_name'],
                'email': vendor_data['email'],
                'is_active': True
            }
        )
        
        if created:
            vendedor.set_password(vendor_data['password'])
            vendedor.save()
            print(f"✅ Vendedor {vendedor.get_full_name()} creado")
        else:
            print(f"ℹ️  Vendedor {vendedor.get_full_name()} ya existe")
        
        # Agregar al grupo vendedor
        vendedor.groups.add(grupo_vendedor)
        vendedores_creados.append(vendedor)
    
    # 3. Obtener clientes existentes
    clientes = list(Cliente.objects.all())
    print(f"📊 Clientes disponibles: {len(clientes)}")
    
    if len(clientes) == 0:
        print("❌ No hay clientes en el sistema. No se pueden crear asignaciones.")
        return
    
    # 4. Crear asignaciones de clientes a vendedores
    asignaciones_creadas = 0
    for i, cliente in enumerate(clientes):
        # Verificar si ya tiene asignación
        if hasattr(cliente, 'asignacion_vendedor') and cliente.asignacion_vendedor:
            print(f"ℹ️  Cliente {cliente.nombre_completo} ya tiene asignación")
            continue
        
        # Asignar vendedor rotativo
        vendedor = vendedores_creados[i % len(vendedores_creados)]
        
        # Frecuencias variadas para demostración
        frecuencias = ['semanal', 'quincenal', 'mensual', 'semanal']
        frecuencia = frecuencias[i % len(frecuencias)]
        
        asignacion, created = AsignacionCliente.objects.get_or_create(
            cliente=cliente,
            vendedor=vendedor,
            defaults={
                'frecuencia_visita': frecuencia,
                'activa': True,
                'notas': f'Cliente asignado a {vendedor.get_full_name()} para visitas {frecuencia}s'
            }
        )
        
        if created:
            print(f"✅ {cliente.nombre_completo} → {vendedor.get_full_name()} ({frecuencia})")
            asignaciones_creadas += 1
        else:
            print(f"ℹ️  Asignación {cliente.nombre_completo} → {vendedor.get_full_name()} ya existe")
    
    print(f"📈 Total asignaciones creadas: {asignaciones_creadas}")
    
    # 5. Crear algunas visitas de ejemplo
    asignaciones = AsignacionCliente.objects.all()
    visitas_creadas = 0
    
    for asignacion in asignaciones[:3]:  # Solo para las primeras 3 asignaciones
        # Crear una visita reciente (hace 3 días)
        fecha_visita = timezone.now() - timedelta(days=3)
        
        visita, created = VisitaCliente.objects.get_or_create(
            asignacion=asignacion,
            fecha_programada=fecha_visita,
            defaults={
                'observaciones': f'Visita de demostración realizada con {asignacion.cliente.nombre_completo}. Cliente mostró interés en ampliar pedidos.',
                'resultado': 'exitosa',
                'estado': 'realizada',
                'fecha_realizada': timezone.now(),
                'creada_por': asignacion.vendedor
            }
        )
        
        if created:
            print(f"✅ Visita registrada: {asignacion.cliente.nombre_completo} ({fecha_visita})")
            visitas_creadas += 1
    
    print(f"📅 Total visitas creadas: {visitas_creadas}")
    
    # 6. Resumen final
    print("\n" + "="*50)
    print("📊 RESUMEN DE DATOS CREADOS:")
    print("="*50)
    print(f"👥 Vendedores: {User.objects.filter(groups__name='vendedor').count()}")
    print(f"🤝 Asignaciones: {AsignacionCliente.objects.count()}")
    print(f"📅 Visitas registradas: {VisitaCliente.objects.count()}")
    print(f"👤 Clientes en sistema: {Cliente.objects.count()}")
    
    print("\n🎯 Credenciales de prueba:")
    print("- Usuario: vendedor1, Contraseña: vendedor123")
    print("- Usuario: vendedor2, Contraseña: vendedor123") 
    print("- Usuario: vendedor3, Contraseña: vendedor123")
    
    print("\n🚀 ¡El módulo de rutas está listo para probar!")
    print("   Accede a http://localhost:8000/rutas/ con cualquier vendedor")

if __name__ == '__main__':
    try:
        crear_datos_prueba()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()