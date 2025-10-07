from django.db import models
from django.contrib.auth import get_    # Ubicación - Solo URL de Google Maps
    enlace_maps = models.URLField(blank=False, verbose_name='URL de Google Maps',
                                help_text='URL completa de Google Maps con la ubicación del cliente')
    
    # Comercialom django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from inventario.models import Producto, VarianteProducto, Stock, Bodega, MovimientoInventario
from django.utils import timezone
import uuid

User = get_user_model()

class Departamento(models.Model):
    """Modelo para departamentos/estados"""
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=10, unique=True, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Departamento'
        verbose_name_plural = 'Departamentos'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class Ciudad(models.Model):
    """Modelo para ciudades/municipios"""
    nombre = models.CharField(max_length=100)
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='ciudades')
    codigo_postal = models.CharField(max_length=10, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Ciudad'
        verbose_name_plural = 'Ciudades'
        ordering = ['departamento__nombre', 'nombre']
        unique_together = ['nombre', 'departamento']
    
    def __str__(self):
        return f"{self.nombre}, {self.departamento.nombre}"

class Cliente(models.Model):
    """Modelo para gestión de clientes"""
    TIPO_DOCUMENTO_CHOICES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('NIT', 'NIT'),
        ('CE', 'Cédula de Extranjería'),
        ('PAS', 'Pasaporte'),
    ]
    
    TIPO_CLIENTE_CHOICES = [
        ('minorista', 'Minorista'),
        ('mayorista', 'Mayorista'),
        ('corporativo', 'Corporativo'),
    ]
    
    # Información básica
    tipo_documento = models.CharField(max_length=3, choices=TIPO_DOCUMENTO_CHOICES, default='CC')
    numero_documento = models.CharField(max_length=20, unique=True, verbose_name='Número de documento')
    nombre_completo = models.CharField(max_length=200, verbose_name='Nombre completo')
    nombre_comercial = models.CharField(max_length=200, blank=True, verbose_name='Nombre comercial')
    
    # Contacto
    telefono = models.CharField(max_length=20, verbose_name='Teléfono')
    email = models.EmailField(blank=True, verbose_name='Email')
    direccion = models.TextField(verbose_name='Dirección')
    ciudad = models.CharField(max_length=100, default='Bogotá', verbose_name='Ciudad')
    departamento = models.CharField(max_length=100, default='Cundinamarca', verbose_name='Departamento')
    
    # Ubicación - Solo URL de Google Maps
    enlace_maps = models.URLField(blank=False, verbose_name='URL de Google Maps',
                                help_text='URL completa de Google Maps con la ubicación del cliente')
    
    # Comercial
    tipo_cliente = models.CharField(max_length=20, choices=TIPO_CLIENTE_CHOICES, default='minorista')
    vendedor_asignado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                         limit_choices_to={'role__in': ['vendedor', 'administrador']})
    limite_credito = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'),
                                       validators=[MinValueValidator(Decimal('0.00'))])
    dias_credito = models.PositiveIntegerField(default=0, verbose_name='Días de crédito')
    
    # Control
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='clientes_creados')
    
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre_completo']
    
    def __str__(self):
        return f"{self.numero_documento} - {self.nombre_completo}"
    
    @property
    def nombre_display(self):
        """Nombre para mostrar (comercial o completo)"""
        return self.nombre_comercial or self.nombre_completo

class DocumentoVenta(models.Model):
    """Clase base para documentos de venta"""
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('enviada', 'Enviada'),
        ('pendiente', 'Pendiente'),
        ('proceso', 'En Proceso'),
        ('completado', 'Completado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero = models.CharField(max_length=20, unique=True, verbose_name='Número')
    fecha = models.DateTimeField(auto_now_add=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    vendedor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                               limit_choices_to={'role__in': ['vendedor', 'administrador']})
    
    # Totales
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'),
                                             validators=[MinValueValidator(Decimal('0.00')), 
                                                       MaxValueValidator(Decimal('100.00'))])
    descuento_valor = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    impuestos = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Estado y control
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador')
    observaciones = models.TextField(blank=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        ordering = ['-fecha']
    
    @property
    def numero_documento(self):
        """Devuelve el número del documento para compatibilidad con templates"""
        return self.numero
    
    @property
    def valor_iva(self):
        """Calcula el valor del IVA (19%)"""
        return self.subtotal * Decimal('0.19')
    
    @property
    def porcentaje_iva(self):
        """Porcentaje de IVA"""
        return 19
    
    def calcular_totales(self):
        """Calcula los totales del documento"""
        items = self.items.all()
        # Convertir el resultado de sum() a Decimal
        self.subtotal = Decimal(str(sum(item.total for item in items) or 0))
        
        # Calcular descuento
        if self.descuento_porcentaje > 0:
            self.descuento_valor = (self.subtotal * self.descuento_porcentaje) / Decimal('100')
        else:
            self.descuento_valor = Decimal('0.00')
        
        # Calcular IVA sobre el subtotal menos descuento
        base_iva = self.subtotal - self.descuento_valor
        self.impuestos = base_iva * Decimal('0.19')
        
        self.total = self.subtotal - self.descuento_valor + self.impuestos
        self.save()

class Cotizacion(DocumentoVenta):
    """Cotización - Primera etapa del proceso de venta"""
    fecha_vencimiento = models.DateField(verbose_name='Fecha de vencimiento')
    convertida_a_pedido = models.BooleanField(default=False)
    oportunidad_origen = models.ForeignKey(
        'crm.Oportunidad', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='cotizaciones',
        verbose_name='Oportunidad de Origen'
    )
    
    class Meta:
        verbose_name = 'Cotización'
        verbose_name_plural = 'Cotizaciones'
    
    def __str__(self):
        return f"COT-{self.numero} - {self.cliente.nombre_display}"
    
    def save(self, *args, **kwargs):
        if not self.numero:
            # Generar número de cotización
            ultimo = Cotizacion.objects.order_by('-numero').first()
            if ultimo and ultimo.numero.isdigit():
                nuevo_numero = int(ultimo.numero) + 1
            else:
                nuevo_numero = 1
            self.numero = f"{nuevo_numero:06d}"
        super().save(*args, **kwargs)

class Pedido(DocumentoVenta):
    """Pedido - Segunda etapa del proceso de venta"""
    cotizacion_origen = models.ForeignKey(Cotizacion, on_delete=models.SET_NULL, null=True, blank=True)
    oportunidad_origen = models.ForeignKey(
        'crm.Oportunidad', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='pedidos',
        verbose_name='Oportunidad de Origen'
    )
    fecha_entrega_estimada = models.DateField(null=True, blank=True)
    bodega = models.ForeignKey(Bodega, on_delete=models.CASCADE, verbose_name='Bodega de despacho')
    asignado_a = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='pedidos_asignados',
        verbose_name='Asignado a',
        help_text='Bodeguero asignado para el alistamiento del pedido'
    )
    
    # Campos para ventas inmediatas
    entrega_inmediata = models.BooleanField(default=False, verbose_name='Entrega inmediata', 
                                          help_text='Marca si fue entrega inmediata en punto de venta')
    fecha_entrega = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de entrega',
                                       help_text='Fecha y hora real de entrega del pedido')
    
    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
    
    def __str__(self):
        return f"PED-{self.numero} - {self.cliente.nombre_display}"
    
    def save(self, *args, **kwargs):
        if not self.numero:
            # Generar número de pedido
            ultimo = Pedido.objects.order_by('-numero').first()
            if ultimo and ultimo.numero.isdigit():
                nuevo_numero = int(ultimo.numero) + 1
            else:
                nuevo_numero = 1
            self.numero = f"{nuevo_numero:06d}"
        super().save(*args, **kwargs)
    
    def reservar_stock(self):
        """Reserva el stock de los productos del pedido"""
        from django.db import transaction
        
        with transaction.atomic():
            for item in self.items.all():
                try:
                    stock = Stock.objects.select_for_update().get(
                        producto=item.producto,
                        variante=item.variante,
                        bodega=self.bodega
                    )
                    
                    # Usar el nuevo método de reserva con trazabilidad
                    if not stock.reservar(
                        cantidad=int(item.cantidad),
                        usuario=self.vendedor,
                        pedido_id=self.id,
                        observaciones=f"Reserva para pedido {self.numero}"
                    ):
                        raise ValueError(f"Stock insuficiente para {item.producto.nombre}")
                        
                except Stock.DoesNotExist:
                    # Crear stock con cantidad 0 si no existe
                    Stock.objects.create(
                        producto=item.producto,
                        variante=item.variante,
                        bodega=self.bodega,
                        cantidad=0,
                        cantidad_reservada=0
                    )
                    raise ValueError(f"No hay stock disponible para {item.producto.nombre}")
    
    def liberar_stock(self):
        """Libera el stock reservado del pedido"""
        from django.db import transaction
        
        with transaction.atomic():
            for item in self.items.all():
                try:
                    stock = Stock.objects.select_for_update().get(
                        producto=item.producto,
                        variante=item.variante,
                        bodega=self.bodega
                    )
                    
                    # Usar el nuevo método de liberación con trazabilidad
                    stock.liberar_reserva(
                        cantidad=int(item.cantidad),
                        usuario=self.vendedor,
                        pedido_id=self.id,
                        observaciones=f"Liberación de reserva del pedido {self.numero}"
                    )
                    
                except Stock.DoesNotExist:
                    pass  # Si no existe el stock, no hay nada que liberar
    
    def confirmar_venta(self):
        """Confirma la venta descontando del stock físico"""
        from django.db import transaction
        
        with transaction.atomic():
            for item in self.items.all():
                try:
                    stock = Stock.objects.select_for_update().get(
                        producto=item.producto,
                        variante=item.variante,
                        bodega=self.bodega
                    )
                    
                    # Confirmar venta con trazabilidad completa
                    if not stock.confirmar_venta(
                        cantidad=int(item.cantidad),
                        usuario=self.vendedor,
                        pedido_id=self.id,
                        observaciones=f"Venta confirmada del pedido {self.numero}"
                    ):
                        raise ValueError(f"Error al confirmar venta de {item.producto.nombre}")
                        
                except Stock.DoesNotExist:
                    raise ValueError(f"No existe stock para {item.producto.nombre}")
            
            # Actualizar estado del pedido
            self.estado = 'completado'
            if self.entrega_inmediata:
                self.fecha_entrega = timezone.now()
                self.estado = 'entregado'
            self.save()
    
    def _confirmar_venta_stock(self):
        """Confirma solo el stock sin cambiar el estado del pedido (para usar en signals)"""
        from django.db import transaction
        
        with transaction.atomic():
            for item in self.items.all():
                try:
                    stock = Stock.objects.select_for_update().get(
                        producto=item.producto,
                        variante=item.variante,
                        bodega=self.bodega
                    )
                    
                    # Confirmar venta con trazabilidad completa
                    if not stock.confirmar_venta(
                        cantidad=int(item.cantidad),
                        usuario=self.vendedor,
                        pedido_id=self.id,
                        observaciones=f"Venta confirmada del pedido {self.numero}"
                    ):
                        raise ValueError(f"Error al confirmar venta de {item.producto.nombre}")
                        
                except Stock.DoesNotExist:
                    raise ValueError(f"No existe stock para {item.producto.nombre}")
            
            # Actualizar campos adicionales sin cambiar estado
            if self.entrega_inmediata:
                self.fecha_entrega = timezone.now()
    
    def _revertir_venta(self):
        """Revierte una venta cancelada reintegrando al stock"""
        from django.db import transaction
        
        with transaction.atomic():
            for item in self.items.all():
                try:
                    stock = Stock.objects.select_for_update().get(
                        producto=item.producto,
                        variante=item.variante,
                        bodega=self.bodega
                    )
                    
                    # Reintegrar al stock físico
                    stock.cantidad += int(item.cantidad)
                    stock.save()
                    
                    # Registrar movimiento de reintegro
                    MovimientoInventario.objects.create(
                        producto=item.producto,
                        variante=item.variante,
                        bodega=self.bodega,
                        tipo_movimiento='entrada',
                        motivo='devolucion_cliente',
                        cantidad=int(item.cantidad),
                        costo_unitario=item.producto.costo_promedio,
                        usuario=self.vendedor,
                        pedido_referencia=self.id,
                        documento_referencia=f"CANCEL-{self.numero}",
                        observaciones=f"Reversión por cancelación del pedido {self.numero}"
                    )
                    
                except Stock.DoesNotExist:
                    # Crear el stock si no existe
                    Stock.objects.create(
                        producto=item.producto,
                        variante=item.variante,
                        bodega=self.bodega,
                        cantidad=int(item.cantidad),
                        cantidad_reservada=0
                    )

class Factura(DocumentoVenta):
    """Factura - Tercera etapa del proceso de venta"""
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('emitida', 'Emitida'),
        ('pagada', 'Pagada'),
        ('vencida', 'Vencida'),
        ('anulada', 'Anulada'),
    ]
    
    pedido_origen = models.ForeignKey(Pedido, on_delete=models.CASCADE, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador')
    
    # Datos fiscales
    prefijo = models.CharField(max_length=10, default='SETT')
    numero_fiscal = models.CharField(max_length=20, unique=True, verbose_name='Número fiscal', blank=True)
    cufde = models.CharField(max_length=255, blank=True, verbose_name='CUFE/CUFDE')  # Para DIAN
    qr_code = models.TextField(blank=True, verbose_name='Código QR')
    
    # Datos de pago
    fecha_vencimiento = models.DateField(verbose_name='Fecha de vencimiento', null=True, blank=True)
    fecha_pago = models.DateField(verbose_name='Fecha de pago', null=True, blank=True)
    metodo_pago = models.CharField(max_length=50, blank=True, choices=[
        ('contado', 'Contado'),
        ('credito', 'Crédito'),
        ('transferencia', 'Transferencia'),
        ('cheque', 'Cheque'),
        ('tarjeta', 'Tarjeta'),
    ], default='contado')
    
    # Referencias adicionales
    orden_compra = models.CharField(max_length=50, blank=True, verbose_name='Orden de compra')
    nota_interna = models.TextField(blank=True, verbose_name='Nota interna')
    
    class Meta:
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"FACT-{self.numero} - {self.cliente.nombre_display}"
    
    def save(self, *args, **kwargs):
        if not self.numero:
            # Generar número de factura
            ultimo = Factura.objects.order_by('-numero').first()
            if ultimo and ultimo.numero.isdigit():
                nuevo_numero = int(ultimo.numero) + 1
            else:
                nuevo_numero = 1
            self.numero = f"{nuevo_numero:06d}"
        
        if not self.numero_fiscal:
            self.numero_fiscal = f"{self.prefijo}{self.numero}"
        
        # Establecer fecha si no existe
        if not self.fecha:
            from datetime import date
            self.fecha = date.today()
        
        # Auto-calcular fecha de vencimiento si no está establecida
        if not self.fecha_vencimiento and self.cliente and self.cliente.dias_credito:
            from datetime import timedelta
            self.fecha_vencimiento = self.fecha + timedelta(days=self.cliente.dias_credito)
        
        super().save(*args, **kwargs)
    
    @property
    def esta_vencida(self):
        """Verifica si la factura está vencida"""
        if not self.fecha_vencimiento or self.estado in ['pagada', 'anulada']:
            return False
        from datetime import date
        return date.today() > self.fecha_vencimiento
    
    @property
    def dias_vencimiento(self):
        """Días hasta el vencimiento (negativo si ya venció)"""
        if not self.fecha_vencimiento:
            return None
        from datetime import date
        delta = self.fecha_vencimiento - date.today()
        return delta.days
    
    def marcar_pagada(self, fecha_pago=None):
        """Marca la factura como pagada"""
        from datetime import date
        self.estado = 'pagada'
        self.fecha_pago = fecha_pago or date.today()
        self.save()
    
    def anular(self):
        """Anula la factura"""
        if self.estado == 'pagada':
            raise ValueError("No se puede anular una factura pagada")
        self.estado = 'anulada'
        self.save()
    
    def generar_cufe(self):
        """Genera el CUFE para integración con DIAN (placeholder)"""
        import hashlib
        data = f"{self.numero_fiscal}{self.fecha}{self.cliente.numero_documento}{self.total}"
        return hashlib.md5(data.encode()).hexdigest().upper()[:16]

class ItemDocumento(models.Model):
    """Clase base para items de documentos"""
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    variante = models.ForeignKey(VarianteProducto, on_delete=models.CASCADE, null=True, blank=True)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2,
                                        validators=[MinValueValidator(Decimal('0.01'))])
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'),
                                             validators=[MinValueValidator(Decimal('0.00')), 
                                                       MaxValueValidator(Decimal('100.00'))])
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        # Calcular total del item usando Decimal para evitar errores de tipo
        subtotal = self.cantidad * self.precio_unitario
        descuento = (subtotal * self.descuento_porcentaje) / Decimal('100')
        self.total = subtotal - descuento
        super().save(*args, **kwargs)
    
    @property
    def subtotal(self):
        """Subtotal sin descuento"""
        return self.cantidad * self.precio_unitario
    
    def __str__(self):
        producto_str = f"{self.producto.codigo} - {self.producto.nombre}"
        if self.variante:
            producto_str += f" ({self.variante.valor})"
        return f"{producto_str} x{self.cantidad}"

class ItemCotizacion(ItemDocumento):
    """Item de cotización"""
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items')
    
    class Meta:
        verbose_name = 'Item de cotización'
        verbose_name_plural = 'Items de cotización'

class ItemPedido(ItemDocumento):
    """Item de pedido"""
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    
    class Meta:
        verbose_name = 'Item de pedido'
        verbose_name_plural = 'Items de pedido'

class ItemFactura(ItemDocumento):
    """Item de factura"""
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='items')
    
    class Meta:
        verbose_name = 'Item de factura'
        verbose_name_plural = 'Items de factura'


# ============= ENTREGAS =============

class Entrega(models.Model):
    """Modelo para gestionar entregas de pedidos por repartidores"""
    ESTADO_CHOICES = [
        ('programada', 'Programada'),
        ('en_camino', 'En Camino'),
        ('entregado', 'Entregado'),
        ('fallido', 'Entrega Fallida'),
        ('devuelto', 'Devuelto'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='entrega')
    repartidor = models.ForeignKey(User, on_delete=models.CASCADE, 
                                  limit_choices_to={'role': 'repartidor'},
                                  related_name='entregas_asignadas')
    
    # Datos de programación
    fecha_programada = models.DateTimeField(verbose_name='Fecha programada')
    fecha_salida = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de salida')
    fecha_entrega = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de entrega real')
    
    # Estado y seguimiento
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='programada')
    direccion_entrega = models.TextField(verbose_name='Dirección de entrega')
    telefono_contacto = models.CharField(max_length=20, verbose_name='Teléfono de contacto')
    persona_recibe = models.CharField(max_length=200, blank=True, verbose_name='Persona que recibe')
    
    # Evidencia de entrega
    firma_digital = models.TextField(blank=True, verbose_name='Firma digital (base64)')
    foto_evidencia = models.ImageField(upload_to='entregas/evidencias/%Y/%m/', 
                                     blank=True, null=True,
                                     verbose_name='Foto de evidencia')
    
    # Observaciones y comentarios
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    motivo_fallo = models.TextField(blank=True, verbose_name='Motivo de fallo de entrega')
    
    # Control
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Entrega'
        verbose_name_plural = 'Entregas'
        ordering = ['-fecha_programada']
    
    def __str__(self):
        return f"Entrega {self.pedido.numero} - {self.get_estado_display()}"
    
    def marcar_en_camino(self):
        """Marca la entrega como en camino"""
        from django.utils import timezone
        self.estado = 'en_camino'
        self.fecha_salida = timezone.now()
        self.save()
    
    def marcar_entregado(self, persona_recibe=None, firma=None, observaciones=None):
        """Marca la entrega como completada"""
        from django.utils import timezone
        self.estado = 'entregado'
        self.fecha_entrega = timezone.now()
        if persona_recibe:
            self.persona_recibe = persona_recibe
        if firma:
            self.firma_digital = firma
        if observaciones:
            self.observaciones = observaciones
        self.save()
        
        # Actualizar el pedido a entregado
        self.pedido.estado = 'entregado'
        self.pedido.fecha_entrega = self.fecha_entrega
        self.pedido.save()
    
    def marcar_fallido(self, motivo):
        """Marca la entrega como fallida"""
        self.estado = 'fallido'
        self.motivo_fallo = motivo
        self.save()
    
    @property
    def tiempo_estimado_entrega(self):
        """Tiempo estimado desde salida hasta entrega"""
        if self.fecha_salida and self.fecha_entrega:
            return self.fecha_entrega - self.fecha_salida
        return None
    
    @property
    def cliente(self):
        """Acceso directo al cliente del pedido"""
        return self.pedido.cliente
    
    @classmethod
    def asignar_repartidor_automatico(cls, pedido, fecha_programada=None):
        """Asigna automáticamente el repartidor más cercano disponible"""
        from django.utils import timezone
        
        if fecha_programada is None:
            fecha_programada = timezone.now() + timezone.timedelta(hours=24)
        
        # Buscar repartidor más cercano
        resultado = User.encontrar_repartidor_mas_cercano(pedido.cliente)
        
        if not resultado['repartidor']:
            # Si no hay repartidor por GPS, asignar el primer disponible
            repartidor_disponible = User.objects.filter(
                role='repartidor',
                activo=True,
                disponible_entregas=True
            ).first()
            
            if not repartidor_disponible:
                raise ValueError("No hay repartidores disponibles para la entrega")
            
            resultado['repartidor'] = repartidor_disponible
            resultado['distancia'] = None
        
        # Crear la entrega
        entrega = cls.objects.create(
            pedido=pedido,
            repartidor=resultado['repartidor'],
            fecha_programada=fecha_programada,
            direccion_entrega=pedido.cliente.direccion or 'Dirección no especificada',
            telefono_contacto=pedido.cliente.telefono or 'Sin teléfono'
        )
        
        return entrega, resultado['distancia']
    
    def distancia_al_cliente(self):
        """Calcula la distancia entre el repartidor y el cliente"""
        return self.repartidor.calcular_distancia_cliente(self.cliente)
    
    def reasignar_repartidor_cercano(self):
        """Reasigna a un repartidor más cercano si está disponible"""
        resultado = User.encontrar_repartidor_mas_cercano(self.cliente)
        
        if resultado['repartidor'] and resultado['repartidor'] != self.repartidor:
            # Solo reasignar si el estado permite (programada o fallido)
            if self.estado in ['programada', 'fallido']:
                self.repartidor = resultado['repartidor']
                self.save(update_fields=['repartidor'])
                return True, resultado['distancia']
        
        return False, None
