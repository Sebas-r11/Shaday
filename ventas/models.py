from django.db import models
from django.db.models import F
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

class Departamento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=10, unique=True, null=True, blank=True)
    
    def __str__(self):
        return self.nombre

class Ciudad(models.Model):
    nombre = models.CharField(max_length=100)
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='ciudades')
    codigo_postal = models.CharField(max_length=10, null=True, blank=True)
    
    def __str__(self):
        return f"{self.nombre}, {self.departamento.nombre}"

class Cliente(models.Model):
    TIPO_DOCUMENTO_CHOICES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('NIT', 'NIT'),
    ]
    
    TIPO_CLIENTE_CHOICES = [
        ('minorista', 'Minorista'),
        ('mayorista', 'Mayorista'),
    ]
    
    tipo_documento = models.CharField(max_length=3, choices=TIPO_DOCUMENTO_CHOICES, default='CC')
    numero_documento = models.CharField(max_length=20, unique=True)
    nombre_completo = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20)
    direccion = models.TextField()
    ciudad = models.CharField(max_length=100, default='Bogotá')
    enlace_maps = models.URLField(blank=True)
    tipo_cliente = models.CharField(max_length=20, choices=TIPO_CLIENTE_CHOICES, default='minorista')
    limite_credito = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Límite de crédito en pesos")
    dias_credito = models.IntegerField(default=0, help_text="Días de crédito permitidos")
    vendedor_asignado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre_completo

class Cotizacion(models.Model):
    numero = models.CharField(max_length=20, unique=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='borrador')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.generar_numero()
        super().save(*args, **kwargs)
    
    def generar_numero(self):
        """Genera un número único para la cotización"""
        from datetime import datetime
        
        # Obtener año actual
        año_actual = datetime.now().year
        
        # Buscar el último número del año
        prefijo = f"COT{año_actual}"
        
        ultimas_cotizaciones = Cotizacion.objects.filter(
            numero__startswith=prefijo
        ).order_by('-numero')
        
        if ultimas_cotizaciones.exists():
            ultimo_numero = ultimas_cotizaciones.first().numero
            try:
                # Extraer el número secuencial
                parte_numerica = ultimo_numero.replace(prefijo, '').lstrip('0') or '0'
                siguiente_numero = int(parte_numerica) + 1
            except ValueError:
                siguiente_numero = 1
        else:
            siguiente_numero = 1
        
        # Formatear con ceros a la izquierda
        numero_formateado = f"{prefijo}{siguiente_numero:03d}"
        
        # Verificar que no exista
        while Cotizacion.objects.filter(numero=numero_formateado).exists():
            siguiente_numero += 1
            numero_formateado = f"{prefijo}{siguiente_numero:03d}"
        
        return numero_formateado
    
    def calcular_totales(self):
        """Calcula y actualiza el total de la cotización basado en sus items"""
        from django.db.models import Sum
        total_items = self.items.aggregate(
            total=Sum(F('cantidad') * F('precio_unitario'))
        )['total'] or Decimal('0.00')
        
        self.total = total_items
        self.save(update_fields=['total'])
        return self.total
    
    def __str__(self):
        return self.numero

class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('pendiente', 'Pendiente'),
        ('proceso', 'En Proceso'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
        ('en_proceso', 'En Proceso'),  # Por compatibilidad
    ]
    
    numero = models.CharField(max_length=20, unique=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    asignado_a = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos_asignados')
    
    def calcular_totales(self):
        """Calcula y actualiza el total del pedido basado en sus items"""
        from django.db.models import Sum
        total_items = self.items.aggregate(
            total=Sum(F('cantidad') * F('precio_unitario'))
        )['total'] or Decimal('0.00')
        
        self.total = total_items
        self.save(update_fields=['total'])
        return self.total
    
    def __str__(self):
        return self.numero

class Factura(models.Model):
    numero = models.CharField(max_length=20, unique=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='borrador')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.generar_numero()
        super().save(*args, **kwargs)
    
    def generar_numero(self):
        """Genera un número único para la factura"""
        from datetime import datetime
        
        # Obtener año actual
        año_actual = datetime.now().year
        
        # Buscar el último número del año
        prefijo = f"FAC{año_actual}"
        
        ultimas_facturas = Factura.objects.filter(
            numero__startswith=prefijo
        ).order_by('-numero')
        
        if ultimas_facturas.exists():
            ultimo_numero = ultimas_facturas.first().numero
            try:
                # Extraer el número secuencial
                numero_secuencial = int(ultimo_numero.replace(prefijo, ""))
                nuevo_numero = numero_secuencial + 1
            except (ValueError, IndexError):
                nuevo_numero = 1
        else:
            nuevo_numero = 1
        
        # Formatear con ceros a la izquierda
        return f"{prefijo}{nuevo_numero:06d}"
    
    def __str__(self):
        return self.numero

class ItemCotizacion(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey('inventario.Producto', on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario
    
    def __str__(self):
        return f"{self.producto.nombre} - {self.cotizacion.numero}"

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey('inventario.Producto', on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario
    
    def __str__(self):
        return f"{self.producto.nombre} - {self.pedido.numero}"

class ItemFactura(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    def __str__(self):
        return f"Item {self.factura.numero}"

class Entrega(models.Model):
    numero = models.CharField(max_length=20, unique=True)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='entregas')
    repartidor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    direccion_entrega = models.TextField()
    telefono_contacto = models.CharField(max_length=20)
    fecha_programada = models.DateTimeField()
    estado = models.CharField(max_length=20, default='programada')
    
    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.generar_numero()
        super().save(*args, **kwargs)
    
    def generar_numero(self):
        """Genera un número único para la entrega"""
        from datetime import datetime
        
        # Obtener año actual
        año_actual = datetime.now().year
        
        # Buscar el último número del año
        prefijo = f"ENT{año_actual}"
        
        ultimas_entregas = Entrega.objects.filter(
            numero__startswith=prefijo
        ).order_by('-numero')
        
        if ultimas_entregas.exists():
            ultimo_numero = ultimas_entregas.first().numero
            try:
                # Extraer el número secuencial
                parte_numerica = ultimo_numero.replace(prefijo, '').lstrip('0') or '0'
                siguiente_numero = int(parte_numerica) + 1
            except ValueError:
                siguiente_numero = 1
        else:
            siguiente_numero = 1
        
        # Formatear con ceros a la izquierda
        numero_formateado = f"{prefijo}{siguiente_numero:03d}"
        
        # Verificar que no exista
        while Entrega.objects.filter(numero=numero_formateado).exists():
            siguiente_numero += 1
            numero_formateado = f"{prefijo}{siguiente_numero:03d}"
        
        return numero_formateado
    
    def __str__(self):
        return self.numero
    
    def get_items_disponibles(self):
        """Obtiene los items del pedido que pueden ser rechazados"""
        return self.pedido.items.all()
    
    def get_total_rechazado(self):
        """Calcula el valor total de items rechazados"""
        total = sum(item.valor_rechazado for item in self.items_rechazados.all())
        return total
    
    def get_items_entregados_efectivamente(self):
        """Obtiene los items que efectivamente se entregaron (no rechazados)"""
        items_entregados = []
        for item in self.pedido.items.all():
            # Verificar si hay rechazo para este item
            rechazo = self.items_rechazados.filter(item_pedido=item).first()
            if rechazo:
                cantidad_entregada = item.cantidad - rechazo.cantidad_rechazada
                if cantidad_entregada > 0:
                    items_entregados.append({
                        'item': item,
                        'cantidad_entregada': cantidad_entregada,
                        'cantidad_rechazada': rechazo.cantidad_rechazada
                    })
            else:
                items_entregados.append({
                    'item': item,
                    'cantidad_entregada': item.cantidad,
                    'cantidad_rechazada': 0
                })
        return items_entregados
    
    def tiene_items_rechazados(self):
        """Verifica si la entrega tiene items rechazados"""
        return self.items_rechazados.exists()


class ItemRechazado(models.Model):
    """Modelo para registrar items rechazados por el cliente durante la entrega"""
    
    MOTIVOS_RECHAZO = [
        ('defectuoso', 'Producto defectuoso'),
        ('incorrecto', 'Producto incorrecto'),
        ('no_solicitado', 'No fue solicitado'),
        ('cambio_opinion', 'Cliente cambió de opinión'),
        ('precio', 'Problema con el precio'),
        ('otro', 'Otro motivo'),
    ]
    
    entrega = models.ForeignKey(Entrega, on_delete=models.CASCADE, related_name='items_rechazados')
    item_pedido = models.ForeignKey(ItemPedido, on_delete=models.CASCADE)
    cantidad_rechazada = models.DecimalField(max_digits=10, decimal_places=2, help_text="Cantidad del item que fue rechazada")
    motivo = models.CharField(max_length=20, choices=MOTIVOS_RECHAZO, default='otro')
    observaciones = models.TextField(blank=True, help_text="Observaciones adicionales sobre el rechazo")
    fecha_rechazo = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Item Rechazado"
        verbose_name_plural = "Items Rechazados"
        unique_together = [['entrega', 'item_pedido']]  # Un item solo puede ser rechazado una vez por entrega
    
    def __str__(self):
        return f"{self.item_pedido.producto.nombre} - {self.cantidad_rechazada} rechazado(s) en {self.entrega.numero}"
    
    @property
    def valor_rechazado(self):
        """Calcula el valor monetario de los items rechazados"""
        return self.cantidad_rechazada * self.item_pedido.precio_unitario
