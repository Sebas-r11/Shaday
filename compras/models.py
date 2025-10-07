import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db.models import Sum, F

User = get_user_model()

class TipoDocumentoProveedor(models.TextChoices):
    """Tipos de documento para proveedores"""
    NIT = 'NIT', 'NIT'
    CC = 'CC', 'Cédula de Ciudadanía'
    CE = 'CE', 'Cédula de Extranjería'
    PAS = 'PAS', 'Pasaporte'
    RUT = 'RUT', 'RUT'

class EstadoSolicitudCompra(models.TextChoices):
    """Estados de las solicitudes de compra"""
    BORRADOR = 'borrador', 'Borrador'
    PENDIENTE = 'pendiente', 'Pendiente de Aprobación'
    APROBADA = 'aprobada', 'Aprobada'
    RECHAZADA = 'rechazada', 'Rechazada'
    CONVERTIDA = 'convertida', 'Convertida a OC'
    CANCELADA = 'cancelada', 'Cancelada'

class PrioridadCompra(models.TextChoices):
    """Prioridades para solicitudes de compra"""
    BAJA = 'baja', 'Baja'
    MEDIA = 'media', 'Media'
    ALTA = 'alta', 'Alta'
    URGENTE = 'urgente', 'Urgente'

class EstadoOrdenCompra(models.TextChoices):
    """Estados de las órdenes de compra"""
    BORRADOR = 'borrador', 'Borrador'
    ENVIADA = 'enviada', 'Enviada al Proveedor'
    CONFIRMADA = 'confirmada', 'Confirmada por Proveedor'
    RECIBIDA_PARCIAL = 'recibida_parcial', 'Recibida Parcialmente'
    RECIBIDA_TOTAL = 'recibida_total', 'Recibida Totalmente'
    CANCELADA = 'cancelada', 'Cancelada'

class CondicionesPago(models.TextChoices):
    """Condiciones de pago para proveedores"""
    CONTADO = 'contado', 'Contado'
    CREDITO_8 = 'credito_8', '8 días'
    CREDITO_15 = 'credito_15', '15 días'
    CREDITO_30 = 'credito_30', '30 días'
    CREDITO_45 = 'credito_45', '45 días'
    CREDITO_60 = 'credito_60', '60 días'
    CREDITO_90 = 'credito_90', '90 días'

# ============= MODELOS PRINCIPALES =============

class SolicitudCompra(models.Model):
    """Modelo para solicitudes de compra internas"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Información básica
    numero = models.CharField(max_length=20, unique=True, verbose_name='Número de Solicitud')
    titulo = models.CharField(max_length=200, verbose_name='Título de la Solicitud')
    descripcion = models.TextField(verbose_name='Descripción')
    
    # Estado y prioridad
    estado = models.CharField(
        max_length=20, 
        choices=EstadoSolicitudCompra.choices, 
        default=EstadoSolicitudCompra.BORRADOR,
        verbose_name='Estado'
    )
    prioridad = models.CharField(
        max_length=20, 
        choices=PrioridadCompra.choices, 
        default=PrioridadCompra.MEDIA,
        verbose_name='Prioridad'
    )
    
    # Fechas
    fecha_solicitud = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Solicitud')
    fecha_requerida = models.DateField(verbose_name='Fecha Requerida')
    fecha_aprobacion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Aprobación')
    
    # Usuarios involucrados
    solicitante = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='solicitudes_compra_creadas',
        verbose_name='Solicitante'
    )
    aprobado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='solicitudes_compra_aprobadas',
        verbose_name='Aprobado por'
    )
    
    # Área/Departamento solicitante
    departamento = models.CharField(
        max_length=100, 
        verbose_name='Departamento Solicitante'
    )
    centro_costo = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name='Centro de Costo'
    )
    
    # Información adicional
    justificacion = models.TextField(verbose_name='Justificación de la Compra')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    observaciones_aprobacion = models.TextField(
        blank=True, 
        verbose_name='Observaciones de Aprobación'
    )
    
    # Total estimado
    presupuesto_estimado = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Presupuesto Estimado'
    )
    
    # Referencias
    orden_compra_generada = models.ForeignKey(
        'OrdenCompra', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Orden de Compra Generada'
    )
    
    class Meta:
        verbose_name = 'Solicitud de Compra'
        verbose_name_plural = 'Solicitudes de Compra'
        ordering = ['-fecha_solicitud']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['estado', 'fecha_solicitud']),
            models.Index(fields=['solicitante', 'estado']),
        ]
    
    def __str__(self):
        return f"SOL-{self.numero} - {self.titulo}"
    
    def get_absolute_url(self):
        return reverse('compras:solicitud_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        if not self.numero:
            # Generar número consecutivo
            ultimo = SolicitudCompra.objects.order_by('-numero').first()
            if ultimo and ultimo.numero.isdigit():
                nuevo_numero = int(ultimo.numero) + 1
            else:
                nuevo_numero = 1
            self.numero = f"{nuevo_numero:06d}"
        super().save(*args, **kwargs)
    
    @property
    def estado_display_color(self):
        """Color CSS para el estado"""
        colors = {
            'borrador': 'bg-gray-100 text-gray-800',
            'pendiente': 'bg-yellow-100 text-yellow-800',
            'aprobada': 'bg-green-100 text-green-800',
            'rechazada': 'bg-red-100 text-red-800',
            'convertida': 'bg-blue-100 text-blue-800',
            'cancelada': 'bg-red-100 text-red-800',
        }
        return colors.get(self.estado, 'bg-gray-100 text-gray-800')
    
    @property
    def prioridad_display_color(self):
        """Color CSS para la prioridad"""
        colors = {
            'baja': 'bg-gray-100 text-gray-800',
            'media': 'bg-blue-100 text-blue-800',
            'alta': 'bg-yellow-100 text-yellow-800',
            'urgente': 'bg-red-100 text-red-800',
        }
        return colors.get(self.prioridad, 'bg-gray-100 text-gray-800')
    
    def puede_aprobarse(self):
        """Verificar si la solicitud puede ser aprobada"""
        return self.estado in ['pendiente']
    
    def puede_convertirse_oc(self):
        """Verificar si puede convertirse en orden de compra"""
        return self.estado == 'aprobada' and not self.orden_compra_generada
    
    def aprobar(self, usuario, observaciones=""):
        """Aprobar la solicitud"""
        if not self.puede_aprobarse():
            raise ValueError(f"No se puede aprobar una solicitud en estado {self.get_estado_display()}")
        
        self.estado = EstadoSolicitudCompra.APROBADA
        self.aprobado_por = usuario
        self.fecha_aprobacion = timezone.now()
        self.observaciones_aprobacion = observaciones
        self.save()
        return True
    
    def rechazar(self, usuario, motivo):
        """Rechazar la solicitud"""
        if not self.puede_aprobarse():
            raise ValueError(f"No se puede rechazar una solicitud en estado {self.get_estado_display()}")
        
        self.estado = EstadoSolicitudCompra.RECHAZADA
        self.aprobado_por = usuario
        self.fecha_aprobacion = timezone.now()
        self.observaciones_aprobacion = motivo
        self.save()
        return True
    
    def enviar_a_aprobacion(self):
        """Enviar solicitud a aprobación"""
        if self.estado != EstadoSolicitudCompra.BORRADOR:
            raise ValueError(f"Solo se pueden enviar solicitudes en borrador, estado actual: {self.get_estado_display()}")
        
        # Verificar que tenga items
        if not self.items.exists():
            raise ValueError("La solicitud debe tener al menos un item para enviar a aprobación")
        
        self.estado = EstadoSolicitudCompra.PENDIENTE
        self.save()
        return True
    
    def calcular_total(self):
        """Calcular total estimado de la solicitud"""
        total = self.items.aggregate(
            total=models.Sum(
                models.F('cantidad') * models.F('precio_estimado'),
                output_field=models.DecimalField(max_digits=15, decimal_places=2)
            )
        )['total']
        return total or Decimal('0.00')
    
    def puede_ser_aprobada_por(self, usuario):
        """Verificar si el usuario puede aprobar esta solicitud"""
        if not usuario or not usuario.is_authenticated:
            return False
        
        # Superusuarios y staff pueden aprobar
        if usuario.is_superuser or usuario.is_staff:
            return True
        
        # Verificar grupos o roles específicos
        return usuario.groups.filter(name__in=['Aprobadores', 'Jefes', 'Administradores']).exists()
    
    def puede_ser_rechazada_por(self, usuario):
        """Verificar si el usuario puede rechazar esta solicitud"""
        return self.puede_ser_aprobada_por(usuario)
    
    def clean(self):
        """Validaciones personalizadas"""
        from django.core.exceptions import ValidationError
        from datetime import date
        
        super().clean()
        
        if self.fecha_requerida and self.fecha_requerida <= date.today():
            raise ValidationError({
                'fecha_requerida': 'La fecha requerida debe ser posterior a hoy'
            })
    
    def crear_orden_compra(self, proveedor, usuario_comprador):
        """Crear orden de compra desde solicitud aprobada"""
        if self.estado != EstadoSolicitudCompra.APROBADA:
            raise ValueError("Solo se pueden crear órdenes desde solicitudes aprobadas")
        
        if self.orden_compra_generada:
            raise ValueError("Ya existe una orden de compra generada para esta solicitud")
        
        # Importación tardía para evitar circular imports
        from decimal import Decimal
        
        # Crear la orden de compra
        orden = OrdenCompra.objects.create(
            proveedor=proveedor,
            numero=self._generar_numero_orden_desde_solicitud(),
            fecha_orden=timezone.now().date(),
            fecha_entrega_estimada=self.fecha_requerida,
            estado=EstadoOrdenCompra.BORRADOR,
            observaciones=f"Generada desde solicitud {self.numero}\n{self.observaciones}",
            usuario_creacion=usuario_comprador
        )
        
        # Crear items de la orden desde items de la solicitud
        for item_solicitud in self.items.all():
            # Solo crear items si hay producto asociado
            if item_solicitud.producto:
                ItemOrdenCompra.objects.create(
                    orden_compra=orden,
                    producto=item_solicitud.producto,
                    cantidad=item_solicitud.cantidad,
                    precio_unitario=item_solicitud.precio_estimado
                )
        
        # Actualizar referencia en la solicitud
        self.orden_compra_generada = orden
        self.save()
        
        # Recalcular totales de la orden
        orden.calcular_totales()
        
        return orden
    
    def _generar_numero_orden_desde_solicitud(self):
        """Generar número único para la orden"""
        from django.utils import timezone
        hoy = timezone.now().date()
        prefijo = f"OC-{hoy.strftime('%Y%m%d')}"
        
        # Buscar el último número del día
        ultima_orden = OrdenCompra.objects.filter(
            numero__startswith=prefijo
        ).order_by('-numero').first()
        
        if ultima_orden:
            try:
                ultimo_numero = int(ultima_orden.numero.split('-')[-1])
                siguiente = ultimo_numero + 1
            except (ValueError, IndexError):
                siguiente = 1
        else:
            siguiente = 1
        
        return f"{prefijo}-{siguiente:03d}"


class ItemSolicitudCompra(models.Model):
    """Items de las solicitudes de compra"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    solicitud = models.ForeignKey(
        SolicitudCompra, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name='Solicitud de Compra'
    )
    producto = models.ForeignKey(
        'inventario.Producto', 
        on_delete=models.PROTECT, 
        null=True,
        blank=True,
        verbose_name='Producto'
    )
    
    # Descripción del item (para productos no existentes en inventario)
    descripcion_item = models.TextField(verbose_name='Descripción del Item')
    especificaciones = models.TextField(
        blank=True, 
        verbose_name='Especificaciones Técnicas'
    )
    
    # Cantidad y unidad
    cantidad = models.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name='Cantidad'
    )
    unidad_medida = models.CharField(
        max_length=20, 
        default='UND',
        verbose_name='Unidad de Medida'
    )
    
    # Precios estimados
    precio_estimado = models.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0.0000'))],
        verbose_name='Precio Unitario Estimado'
    )
    total_estimado = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name='Total Estimado'
    )
    
    # Proveedor sugerido
    proveedor_sugerido = models.ForeignKey(
        'Proveedor', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Proveedor Sugerido'
    )
    
    # Observaciones
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    
    class Meta:
        verbose_name = 'Item Solicitud de Compra'
        verbose_name_plural = 'Items Solicitud de Compra'
    
    def __str__(self):
        descripcion = self.producto.nombre if self.producto else self.descripcion_item
        return f"{descripcion} - {self.cantidad}"
    
    def save(self, *args, **kwargs):
        # Calcular total estimado
        self.total_estimado = self.cantidad * self.precio_estimado
        super().save(*args, **kwargs)
        
        # Actualizar total de la solicitud
        if self.solicitud_id:
            self.actualizar_total_solicitud()
    
    def actualizar_total_solicitud(self):
        """Actualizar el presupuesto estimado de la solicitud"""
        total = self.solicitud.items.aggregate(
            total=Sum('total_estimado')
        )['total'] or Decimal('0.00')
        
        self.solicitud.presupuesto_estimado = total
        self.solicitud.save()

class Proveedor(models.Model):
    """Modelo para gestión de proveedores"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Información básica
    codigo = models.CharField(
        max_length=20, 
        unique=True, 
        blank=True,  # Permite que esté vacío en formularios
        verbose_name='Código Proveedor',
        help_text='Código único del proveedor (se genera automáticamente si se deja vacío)'
    )
    razon_social = models.CharField(max_length=200, verbose_name='Razón Social')
    nombre_comercial = models.CharField(
        max_length=200, 
        blank=True, 
        verbose_name='Nombre Comercial'
    )
    
    # Documento de identificación
    tipo_documento = models.CharField(
        max_length=10, 
        choices=TipoDocumentoProveedor.choices, 
        default=TipoDocumentoProveedor.NIT,
        verbose_name='Tipo de Documento'
    )
    numero_documento = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name='Número de Documento'
    )
    
    # Información de contacto
    telefono = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    email = models.EmailField(blank=True, verbose_name='Email')
    sitio_web = models.URLField(blank=True, verbose_name='Sitio Web')
    
    # Dirección
    direccion = models.TextField(verbose_name='Dirección')
    ciudad = models.ForeignKey(
        'ventas.Ciudad', 
        on_delete=models.PROTECT, 
        verbose_name='Ciudad'
    )
    codigo_postal = models.CharField(max_length=10, blank=True, verbose_name='Código Postal')
    
    # Información comercial
    condiciones_pago = models.CharField(
        max_length=20, 
        choices=CondicionesPago.choices, 
        default=CondicionesPago.CONTADO,
        verbose_name='Condiciones de Pago'
    )
    limite_credito = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Límite de Crédito'
    )
    descuento_comercial = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Descuento Comercial (%)',
        help_text='Descuento general otorgado por el proveedor'
    )
    
    # Contacto principal
    contacto_nombre = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name='Nombre del Contacto'
    )
    contacto_cargo = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name='Cargo del Contacto'
    )
    contacto_telefono = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name='Teléfono del Contacto'
    )
    contacto_email = models.EmailField(
        blank=True, 
        verbose_name='Email del Contacto'
    )
    
    # Información adicional
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha Creación')
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name='Última Actualización')
    usuario_creacion = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='proveedores_creados',
        verbose_name='Creado por'
    )
    
    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['razon_social']
        indexes = [
            models.Index(fields=['numero_documento']),
            models.Index(fields=['codigo']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre_display}"
    
    def get_absolute_url(self):
        return reverse('compras:proveedor_detail', kwargs={'pk': self.pk})
    
    @property
    def nombre_display(self):
        """Nombre a mostrar (comercial o razón social)"""
        return self.nombre_comercial if self.nombre_comercial else self.razon_social
    
    def save(self, *args, **kwargs):
        if not self.codigo:
            # Generar código automático PRV001, PRV002, etc.
            ultimo = Proveedor.objects.filter(codigo__startswith='PRV').order_by('codigo').last()
            if ultimo and ultimo.codigo.startswith('PRV'):
                try:
                    numero = int(ultimo.codigo[3:]) + 1
                    self.codigo = f"PRV{numero:03d}"
                except ValueError:
                    self.codigo = "PRV001"
            else:
                self.codigo = "PRV001"
        super().save(*args, **kwargs)

class OrdenCompra(models.Model):
    """Modelo para órdenes de compra"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Información básica
    numero = models.CharField(max_length=20, unique=True, verbose_name='Número de Orden')
    proveedor = models.ForeignKey(
        Proveedor, 
        on_delete=models.PROTECT, 
        related_name='ordenes_compra',
        verbose_name='Proveedor'
    )
    
    # Fechas importantes
    fecha_orden = models.DateField(default=timezone.now, verbose_name='Fecha de Orden')
    fecha_entrega_estimada = models.DateField(
        null=True, 
        blank=True, 
        verbose_name='Fecha Entrega Estimada'
    )
    fecha_entrega_real = models.DateField(
        null=True, 
        blank=True, 
        verbose_name='Fecha Entrega Real'
    )
    
    # Estado y control
    estado = models.CharField(
        max_length=20, 
        choices=EstadoOrdenCompra.choices, 
        default=EstadoOrdenCompra.BORRADOR,
        verbose_name='Estado'
    )
    
    # Información comercial
    subtotal = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name='Subtotal'
    )
    descuento_porcentaje = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Descuento (%)'
    )
    descuento_valor = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name='Valor Descuento'
    )
    impuestos = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name='Impuestos'
    )
    total = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name='Total'
    )
    
    # Información adicional
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    condiciones_especiales = models.TextField(
        blank=True, 
        verbose_name='Condiciones Especiales'
    )
    
    # Referencia externa
    numero_referencia_proveedor = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name='Número Referencia Proveedor',
        help_text='Número de cotización o referencia del proveedor'
    )
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha Creación')
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name='Última Actualización')
    usuario_creacion = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='ordenes_compra_creadas',
        verbose_name='Creado por'
    )
    
    # Campos de cancelación
    fecha_cancelacion = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name='Fecha de Cancelación'
    )
    motivo_cancelacion = models.TextField(
        blank=True, 
        verbose_name='Motivo de Cancelación'
    )
    usuario_cancelacion = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='ordenes_compra_canceladas',
        verbose_name='Cancelado por'
    )
    
    class Meta:
        verbose_name = 'Orden de Compra'
        verbose_name_plural = 'Órdenes de Compra'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['estado', 'fecha_orden']),
            models.Index(fields=['proveedor', 'estado']),
        ]
    
    def __str__(self):
        return f"OC-{self.numero} - {self.proveedor.nombre_display}"
    
    def get_absolute_url(self):
        return reverse('compras:orden_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        if not self.numero:
            # Generar número único basado en fecha y secuencia
            self.numero = self._generar_numero_orden()
        
        # Calcular totales
        self.calcular_totales()
        super().save(*args, **kwargs)
    
    def _generar_numero_orden(self):
        """Generar número único para la orden"""
        from django.utils import timezone
        hoy = timezone.now().date()
        prefijo = f"OC-{hoy.strftime('%Y%m%d')}"
        
        # Buscar el último número del día
        ultima_orden = OrdenCompra.objects.filter(
            numero__startswith=prefijo
        ).order_by('-numero').first()
        
        if ultima_orden:
            try:
                ultimo_numero = int(ultima_orden.numero.split('-')[-1])
                siguiente = ultimo_numero + 1
            except (ValueError, IndexError):
                siguiente = 1
        else:
            siguiente = 1
        
        return f"{prefijo}-{siguiente:03d}"
    
    def calcular_totales(self):
        """Calcular subtotal, descuentos y total"""
        items = self.items.all()
        self.subtotal = sum(item.total for item in items)
        
        # Calcular descuento
        if self.descuento_porcentaje > 0:
            self.descuento_valor = (self.subtotal * self.descuento_porcentaje) / 100
        
        # Total = subtotal - descuento + impuestos
        self.total = self.subtotal - self.descuento_valor + self.impuestos
    
    @property
    def estado_display_color(self):
        """Color CSS para el estado"""
        colors = {
            'borrador': 'bg-gray-100 text-gray-800',
            'enviada': 'bg-blue-100 text-blue-800',
            'confirmada': 'bg-green-100 text-green-800',
            'recibida_parcial': 'bg-yellow-100 text-yellow-800',
            'recibida_total': 'bg-green-100 text-green-800',
            'cancelada': 'bg-red-100 text-red-800',
        }
        return colors.get(self.estado, 'bg-gray-100 text-gray-800')
    
    @property
    def porcentaje_recibido(self):
        """Porcentaje de productos recibidos"""
        total_ordenado = sum(item.cantidad for item in self.items.all())
        if total_ordenado == 0:
            return 0
        
        total_recibido = sum(item.cantidad_recibida for item in self.items.all())
        return (total_recibido / total_ordenado) * 100
    
    def puede_cancelarse(self):
        """Verificar si la orden puede ser cancelada"""
        estados_cancelables = ['borrador', 'enviada', 'confirmada']
        return self.estado in estados_cancelables
    
    def cancelar(self, usuario, motivo):
        """Cancelar la orden de compra"""
        from django.utils import timezone
        
        if not self.puede_cancelarse():
            raise ValueError(f"No se puede cancelar una orden en estado {self.get_estado_display()}")
        
        self.estado = EstadoOrdenCompra.CANCELADA
        self.fecha_cancelacion = timezone.now()
        self.motivo_cancelacion = motivo
        self.usuario_cancelacion = usuario
        self.save()
        
        return True
    
    def actualizar_estado_por_recepcion(self):
        """Actualizar el estado de la orden basado en las recepciones"""
        if self.estado in ['cancelada']:
            return  # No actualizar órdenes canceladas
        
        # Verificar si todos los items han sido recibidos completamente
        items_completos = 0
        items_parciales = 0
        total_items = self.items.count()
        
        for item in self.items.all():
            if item.cantidad_recibida >= item.cantidad:
                items_completos += 1
            elif item.cantidad_recibida > 0:
                items_parciales += 1
        
        # Actualizar estado
        if items_completos == total_items and total_items > 0:
            self.estado = EstadoOrdenCompra.RECIBIDA_TOTAL
        elif items_parciales > 0 or items_completos > 0:
            self.estado = EstadoOrdenCompra.RECIBIDA_PARCIAL
        
        self.save()

class ItemOrdenCompra(models.Model):
    """Items de las órdenes de compra"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    orden_compra = models.ForeignKey(
        OrdenCompra, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name='Orden de Compra'
    )
    producto = models.ForeignKey(
        'inventario.Producto', 
        on_delete=models.PROTECT, 
        verbose_name='Producto'
    )
    variante = models.ForeignKey(
        'inventario.VarianteProducto', 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        verbose_name='Variante'
    )
    
    # Cantidades
    cantidad = models.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name='Cantidad Ordenada'
    )
    cantidad_recibida = models.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        default=Decimal('0.000'),
        verbose_name='Cantidad Recibida'
    )
    
    # Precios
    precio_unitario = models.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        validators=[MinValueValidator(Decimal('0.0001'))],
        verbose_name='Precio Unitario'
    )
    descuento_porcentaje = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Descuento (%)'
    )
    descuento_valor = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name='Descuento Valor'
    )
    total = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name='Total'
    )
    
    # Información adicional
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    
    class Meta:
        verbose_name = 'Item Orden de Compra'
        verbose_name_plural = 'Items Órdenes de Compra'
        unique_together = ['orden_compra', 'producto', 'variante']
    
    def __str__(self):
        return f"{self.producto.codigo} - {self.cantidad}"
    
    def save(self, *args, **kwargs):
        # Calcular descuento y total
        subtotal = self.cantidad * self.precio_unitario
        
        if self.descuento_porcentaje > 0:
            self.descuento_valor = (subtotal * self.descuento_porcentaje) / 100
        
        self.total = subtotal - self.descuento_valor
        
        super().save(*args, **kwargs)
        
        # Actualizar totales de la orden
        if self.orden_compra_id:
            self.orden_compra.save()
    
    @property
    def pendiente_recibir(self):
        """Cantidad pendiente por recibir"""
        return self.cantidad - self.cantidad_recibida
    
    @property
    def porcentaje_recibido(self):
        """Porcentaje recibido de este item"""
        if self.cantidad == 0:
            return 0
        return (self.cantidad_recibida / self.cantidad) * 100

class RecepcionCompra(models.Model):
    """Modelo para recepciones de órdenes de compra"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    numero = models.CharField(max_length=20, unique=True, verbose_name='Número de Recepción')
    orden_compra = models.ForeignKey(
        OrdenCompra, 
        on_delete=models.PROTECT, 
        related_name='recepciones',
        verbose_name='Orden de Compra'
    )
    
    # Fechas
    fecha_recepcion = models.DateTimeField(default=timezone.now, verbose_name='Fecha de Recepción')
    
    # Información de la entrega
    numero_factura_proveedor = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name='Número Factura Proveedor'
    )
    numero_remision = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name='Número de Remisión'
    )
    transportadora = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name='Transportadora'
    )
    
    # Estado de la recepción
    recepcion_completa = models.BooleanField(
        default=False, 
        verbose_name='Recepción Completa',
        help_text='Indica si esta recepción completa la orden de compra'
    )
    
    # Observaciones
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    observaciones_calidad = models.TextField(
        blank=True, 
        verbose_name='Observaciones de Calidad',
        help_text='Notas sobre la calidad de los productos recibidos'
    )
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha Creación')
    usuario_recepcion = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='recepciones_realizadas',
        verbose_name='Recibido por'
    )
    
    class Meta:
        verbose_name = 'Recepción de Compra'
        verbose_name_plural = 'Recepciones de Compra'
        ordering = ['-fecha_recepcion']
    
    def __str__(self):
        return f"REC-{self.numero} - {self.orden_compra}"
    
    def get_absolute_url(self):
        return reverse('compras:recepcion_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        if not self.numero:
            # Generar número consecutivo
            ultimo = RecepcionCompra.objects.order_by('-numero').first()
            if ultimo and ultimo.numero.isdigit():
                nuevo_numero = int(ultimo.numero) + 1
            else:
                nuevo_numero = 1
            self.numero = f"{nuevo_numero:06d}"
        
        super().save(*args, **kwargs)

class ItemRecepcionCompra(models.Model):
    """Items recibidos en cada recepción"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    recepcion = models.ForeignKey(
        RecepcionCompra, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name='Recepción'
    )
    item_orden = models.ForeignKey(
        ItemOrdenCompra, 
        on_delete=models.PROTECT, 
        verbose_name='Item de Orden'
    )
    
    # Cantidad recibida
    cantidad_recibida = models.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name='Cantidad Recibida'
    )
    
    # Estado de calidad
    calidad_aceptable = models.BooleanField(
        default=True, 
        verbose_name='Calidad Aceptable'
    )
    observaciones_item = models.TextField(
        blank=True, 
        verbose_name='Observaciones del Item'
    )
    
    class Meta:
        verbose_name = 'Item Recepción de Compra'
        verbose_name_plural = 'Items Recepción de Compra'
    
    def __str__(self):
        return f"{self.item_orden.producto.codigo} - {self.cantidad_recibida}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Actualizar cantidad recibida en el item de orden
        self.actualizar_cantidad_recibida()
        
        # Actualizar stock en inventario si la calidad es aceptable
        if self.calidad_aceptable:
            self.actualizar_inventario()
        
        # Actualizar estado de la orden de compra
        self.recepcion.orden_compra.actualizar_estado_por_recepcion()
    
    def actualizar_cantidad_recibida(self):
        """Actualizar la cantidad recibida total en el item de orden"""
        total_recibido = ItemRecepcionCompra.objects.filter(
            item_orden=self.item_orden,
            calidad_aceptable=True
        ).aggregate(total=models.Sum('cantidad_recibida'))['total'] or Decimal('0')
        
        self.item_orden.cantidad_recibida = total_recibido
        self.item_orden.save()
    
    def actualizar_inventario(self):
        """Actualizar el stock en inventario"""
        from inventario.models import Stock, MovimientoInventario, Bodega
        
        # Obtener bodega principal o la primera disponible
        bodega_principal = Bodega.objects.filter(es_principal=True).first()
        if not bodega_principal:
            bodega_principal = Bodega.objects.filter(activa=True).first()
        
        if not bodega_principal:
            raise ValueError("No hay bodegas disponibles para recibir la mercancía")
        
        # Buscar o crear stock
        stock, created = Stock.objects.get_or_create(
            producto=self.item_orden.producto,
            variante=self.item_orden.variante,
            bodega=bodega_principal,
            defaults={'cantidad': Decimal('0'), 'cantidad_reservada': Decimal('0')}
        )
        
        # Actualizar cantidad
        stock.cantidad += self.cantidad_recibida
        stock.save()
        
        # Registrar movimiento de inventario
        MovimientoInventario.objects.create(
            producto=self.item_orden.producto,
            variante=self.item_orden.variante,
            bodega=bodega_principal,
            tipo_movimiento='entrada',
            motivo='compra',
            cantidad=int(self.cantidad_recibida),
            costo_unitario=self.item_orden.precio_unitario,
            documento_referencia=f'OC-{self.recepcion.orden_compra.numero}',
            observaciones=f'Recepción {self.recepcion.numero} - OC {self.recepcion.orden_compra.numero}',
            usuario=self.recepcion.usuario_recepcion
        )
        
        # Actualizar costo promedio del producto
        self.actualizar_costo_promedio()
    
    def actualizar_costo_promedio(self):
        """Actualizar el costo promedio del producto"""
        from inventario.models import MovimientoInventario
        
        producto = self.item_orden.producto
        
        # Obtener todas las entradas de compra del producto
        entradas_compra = MovimientoInventario.objects.filter(
            producto=producto,
            tipo_movimiento='entrada',
            motivo='compra'
        ).aggregate(
            total_cantidad=Sum('cantidad'),
            total_valor=Sum(F('cantidad') * F('costo_unitario'))
        )
        
        if entradas_compra['total_cantidad'] and entradas_compra['total_cantidad'] > 0:
            nuevo_costo_promedio = entradas_compra['total_valor'] / entradas_compra['total_cantidad']
            producto.costo_promedio = nuevo_costo_promedio
            producto.save()
