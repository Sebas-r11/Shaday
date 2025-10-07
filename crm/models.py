import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal

User = get_user_model()

class EstadoOportunidad(models.TextChoices):
    """Estados del pipeline de ventas"""
    PROSPECTO = 'prospecto', 'Prospecto'
    CALIFICADO = 'calificado', 'Calificado'
    PROPUESTA = 'propuesta', 'Propuesta Enviada'
    NEGOCIACION = 'negociacion', 'En Negociación'
    CERRADO_GANADO = 'cerrado_ganado', 'Cerrado Ganado'
    CERRADO_PERDIDO = 'cerrado_perdido', 'Cerrado Perdido'

class PrioridadOportunidad(models.TextChoices):
    """Niveles de prioridad"""
    BAJA = 'baja', 'Baja'
    MEDIA = 'media', 'Media'
    ALTA = 'alta', 'Alta'
    URGENTE = 'urgente', 'Urgente'

class FuenteOportunidad(models.TextChoices):
    """Fuente de la oportunidad"""
    WEB = 'web', 'Sitio Web'
    REFERENCIA = 'referencia', 'Referencia'
    LLAMADA_FRIA = 'llamada_fria', 'Llamada Fría'
    REDES_SOCIALES = 'redes_sociales', 'Redes Sociales'
    EVENTO = 'evento', 'Evento/Feria'
    EMAIL = 'email', 'Email Marketing'
    PUBLICIDAD = 'publicidad', 'Publicidad'
    OTRO = 'otro', 'Otro'

class TipoActividad(models.TextChoices):
    """Tipos de actividades CRM"""
    LLAMADA = 'llamada', 'Llamada Telefónica'
    EMAIL = 'email', 'Email'
    REUNION = 'reunion', 'Reunión'
    PRESENTACION = 'presentacion', 'Presentación'
    SEGUIMIENTO = 'seguimiento', 'Seguimiento'
    PROPUESTA = 'propuesta', 'Envío de Propuesta'
    VISITA = 'visita', 'Visita Cliente'
    OTRO = 'otro', 'Otro'

# ============= MODELOS PRINCIPALES =============

class Oportunidad(models.Model):
    """Modelo para gestionar oportunidades de venta"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=200, verbose_name='Nombre de la Oportunidad')
    cliente = models.ForeignKey(
        'ventas.Cliente', 
        on_delete=models.CASCADE, 
        related_name='oportunidades',
        verbose_name='Cliente'
    )
    
    # Información comercial
    valor_estimado = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name='Valor Estimado'
    )
    probabilidad = models.PositiveIntegerField(
        default=50, 
        verbose_name='Probabilidad (%)',
        help_text='Probabilidad de cierre (0-100%)'
    )
    estado = models.CharField(
        max_length=20, 
        choices=EstadoOportunidad.choices, 
        default=EstadoOportunidad.PROSPECTO,
        verbose_name='Estado'
    )
    
    # Clasificación
    prioridad = models.CharField(
        max_length=10, 
        choices=PrioridadOportunidad.choices, 
        default=PrioridadOportunidad.MEDIA,
        verbose_name='Prioridad'
    )
    fuente = models.CharField(
        max_length=20, 
        choices=FuenteOportunidad.choices, 
        default=FuenteOportunidad.WEB,
        verbose_name='Fuente'
    )
    
    # Fechas importantes
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha Creación')
    fecha_cierre_estimada = models.DateField(
        null=True, 
        blank=True, 
        verbose_name='Fecha Cierre Estimada'
    )
    fecha_cierre_real = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name='Fecha Cierre Real'
    )
    
    # Asignación y seguimiento
    vendedor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='oportunidades_asignadas',
        verbose_name='Vendedor Asignado'
    )
    
    # Información adicional
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    productos_interes = models.TextField(
        blank=True, 
        verbose_name='Productos de Interés',
        help_text='Productos o servicios de interés del cliente'
    )
    competencia = models.TextField(
        blank=True, 
        verbose_name='Competencia',
        help_text='Información sobre competidores'
    )
    
    # Campos de auditoría
    usuario_creacion = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='oportunidades_creadas',
        verbose_name='Creado por'
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name='Última Actualización')
    
    class Meta:
        verbose_name = 'Oportunidad'
        verbose_name_plural = 'Oportunidades'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['estado', 'fecha_creacion']),
            models.Index(fields=['vendedor', 'estado']),
            models.Index(fields=['cliente']),
        ]
    
    def __str__(self):
        return f"{self.nombre} - {self.cliente.nombre_display}"
    
    def get_absolute_url(self):
        return reverse('crm:oportunidad_detail', kwargs={'pk': self.pk})
    
    @property
    def valor_ponderado(self):
        """Calcula el valor ponderado por probabilidad"""
        return (self.valor_estimado * self.probabilidad) / 100
    
    @property
    def dias_desde_creacion(self):
        """Días transcurridos desde la creación"""
        return (timezone.now().date() - self.fecha_creacion.date()).days
    
    @property
    def estado_display_color(self):
        """Color CSS para el estado"""
        colors = {
            'prospecto': 'bg-gray-100 text-gray-800',
            'calificado': 'bg-blue-100 text-blue-800',
            'propuesta': 'bg-yellow-100 text-yellow-800',
            'negociacion': 'bg-orange-100 text-orange-800',
            'cerrado_ganado': 'bg-green-100 text-green-800',
            'cerrado_perdido': 'bg-red-100 text-red-800',
        }
        return colors.get(self.estado, 'bg-gray-100 text-gray-800')
    
    @property
    def prioridad_display_color(self):
        """Color CSS para la prioridad"""
        colors = {
            'baja': 'bg-gray-100 text-gray-700',
            'media': 'bg-blue-100 text-blue-700',
            'alta': 'bg-orange-100 text-orange-700',
            'urgente': 'bg-red-100 text-red-700',
        }
        return colors.get(self.prioridad, 'bg-gray-100 text-gray-700')

class Actividad(models.Model):
    """Modelo para registrar actividades relacionadas con oportunidades"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    oportunidad = models.ForeignKey(
        Oportunidad, 
        on_delete=models.CASCADE, 
        related_name='actividades',
        verbose_name='Oportunidad'
    )
    
    tipo = models.CharField(
        max_length=20, 
        choices=TipoActividad.choices, 
        verbose_name='Tipo de Actividad'
    )
    asunto = models.CharField(max_length=200, verbose_name='Asunto')
    descripcion = models.TextField(verbose_name='Descripción')
    
    # Fechas y programación
    fecha_actividad = models.DateTimeField(verbose_name='Fecha/Hora de la Actividad')
    duracion_minutos = models.PositiveIntegerField(
        default=30, 
        verbose_name='Duración (minutos)'
    )
    completada = models.BooleanField(default=False, verbose_name='Completada')
    
    # Asignación
    responsable = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='actividades_asignadas',
        verbose_name='Responsable'
    )
    
    # Resultado de la actividad
    resultado = models.TextField(
        blank=True, 
        verbose_name='Resultado',
        help_text='Resultado o conclusiones de la actividad'
    )
    proxima_accion = models.TextField(
        blank=True, 
        verbose_name='Próxima Acción',
        help_text='Próximos pasos a seguir'
    )
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha Creación')
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name='Última Actualización')
    usuario_creacion = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='actividades_creadas',
        verbose_name='Creado por'
    )
    
    class Meta:
        verbose_name = 'Actividad'
        verbose_name_plural = 'Actividades'
        ordering = ['-fecha_actividad']
        indexes = [
            models.Index(fields=['fecha_actividad', 'responsable']),
            models.Index(fields=['oportunidad', 'completada']),
            models.Index(fields=['tipo', 'fecha_actividad']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.asunto}"
    
    @property
    def esta_vencida(self):
        """Verifica si la actividad está vencida"""
        return not self.completada and self.fecha_actividad < timezone.now()
    
    @property
    def tipo_display_color(self):
        """Color CSS para el tipo de actividad"""
        colors = {
            'llamada': 'bg-blue-100 text-blue-800',
            'email': 'bg-green-100 text-green-800',
            'reunion': 'bg-purple-100 text-purple-800',
            'presentacion': 'bg-orange-100 text-orange-800',
            'seguimiento': 'bg-gray-100 text-gray-800',
            'propuesta': 'bg-yellow-100 text-yellow-800',
            'visita': 'bg-indigo-100 text-indigo-800',
            'otro': 'bg-pink-100 text-pink-800',
        }
        return colors.get(self.tipo, 'bg-gray-100 text-gray-800')

class NotaOportunidad(models.Model):
    """Modelo para notas y comentarios sobre oportunidades"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    oportunidad = models.ForeignKey(
        Oportunidad, 
        on_delete=models.CASCADE, 
        related_name='notas',
        verbose_name='Oportunidad'
    )
    
    contenido = models.TextField(verbose_name='Contenido de la Nota')
    es_publica = models.BooleanField(
        default=True, 
        verbose_name='Visible para todo el equipo',
        help_text='Si está marcado, todos los usuarios pueden ver esta nota'
    )
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha Creación')
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name='Última Actualización')
    usuario_creacion = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notas_creadas',
        verbose_name='Autor'
    )
    
    class Meta:
        verbose_name = 'Nota'
        verbose_name_plural = 'Notas'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Nota de {self.usuario_creacion.get_full_name()} - {self.fecha_creacion.strftime('%d/%m/%Y')}"
