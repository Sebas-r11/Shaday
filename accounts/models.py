from django.contrib.auth.models import AbstractUser
from django.db import models
from decimal import Decimal
import math

class User(AbstractUser):
    """
    Usuario personalizado con roles específicos para el sistema ERP
    """
    ROLE_CHOICES = [
        ('superadmin', 'SuperAdmin'),
        ('administrador', 'Administrador'),
        ('vendedor', 'Vendedor'),
        ('bodega', 'Bodega'),
        ('repartidor', 'Repartidor'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='vendedor',
        verbose_name='Rol'
    )
    
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Teléfono'
    )
    
    documento = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Documento de identidad'
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='Usuario activo'
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de modificación'
    )
    
    # Campos de ubicación GPS para repartidores
    latitud = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        null=True, 
        blank=True,
        verbose_name='Latitud GPS'
    )
    
    longitud = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        null=True, 
        blank=True,
        verbose_name='Longitud GPS'
    )
    
    radio_cobertura_km = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('10.0'),
        verbose_name='Radio de cobertura (km)'
    )
    
    ubicacion_actualizada = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Última actualización de ubicación'
    )
    
    disponible_entregas = models.BooleanField(
        default=True,
        verbose_name='Disponible para entregas'
    )
    
    zona_cobertura = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Zona de cobertura'
    )
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['username']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def can_manage_users(self):
        """Solo SuperAdmin y Administrador pueden gestionar usuarios"""
        return self.role in ['superadmin', 'administrador']
    
    def is_admin_user(self):
        """Verifica si el usuario es administrador (para categorías, precios, etc.)"""
        return self.role in ['superadmin', 'administrador'] or self.is_superuser
    
    def can_see_costs(self):
        """Solo SuperAdmin y Administrador pueden ver costos"""
        return self.role in ['superadmin', 'administrador']
    
    def can_adjust_inventory(self):
        """SuperAdmin, Administrador y Personal de Bodega pueden ajustar inventario"""
        return (self.is_superuser or 
                self.role in ['superadmin', 'administrador', 'bodega'])
    
    def can_view_inventory(self):
        """Usuarios que pueden consultar el inventario"""
        return (self.is_superuser or 
                self.role in ['superadmin', 'administrador', 'vendedor', 'bodega'])
    
    def can_view_stock(self):
        """Usuarios que pueden ver el estado del stock"""
        return (self.is_superuser or 
                self.role in ['superadmin', 'administrador', 'vendedor', 'bodega'])
    
    def can_access_crm(self):
        """Vendedores y Administradores pueden acceder al CRM"""
        return (self.is_superuser or 
                self.role in ['superadmin', 'administrador', 'vendedor'])
    
    def can_create_sales(self):
        """Vendedores y Administradores pueden crear ventas"""
        return self.role in ['superadmin', 'administrador', 'vendedor']
    
    def can_prepare_orders(self):
        """Personal de bodega puede preparar pedidos"""
        return self.role in ['superadmin', 'administrador', 'bodega']
    
    def can_deliver_orders(self):
        """Repartidores pueden entregar pedidos"""
        return self.role in ['superadmin', 'administrador', 'repartidor']
    
    def can_see_prices(self):
        """Usuarios que pueden ver precios y totales de productos/pedidos"""
        return self.role in ['superadmin', 'administrador', 'vendedor']
    
    def get_active_users_count(self):
        """Obtiene el número de usuarios activos (solo para administradores)"""
        if self.can_manage_users():
            return User.objects.filter(activo=True).count()
        return 0
    
    # Métodos para gestión de ubicación GPS y repartidores
    def calcular_distancia_cliente(self, cliente):
        """Calcula la distancia en km entre el repartidor y un cliente"""
        if not (self.latitud and self.longitud and cliente.latitud and cliente.longitud):
            return None
        
        # Fórmula de Haversine para calcular distancia entre dos puntos GPS
        lat1, lon1 = float(self.latitud), float(self.longitud)
        lat2, lon2 = float(cliente.latitud), float(cliente.longitud)
        
        # Convertir de grados a radianes
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Diferencias
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Fórmula de Haversine
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radio de la Tierra en km
        radio_tierra = 6371
        
        # Distancia en km
        distancia = radio_tierra * c
        return round(distancia, 2)
    
    def puede_atender_cliente(self, cliente):
        """Verifica si el repartidor puede atender a un cliente según su cobertura"""
        if not self.role == 'repartidor' or not self.disponible_entregas:
            return False
        
        distancia = self.calcular_distancia_cliente(cliente)
        if distancia is None:
            return True  # Si no hay GPS, permitir (por compatibilidad)
        
        return distancia <= float(self.radio_cobertura_km)
    
    def actualizar_ubicacion_gps(self, latitud, longitud):
        """Actualiza la ubicación GPS del repartidor"""
        from django.utils import timezone
        
        self.latitud = Decimal(str(latitud))
        self.longitud = Decimal(str(longitud))
        self.ubicacion_actualizada = timezone.now()
        self.save(update_fields=['latitud', 'longitud', 'ubicacion_actualizada'])
    
    def get_clientes_en_cobertura(self):
        """Obtiene clientes dentro del área de cobertura del repartidor"""
        if not (self.role == 'repartidor' and self.latitud and self.longitud):
            return []
        
        from ventas.models import Cliente
        clientes_cercanos = []
        
        for cliente in Cliente.objects.filter(latitud__isnull=False, longitud__isnull=False):
            if self.puede_atender_cliente(cliente):
                distancia = self.calcular_distancia_cliente(cliente)
                clientes_cercanos.append({
                    'cliente': cliente,
                    'distancia': distancia
                })
        
        # Ordenar por distancia
        clientes_cercanos.sort(key=lambda x: x['distancia'])
        return clientes_cercanos
    
    @classmethod
    def encontrar_repartidor_mas_cercano(cls, cliente):
        """Encuentra el repartidor disponible más cercano a un cliente"""
        repartidores_disponibles = cls.objects.filter(
            role='repartidor',
            activo=True,
            disponible_entregas=True,
            latitud__isnull=False,
            longitud__isnull=False
        )
        
        mejor_repartidor = None
        menor_distancia = float('inf')
        
        for repartidor in repartidores_disponibles:
            if repartidor.puede_atender_cliente(cliente):
                distancia = repartidor.calcular_distancia_cliente(cliente)
                if distancia and distancia < menor_distancia:
                    menor_distancia = distancia
                    mejor_repartidor = repartidor
        
        return {
            'repartidor': mejor_repartidor,
            'distancia': menor_distancia if mejor_repartidor else None
        }
    
    def optimizar_ruta_entregas(self, entregas_pendientes, bodega_origen=None):
        """
        Optimiza la ruta de entregas usando algoritmo nearest neighbor (TSP aproximado)
        
        Args:
            entregas_pendientes: QuerySet o lista de entregas asignadas al repartidor
            bodega_origen: Bodega de origen (si no se proporciona, se usa la principal)
            
        Returns:
            dict con ruta optimizada, distancia total y tiempo estimado
        """
        if not (self.latitud and self.longitud):
            return None
        
        # Obtener bodega de origen
        if not bodega_origen:
            from inventario.models import Bodega
            bodega_origen = Bodega.objects.filter(es_principal=True).first()
            if not bodega_origen:
                bodega_origen = Bodega.objects.filter(activa=True).first()
        
        if not bodega_origen or not (bodega_origen.latitud and bodega_origen.longitud):
            return None
        
        # Filtrar entregas con GPS válido
        entregas_con_gps = []
        for entrega in entregas_pendientes:
            cliente = entrega.cliente
            if cliente.latitud and cliente.longitud:
                entregas_con_gps.append(entrega)
        
        if not entregas_con_gps:
            return {'entregas_ordenadas': list(entregas_pendientes), 'distancia_total': 0, 'sin_gps': True}
        
        # Implementar algoritmo Nearest Neighbor (TSP aproximado)
        punto_actual = {
            'lat': float(bodega_origen.latitud),
            'lng': float(bodega_origen.longitud),
            'tipo': 'bodega',
            'nombre': bodega_origen.nombre
        }
        
        entregas_no_visitadas = list(entregas_con_gps)
        ruta_optimizada = []
        distancia_total = 0
        
        # Algoritmo nearest neighbor
        while entregas_no_visitadas:
            entrega_mas_cercana = None
            distancia_minima = float('inf')
            
            for entrega in entregas_no_visitadas:
                cliente = entrega.cliente
                distancia = self._calcular_distancia_puntos(
                    punto_actual['lat'], punto_actual['lng'],
                    float(cliente.latitud), float(cliente.longitud)
                )
                
                if distancia < distancia_minima:
                    distancia_minima = distancia
                    entrega_mas_cercana = entrega
            
            # Agregar a la ruta
            if entrega_mas_cercana:
                ruta_optimizada.append({
                    'entrega': entrega_mas_cercana,
                    'orden': len(ruta_optimizada) + 1,
                    'distancia_desde_anterior': distancia_minima,
                    'cliente': entrega_mas_cercana.cliente
                })
                
                distancia_total += distancia_minima
                entregas_no_visitadas.remove(entrega_mas_cercana)
                
                # Actualizar punto actual
                cliente = entrega_mas_cercana.cliente
                punto_actual = {
                    'lat': float(cliente.latitud),
                    'lng': float(cliente.longitud),
                    'tipo': 'cliente',
                    'nombre': cliente.nombre_completo
                }
        
        # Calcular tiempo estimado (assumiendo 30 km/h promedio + 10 min por entrega)
        tiempo_viaje_horas = distancia_total / 30  # 30 km/h promedio
        tiempo_entregas_horas = len(ruta_optimizada) * (10/60)  # 10 min por entrega
        tiempo_total_horas = tiempo_viaje_horas + tiempo_entregas_horas
        
        # Agregar entregas sin GPS al final
        entregas_sin_gps = [e for e in entregas_pendientes if e not in entregas_con_gps]
        for entrega in entregas_sin_gps:
            ruta_optimizada.append({
                'entrega': entrega,
                'orden': len(ruta_optimizada) + 1,
                'distancia_desde_anterior': 0,
                'cliente': entrega.cliente,
                'sin_gps': True
            })
        
        return {
            'bodega_origen': bodega_origen,
            'entregas_ordenadas': [item['entrega'] for item in ruta_optimizada],
            'ruta_detallada': ruta_optimizada,
            'distancia_total': round(distancia_total, 2),
            'tiempo_estimado_horas': round(tiempo_total_horas, 2),
            'numero_entregas': len(ruta_optimizada),
            'entregas_con_gps': len(entregas_con_gps),
            'entregas_sin_gps': len(entregas_sin_gps)
        }
    
    def _calcular_distancia_puntos(self, lat1, lng1, lat2, lng2):
        """Método auxiliar para calcular distancia entre dos puntos GPS"""
        import math
        
        # Convertir de grados a radianes
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        
        # Diferencias
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        # Fórmula de Haversine
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radio de la Tierra en km
        radio_tierra = 6371
        
        # Distancia en km
        return radio_tierra * c
