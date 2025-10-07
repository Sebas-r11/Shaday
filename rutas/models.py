from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class AsignacionCliente(models.Model):
    """
    Asignación de clientes a vendedores para rutas de visitas
    """
    FRECUENCIA_CHOICES = [
        ('semanal', 'Semanal'),
        ('quincenal', 'Quincenal'), 
        ('mensual', 'Mensual'),
        ('bimensual', 'Bimensual'),
        ('trimestral', 'Trimestral'),
    ]
    
    vendedor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='clientes_asignados',
        verbose_name='Vendedor'
    )
    cliente = models.OneToOneField(
        'ventas.Cliente',
        on_delete=models.CASCADE,
        related_name='asignacion_vendedor',
        verbose_name='Cliente'
    )
    frecuencia_visita = models.CharField(
        max_length=20,
        choices=FRECUENCIA_CHOICES,
        default='mensual',
        verbose_name='Frecuencia de Visita'
    )
    fecha_asignacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Asignación'
    )
    activa = models.BooleanField(
        default=True,
        verbose_name='Asignación Activa'
    )
    
    # Campos para cálculo automático de próxima visita
    ultima_visita = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='Última Visita'
    )
    proxima_visita = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Próxima Visita Programada'
    )
    
    # Notas adicionales
    notas = models.TextField(
        blank=True,
        verbose_name='Notas de Asignación',
        help_text='Información adicional sobre la asignación o instrucciones especiales'
    )
    
    class Meta:
        verbose_name = 'Asignación de Cliente'
        verbose_name_plural = 'Asignaciones de Clientes'
        ordering = ['vendedor__username', 'cliente__nombre_completo']
        indexes = [
            models.Index(fields=['vendedor', 'activa']),
            models.Index(fields=['proxima_visita']),
            models.Index(fields=['frecuencia_visita']),
        ]
    
    def __str__(self):
        return f"{self.cliente.nombre_completo} → {self.vendedor.get_full_name() or self.vendedor.username}"
    
    def calcular_proxima_visita(self):
        """Calcula la fecha de próxima visita basada en la frecuencia"""
        if not self.ultima_visita:
            # Si no hay visita previa, programar para mañana
            return timezone.now() + timedelta(days=1)
        
        frecuencia_dias = {
            'semanal': 7,
            'quincenal': 15,
            'mensual': 30,
            'bimensual': 60,
            'trimestral': 90,
        }
        
        dias = frecuencia_dias.get(self.frecuencia_visita, 30)
        return self.ultima_visita + timedelta(days=dias)
    
    def save(self, *args, **kwargs):
        """Actualizar automáticamente la próxima visita al guardar"""
        if self.activa and (not self.proxima_visita or self.ultima_visita):
            self.proxima_visita = self.calcular_proxima_visita()
        super().save(*args, **kwargs)
    
    @property
    def dias_desde_ultima_visita(self):
        """Días transcurridos desde la última visita"""
        if not self.ultima_visita:
            return None
        return (timezone.now() - self.ultima_visita).days
    
    @property
    def dias_para_proxima_visita(self):
        """Días hasta la próxima visita (negativo si está vencida)"""
        if not self.proxima_visita:
            return None
        return (self.proxima_visita - timezone.now()).days
    
    @property
    def visita_vencida(self):
        """True si la próxima visita ya pasó"""
        if not self.proxima_visita:
            return False
        return timezone.now() > self.proxima_visita


class VisitaCliente(models.Model):
    """
    Registro de visitas realizadas por vendedores a clientes
    """
    ESTADO_CHOICES = [
        ('programada', 'Programada'),
        ('realizada', 'Realizada'),
        ('cancelada', 'Cancelada'),
        ('reprogramada', 'Reprogramada'),
    ]
    
    RESULTADO_CHOICES = [
        ('exitosa', 'Exitosa'),
        ('sin_contacto', 'Sin Contacto'),
        ('no_interesado', 'No Interesado'),
        ('pedido_realizado', 'Pedido Realizado'),
        ('seguimiento', 'Requiere Seguimiento'),
    ]
    
    asignacion = models.ForeignKey(
        AsignacionCliente,
        on_delete=models.CASCADE,
        related_name='visitas',
        verbose_name='Asignación'
    )
    fecha_programada = models.DateTimeField(
        verbose_name='Fecha Programada'
    )
    fecha_realizada = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha Realizada'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='programada',
        verbose_name='Estado'
    )
    resultado = models.CharField(
        max_length=20,
        choices=RESULTADO_CHOICES,
        blank=True,
        verbose_name='Resultado de la Visita'
    )
    
    # Información de la visita
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones',
        help_text='Detalles de la visita, comentarios del cliente, etc.'
    )
    productos_mostrados = models.TextField(
        blank=True,
        verbose_name='Productos Mostrados',
        help_text='Lista de productos presentados al cliente'
    )
    pedido_generado = models.ForeignKey(
        'ventas.Pedido',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visita_origen',
        verbose_name='Pedido Generado'
    )
    
    # Seguimiento
    requiere_seguimiento = models.BooleanField(
        default=False,
        verbose_name='Requiere Seguimiento'
    )
    fecha_seguimiento = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Seguimiento'
    )
    
    # Metadatos
    creada_por = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='visitas_creadas',
        verbose_name='Creada por'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de Modificación'
    )
    
    class Meta:
        verbose_name = 'Visita a Cliente'
        verbose_name_plural = 'Visitas a Clientes'
        ordering = ['-fecha_programada']
        indexes = [
            models.Index(fields=['estado', 'fecha_programada']),
            models.Index(fields=['asignacion', 'fecha_realizada']),
            models.Index(fields=['resultado']),
            models.Index(fields=['requiere_seguimiento']),
        ]
    
    def __str__(self):
        return f"{self.asignacion.cliente.nombre_completo} - {self.fecha_programada.strftime('%d/%m/%Y')}"
    
    def save(self, *args, **kwargs):
        """Actualizar asignación cuando se realiza una visita"""
        super().save(*args, **kwargs)
        
        # Si la visita se marca como realizada, actualizar la asignación
        if self.estado == 'realizada' and self.fecha_realizada:
            self.asignacion.ultima_visita = self.fecha_realizada
            self.asignacion.save()
    
    @property
    def vendedor(self):
        """Acceso directo al vendedor"""
        return self.asignacion.vendedor
    
    @property
    def cliente(self):
        """Acceso directo al cliente"""
        return self.asignacion.cliente
    
    @property
    def esta_vencida(self):
        """True si la visita programada ya pasó y no se realizó"""
        if self.estado != 'programada':
            return False
        return timezone.now() > self.fecha_programada


class ConfiguracionRutas(models.Model):
    """
    Configuración general del módulo de rutas
    """
    frecuencia_default = models.CharField(
        max_length=20,
        choices=AsignacionCliente.FRECUENCIA_CHOICES,
        default='mensual',
        verbose_name='Frecuencia por Defecto'
    )
    dias_alerta_vencimiento = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        verbose_name='Días de Alerta',
        help_text='Días antes del vencimiento para mostrar alertas'
    )
    max_clientes_por_vendedor = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(200)],
        verbose_name='Máximo Clientes por Vendedor'
    )
    auto_reprogramar = models.BooleanField(
        default=True,
        verbose_name='Auto-reprogramar Visitas',
        help_text='Programar automáticamente la siguiente visita al completar una'
    )
    
    class Meta:
        verbose_name = 'Configuración de Rutas'
        verbose_name_plural = 'Configuración de Rutas'
    
    def save(self, *args, **kwargs):
        # Asegurar que solo haya una configuración
        if not self.pk and ConfiguracionRutas.objects.exists():
            raise ValueError('Solo puede existir una configuración de rutas')
        super().save(*args, **kwargs)
    
    @classmethod
    def get_configuracion(cls):
        """Obtener la configuración actual o crear una por defecto"""
        config, created = cls.objects.get_or_create(pk=1)
        return config