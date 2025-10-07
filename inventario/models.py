from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

User = get_user_model()

class Proveedor(models.Model):
    """Proveedor de productos"""
    codigo = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name='Código',
        help_text='Código único del proveedor'
    )
    nombre = models.CharField(max_length=200, verbose_name='Nombre o Razón Social')
    nit = models.CharField(max_length=20, unique=True, verbose_name='NIT/Cédula')
    telefono = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    email = models.EmailField(blank=True, verbose_name='Email')
    direccion = models.TextField(blank=True, verbose_name='Dirección')
    ciudad = models.CharField(max_length=100, blank=True, verbose_name='Ciudad')
    contacto_principal = models.CharField(max_length=100, blank=True, verbose_name='Contacto Principal')
    telefono_contacto = models.CharField(max_length=20, blank=True, verbose_name='Teléfono Contacto')
    
    # Calificación y confiabilidad
    calificacion = models.IntegerField(
        default=5,
        choices=[(i, f"{i} estrella{'s' if i != 1 else ''}") for i in range(1, 6)],
        verbose_name='Calificación (1-5 estrellas)'
    )
    confiable = models.BooleanField(default=True, verbose_name='Proveedor Confiable')
    
    # Términos comerciales
    dias_credito = models.PositiveIntegerField(default=0, verbose_name='Días de Crédito')
    descuento_pronto_pago = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name='% Descuento Pronto Pago'
    )
    
    # Metadatos
    activo = models.BooleanField(default=True, verbose_name='Activo')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def save(self, *args, **kwargs):
        # Generar código automático si no se proporciona
        if not self.codigo:
            ultimo_codigo = Proveedor.objects.filter(
                codigo__regex=r'^PR\d{4}$'
            ).order_by('codigo').last()
            
            if ultimo_codigo:
                numero = int(ultimo_codigo.codigo[2:]) + 1
            else:
                numero = 1
            
            self.codigo = f"PR{numero:04d}"
        
        super().save(*args, **kwargs)

class Categoria(models.Model):
    """Categoría de productos"""
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    activa = models.BooleanField(default=True, verbose_name='Activa')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class Subcategoria(models.Model):
    """Subcategoría de productos"""
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='subcategorias')
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    activa = models.BooleanField(default=True, verbose_name='Activa')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Subcategoría'
        verbose_name_plural = 'Subcategorías'
        ordering = ['categoria__nombre', 'nombre']
        unique_together = ['categoria', 'nombre']
    
    def __str__(self):
        return f"{self.categoria.nombre} > {self.nombre}"

class Producto(models.Model):
    """Producto base del inventario"""
    codigo = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name='Código',
        help_text='Código único del producto (máximo 20 caracteres)'
    )
    nombre = models.CharField(max_length=200, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, verbose_name='Categoría')
    subcategoria = models.ForeignKey(Subcategoria, on_delete=models.CASCADE, verbose_name='Subcategoría')
    
    # Precios base
    costo_promedio = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Costo promedio'
    )
    precio_minorista = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Precio minorista'
    )
    precio_mayorista = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Precio mayorista'
    )
    
    # Control de inventario
    stock_minimo = models.PositiveIntegerField(default=0, verbose_name='Stock mínimo')
    maneja_variantes = models.BooleanField(default=False, verbose_name='Maneja variantes')
    
    # Metadatos
    activo = models.BooleanField(default=True, verbose_name='Activo')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Imagen
    # imagen = models.ImageField(upload_to='productos/', blank=True, null=True, verbose_name='Imagen')
    
    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def save(self, *args, **kwargs):
        # Generar código automático si no se proporciona
        if not self.codigo:
            # Buscar el último producto con código numérico de 6 dígitos
            ultimo_codigo = Producto.objects.filter(
                codigo__regex=r'^\d{6}$'
            ).order_by('-codigo').first()
            
            if ultimo_codigo:
                try:
                    nuevo_numero = int(ultimo_codigo.codigo) + 1
                except ValueError:
                    nuevo_numero = 1
            else:
                nuevo_numero = 1
            
            self.codigo = f"{nuevo_numero:06d}"
        
        super().save(*args, **kwargs)
    
    @property
    def utilidad_minorista(self):
        """Utilidad bruta minorista (precio - costo)"""
        if self.costo_promedio > 0:
            return self.precio_minorista - self.costo_promedio
        return Decimal('0.00')
    
    @property
    def utilidad_mayorista(self):
        """Utilidad bruta mayorista (precio - costo)"""
        if self.costo_promedio > 0:
            return self.precio_mayorista - self.costo_promedio
        return Decimal('0.00')
    
    @property
    def margen_minorista_porcentaje(self):
        """Margen porcentual minorista"""
        if self.costo_promedio > 0:
            return (self.precio_minorista / self.costo_promedio) * 100
        return 0
    
    @property
    def margen_mayorista_porcentaje(self):
        """Margen porcentual mayorista"""
        if self.costo_promedio > 0:
            return (self.precio_mayorista / self.costo_promedio) * 100
        return 0
    
    @property
    def proveedores_activos(self):
        """Proveedores activos para este producto"""
        return self.producto_proveedores.filter(activo=True, proveedor__activo=True)
    
    @property
    def proveedor_preferido(self):
        """Proveedor preferido para este producto"""
        return self.producto_proveedores.filter(
            proveedor_preferido=True, 
            activo=True, 
            proveedor__activo=True
        ).first()
    
    def get_precio_para_cliente(self, cliente):
        """
        Obtiene el precio apropiado según el tipo de cliente
        
        Args:
            cliente: Instancia del modelo Cliente
            
        Returns:
            Decimal: Precio correspondiente al tipo de cliente
        """
        if not cliente:
            return self.precio_minorista
        
        # Mapear tipo de cliente a precio
        if cliente.tipo_cliente == 'mayorista':
            return self.precio_mayorista
        elif cliente.tipo_cliente == 'corporativo':
            # Para clientes corporativos usar precio mayorista
            return self.precio_mayorista
        elif cliente.tipo_cliente == 'minorista':
            return self.precio_minorista
        else:
            # Por defecto usar precio minorista
            return self.precio_minorista
    
    def get_precio_por_tipo(self, tipo_cliente):
        """
        Obtiene el precio según el tipo de cliente (string)
        
        Args:
            tipo_cliente: String con el tipo ('minorista', 'mayorista', 'corporativo')
            
        Returns:
            Decimal: Precio correspondiente al tipo de cliente
        """
        if tipo_cliente == 'mayorista':
            return self.precio_mayorista
        elif tipo_cliente == 'corporativo':
            return self.precio_mayorista
        elif tipo_cliente == 'minorista':
            return self.precio_minorista
        else:
            return self.precio_minorista
    
    @property
    def mejor_precio_proveedor(self):
        """Proveedor con mejor precio disponible"""
        return self.producto_proveedores.filter(
            disponible=True, 
            activo=True, 
            proveedor__activo=True
        ).order_by('precio_compra').first()
    
    @property
    def proveedores_disponibles(self):
        """Proveedores con stock disponible"""
        return self.producto_proveedores.filter(
            disponible=True, 
            stock_proveedor__gt=0,
            activo=True, 
            proveedor__activo=True
        ).order_by('precio_compra')
    
    def actualizar_costo_promedio(self):
        """Actualiza el costo promedio basado en proveedores activos"""
        proveedores = self.proveedores_disponibles
        if proveedores.exists():
            # Calcular promedio ponderado por stock disponible
            total_costo = Decimal('0.00')
            total_peso = 0
            
            for pp in proveedores:
                peso = pp.stock_proveedor if pp.stock_proveedor > 0 else 1
                total_costo += pp.precio_compra * peso
                total_peso += peso
            
            if total_peso > 0:
                nuevo_costo = total_costo / total_peso
                self.costo_promedio = nuevo_costo.quantize(Decimal('0.01'))
                self.save(update_fields=['costo_promedio'])
    
    @property
    def stock_total(self):
        """Stock total en todas las bodegas"""
        return self.stock.aggregate(
            total=models.Sum('cantidad')
        )['total'] or 0
    
    @property
    def stock_critico(self):
        """Indica si el stock está por debajo del mínimo"""
        return self.stock_total < self.stock_minimo
    
    @property
    def stock_cerca_minimo(self):
        """Indica si el stock está cerca del mínimo (20% por encima)"""
        limite_alerta = self.stock_minimo * Decimal('1.2')  # 20% más que el mínimo
        return self.stock_total <= limite_alerta and self.stock_total >= self.stock_minimo
    
    @property
    def nivel_alerta_stock(self):
        """Nivel de alerta del stock: critico, bajo, normal"""
        if self.stock_critico:
            return 'critico'
        elif self.stock_cerca_minimo:
            return 'bajo'
        else:
            return 'normal'
    
    @property
    def cantidad_sugerida_compra(self):
        """Cantidad sugerida para compra basada en stock mínimo"""
        if self.stock_critico:
            # Comprar para llegar a 3 veces el stock mínimo
            cantidad_objetivo = self.stock_minimo * 3
            return max(cantidad_objetivo - self.stock_total, self.stock_minimo)
        elif self.stock_cerca_minimo:
            # Comprar para llegar a 2 veces el stock mínimo
            cantidad_objetivo = self.stock_minimo * 2
            return max(cantidad_objetivo - self.stock_total, 0)
        return 0
    
    @classmethod
    def productos_con_alerta_stock(cls):
        """Productos que necesitan reabastecimiento"""
        from django.db.models import Sum, Case, When, IntegerField
        
        productos = cls.objects.annotate(
            stock_total_calculated=Sum('stock__cantidad')
        ).filter(
            activo=True,
            stock_total_calculated__lte=models.F('stock_minimo') * Decimal('1.2')  # 20% por encima del mínimo
        ).prefetch_related('producto_proveedores__proveedor')
        
        return productos
    
    def analizar_patron_ventas(self, dias=30):
        """Analiza el patrón de ventas del producto en los últimos N días"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Como ItemFactura no tiene campo producto, usaremos datos simulados basados en stock
        # Este sería el punto donde se integraría con el sistema de ventas real
        
        # Simulación basada en el stock actual y mínimo
        stock_actual = self.stock_total
        stock_minimo = self.stock_minimo
        
        # Estimación conservadora de ventas basada en diferencia de stock
        if stock_minimo > 0:
            # Asumimos que se vende entre 5-20% del stock mínimo por día
            promedio_diario_estimado = stock_minimo * 0.1  # 10% del stock mínimo
        else:
            # Si no hay stock mínimo definido, estimamos basado en stock actual
            promedio_diario_estimado = max(stock_actual * 0.05, 1)  # 5% del stock actual, mínimo 1
        
        total_estimado = promedio_diario_estimado * dias
        
        # Simulación de tendencia basada en categoría y stock
        if stock_actual < stock_minimo:
            tendencia_porcentaje = 10  # Producto con alta demanda
        elif stock_actual > stock_minimo * 2:
            tendencia_porcentaje = -5   # Producto con baja rotación
        else:
            tendencia_porcentaje = 0    # Estable
        
        return {
            'total_vendido': int(total_estimado),
            'total_ventas': max(int(total_estimado / 3), 1),  # Simulamos transacciones
            'promedio_diario': round(promedio_diario_estimado, 2),
            'promedio_semanal': round(promedio_diario_estimado * 7, 2),
            'tendencia_porcentaje': tendencia_porcentaje,
            'ventas_por_semana': [int(promedio_diario_estimado * 7)] * 4,  # 4 semanas similares
            'dias_cobertura': int(stock_actual / promedio_diario_estimado) if promedio_diario_estimado > 0 else 999,
            'es_simulacion': True  # Indicador de que son datos simulados
        }
    
    def calcular_fecha_agotamiento(self, promedio_diario):
        """Calcula cuándo se agotará el stock basado en el promedio de ventas"""
        from django.utils import timezone
        from datetime import timedelta
        
        if promedio_diario <= 0:
            return None
        
        dias_restantes = self.stock_total / promedio_diario
        return timezone.now().date() + timedelta(days=int(dias_restantes))
    
    def obtener_mejor_proveedor_para_reposicion(self):
        """Obtiene el mejor proveedor considerando precio, disponibilidad y tiempo"""
        from django.db.models import Case, When, Value, F
        
        # Priorizar proveedor preferido si está disponible
        proveedor_preferido = self.producto_proveedores.filter(
            proveedor_preferido=True,
            disponible=True,
            activo=True,
            proveedor__activo=True
        ).first()
        
        if proveedor_preferido and proveedor_preferido.stock_proveedor > 0:
            return proveedor_preferido.proveedor
        
        # Si no hay preferido disponible, buscar el mejor balance precio/disponibilidad
        mejor_proveedor = self.producto_proveedores.filter(
            disponible=True,
            activo=True,
            proveedor__activo=True,
            stock_proveedor__gt=0
        ).annotate(
            # Puntaje basado en precio (menor es mejor) y tiempo de entrega
            score=Case(
                When(proveedor_preferido=True, then=Value(0)),  # Preferido tiene mejor score
                default=F('precio_compra') + (F('tiempo_entrega_dias') * 10)
            )
        ).order_by('score').first()
        
        return mejor_proveedor.proveedor if mejor_proveedor else None
    
    def calcular_cantidad_recomendada(self, patron_ventas, factor_seguridad=1.5):
        """Calcula cantidad recomendada basada en patrón de ventas"""
        promedio_semanal = patron_ventas['promedio_semanal']
        tendencia = patron_ventas['tendencia_porcentaje']
        
        # Base: cobertura para 2-4 semanas según la tendencia
        if tendencia > 20:  # Crecimiento fuerte
            semanas_cobertura = 4
            factor_crecimiento = 1.3
        elif tendencia > 5:  # Crecimiento moderado
            semanas_cobertura = 3
            factor_crecimiento = 1.2
        elif tendencia < -20:  # Decrecimiento fuerte
            semanas_cobertura = 2
            factor_crecimiento = 0.8
        elif tendencia < -5:  # Decrecimiento moderado
            semanas_cobertura = 2
            factor_crecimiento = 0.9
        else:  # Estable
            semanas_cobertura = 3
            factor_crecimiento = 1.0
        
        # Calcular cantidad base
        cantidad_base = promedio_semanal * semanas_cobertura * factor_crecimiento
        
        # Aplicar factor de seguridad
        cantidad_con_seguridad = cantidad_base * factor_seguridad
        
        # Restar stock actual para saber cuánto comprar
        cantidad_comprar = cantidad_con_seguridad - self.stock_total
        
        # Asegurar que sea al menos el stock mínimo
        return max(int(cantidad_comprar), self.stock_minimo)
    
    def generar_recomendacion_inteligente(self, forzar=False):
        """Genera una recomendación inteligente de reposición"""
        from django.utils import timezone
        
        # Verificar si ya existe una recomendación activa reciente
        if not forzar:
            recomendacion_existente = self.recomendaciones.filter(
                activa=True,
                estado__in=['pendiente', 'procesando'],
                fecha_generacion__gte=timezone.now().date()
            ).exists()
            
            if recomendacion_existente:
                return None
        
        # Analizar patrón de ventas
        patron_ventas = self.analizar_patron_ventas(30)
        
        # Determinar prioridad basada en stock y ventas
        if self.stock_total <= 0:
            prioridad = 'critica'
            razon = "Producto sin stock disponible"
            tipo_analisis = 'stock_minimo'
        elif self.stock_critico:
            prioridad = 'alta'
            razon = f"Stock crítico: {self.stock_total} unidades (mínimo: {self.stock_minimo})"
            tipo_analisis = 'stock_minimo'
        elif patron_ventas['dias_cobertura'] <= 7:
            prioridad = 'alta' if patron_ventas['dias_cobertura'] <= 3 else 'media'
            razon = f"Stock durará solo {patron_ventas['dias_cobertura']} días según ventas"
            tipo_analisis = 'patron_ventas'
        elif self.stock_cerca_minimo:
            prioridad = 'media'
            razon = f"Stock cerca del mínimo: {self.stock_total} unidades"
            tipo_analisis = 'stock_minimo'
        elif patron_ventas['tendencia_porcentaje'] > 25:
            prioridad = 'baja'
            razon = f"Tendencia de crecimiento del {patron_ventas['tendencia_porcentaje']:.1f}%"
            tipo_analisis = 'tendencia_historica'
        else:
            return None  # No necesita recomendación
        
        # Calcular cantidad sugerida
        if patron_ventas['promedio_diario'] > 0:
            cantidad_sugerida = self.calcular_cantidad_recomendada(patron_ventas)
        else:
            cantidad_sugerida = self.cantidad_sugerida_compra
        
        # Obtener mejor proveedor
        proveedor_sugerido = self.obtener_mejor_proveedor_para_reposicion()
        
        # Calcular precios si hay proveedor
        precio_sugerido = None
        valor_total = None
        if proveedor_sugerido:
            producto_proveedor = self.producto_proveedores.filter(
                proveedor=proveedor_sugerido,
                activo=True
            ).first()
            if producto_proveedor:
                precio_sugerido = producto_proveedor.precio_compra
                valor_total = precio_sugerido * cantidad_sugerida
        
        # Factores considerados
        factores = [
            f"Patrón de ventas: {patron_ventas['promedio_diario']:.1f} unidades/día",
            f"Tendencia: {patron_ventas['tendencia_porcentaje']:+.1f}%",
            f"Stock actual: {self.stock_total} unidades",
            f"Cobertura actual: {patron_ventas['dias_cobertura']} días"
        ]
        
        # Crear la recomendación
        recomendacion = RecomendacionReposicion.objects.create(
            producto=self,
            proveedor_sugerido=proveedor_sugerido,
            prioridad=prioridad,
            tipo_analisis=tipo_analisis,
            stock_actual=self.stock_total,
            stock_minimo=self.stock_minimo,
            cantidad_sugerida=cantidad_sugerida,
            dias_cobertura_actual=patron_ventas['dias_cobertura'],
            promedio_ventas_diario=Decimal(str(patron_ventas['promedio_diario'])),
            promedio_ventas_semanal=Decimal(str(patron_ventas['promedio_semanal'])),
            tendencia_porcentaje=Decimal(str(patron_ventas['tendencia_porcentaje'])),
            precio_sugerido=precio_sugerido,
            valor_total_sugerido=valor_total,
            fecha_agotamiento_estimada=self.calcular_fecha_agotamiento(patron_ventas['promedio_diario']),
            razon_principal=razon,
            factores_considerados='\n'.join(factores),
            es_automatica=True,
            activa=True
        )
        
        return recomendacion

class PresentacionProducto(models.Model):
    """Diferentes presentaciones de un producto (unidad, caja x6, caja x12, etc.)"""
    
    producto = models.ForeignKey(
        Producto, 
        on_delete=models.CASCADE, 
        related_name='presentaciones',
        verbose_name='Producto'
    )
    
    # Información de la presentación
    nombre = models.CharField(
        max_length=100, 
        verbose_name='Nombre de la presentación',
        help_text='Ej: Unidad, Caja x6, Caja x12, Paquete x24'
    )
    descripcion = models.TextField(
        blank=True, 
        verbose_name='Descripción',
        help_text='Descripción detallada de la presentación'
    )
    
    # Cantidades
    unidades_por_presentacion = models.PositiveIntegerField(
        default=1,
        verbose_name='Unidades por presentación',
        help_text='Cantidad de unidades que contiene esta presentación'
    )
    
    # Precios específicos para esta presentación
    costo_presentacion = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Costo de la presentación'
    )
    precio_minorista_presentacion = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Precio minorista de la presentación'
    )
    precio_mayorista_presentacion = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Precio mayorista de la presentación'
    )
    
    # Control
    es_presentacion_principal = models.BooleanField(
        default=False,
        verbose_name='Presentación principal',
        help_text='Marcar si esta es la presentación por defecto'
    )
    activa = models.BooleanField(default=True, verbose_name='Activa')
    orden = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de presentación en listas'
    )
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Presentación de Producto'
        verbose_name_plural = 'Presentaciones de Productos'
        ordering = ['producto__codigo', 'orden', 'nombre']
        unique_together = ['producto', 'nombre']
    
    def __str__(self):
        return f"{self.producto.codigo} - {self.nombre}"
    
    @property
    def costo_por_unidad(self):
        """Costo por unidad individual calculado desde la presentación"""
        if self.unidades_por_presentacion > 0:
            return self.costo_presentacion / self.unidades_por_presentacion
        return Decimal('0.00')
    
    @property
    def precio_minorista_por_unidad(self):
        """Precio minorista por unidad individual"""
        if self.unidades_por_presentacion > 0:
            return self.precio_minorista_presentacion / self.unidades_por_presentacion
        return Decimal('0.00')
    
    @property
    def precio_mayorista_por_unidad(self):
        """Precio mayorista por unidad individual"""
        if self.unidades_por_presentacion > 0:
            return self.precio_mayorista_presentacion / self.unidades_por_presentacion
        return Decimal('0.00')
    
    @property
    def utilidad_minorista(self):
        """Utilidad bruta minorista para la presentación"""
        return self.precio_minorista_presentacion - self.costo_presentacion
    
    @property
    def utilidad_mayorista(self):
        """Utilidad bruta mayorista para la presentación"""
        return self.precio_mayorista_presentacion - self.costo_presentacion
    
    @property
    def margen_minorista_porcentaje(self):
        """Margen porcentual minorista para la presentación"""
        if self.costo_presentacion > 0:
            return (self.precio_minorista_presentacion / self.costo_presentacion) * 100
        return 0
    
    @property
    def margen_mayorista_porcentaje(self):
        """Margen porcentual mayorista para la presentación"""
        if self.costo_presentacion > 0:
            return (self.precio_mayorista_presentacion / self.costo_presentacion) * 100
        return 0

class PresentacionProveedorProducto(models.Model):
    """Presentaciones específicas que cada proveedor ofrece para un producto"""
    
    # Relaciones principales
    producto_proveedor = models.ForeignKey(
        'ProductoProveedor',
        on_delete=models.CASCADE,
        related_name='presentaciones_disponibles',
        verbose_name='Producto-Proveedor'
    )
    presentacion_base = models.ForeignKey(
        PresentacionProducto,
        on_delete=models.CASCADE,
        verbose_name='Presentación Base',
        help_text='Presentación base del producto (unidad, caja x6, etc.)'
    )
    
    # Información específica del proveedor para esta presentación
    codigo_proveedor = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Código del Proveedor',
        help_text='Código que usa el proveedor para esta presentación'
    )
    
    # Precio específico del proveedor para esta presentación
    precio_compra_presentacion = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Precio de Compra de la Presentación'
    )
    precio_compra_anterior = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Precio Anterior'
    )
    
    # Términos específicos para esta presentación
    cantidad_minima_pedido = models.PositiveIntegerField(
        default=1,
        verbose_name='Cantidad Mínima de Pedido',
        help_text='Cantidad mínima de esta presentación que se puede pedir'
    )
    tiempo_entrega_dias = models.PositiveIntegerField(
        default=7,
        verbose_name='Días de Entrega',
        help_text='Tiempo de entrega específico para esta presentación'
    )
    
    # Descuentos por volumen específicos para esta presentación
    descuento_volumen = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='% Descuento por Volumen'
    )
    cantidad_descuento = models.PositiveIntegerField(
        default=0,
        verbose_name='Cantidad para Descuento',
        help_text='Cantidad mínima para aplicar el descuento'
    )
    
    # Estado y disponibilidad
    disponible = models.BooleanField(
        default=True,
        verbose_name='Disponible',
        help_text='Si el proveedor actualmente ofrece esta presentación'
    )
    es_presentacion_preferida = models.BooleanField(
        default=False,
        verbose_name='Presentación Preferida del Proveedor',
        help_text='Presentación que el proveedor recomienda o prefiere'
    )
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    fecha_ultimo_precio = models.DateTimeField(auto_now=True)
    notas = models.TextField(
        blank=True,
        verbose_name='Notas',
        help_text='Notas específicas para esta presentación del proveedor'
    )
    
    class Meta:
        verbose_name = 'Presentación Proveedor-Producto'
        verbose_name_plural = 'Presentaciones Proveedor-Producto'
        unique_together = ['producto_proveedor', 'presentacion_base']
        ordering = ['producto_proveedor__producto__codigo', 'es_presentacion_preferida', 'precio_compra_presentacion']
    
    def __str__(self):
        return f"{self.producto_proveedor.producto.codigo} - {self.producto_proveedor.proveedor.nombre} - {self.presentacion_base.nombre}"
    
    @property
    def precio_por_unidad_individual(self):
        """Precio por unidad individual calculado desde la presentación"""
        if self.presentacion_base.unidades_por_presentacion > 0:
            return self.precio_compra_presentacion / self.presentacion_base.unidades_por_presentacion
        return Decimal('0.00')
    
    @property
    def precio_con_descuento(self):
        """Precio con descuento por volumen aplicado"""
        if self.tiene_descuento:
            descuento_decimal = self.descuento_volumen / Decimal('100')
            return self.precio_compra_presentacion * (Decimal('1') - descuento_decimal)
        return self.precio_compra_presentacion
    
    @property
    def tiene_descuento(self):
        """Indica si tiene descuento por volumen configurado"""
        return self.descuento_volumen > 0 and self.cantidad_descuento > 0
    
    @property
    def ahorro_por_presentacion(self):
        """Ahorro por unidad individual vs presentación unitaria"""
        try:
            presentacion_unitaria = self.producto_proveedor.presentaciones_disponibles.filter(
                presentacion_base__unidades_por_presentacion=1
            ).first()
            
            if presentacion_unitaria and self.presentacion_base.unidades_por_presentacion > 1:
                precio_individual_unitaria = presentacion_unitaria.precio_compra_presentacion
                precio_individual_esta = self.precio_por_unidad_individual
                return precio_individual_unitaria - precio_individual_esta
            return Decimal('0.00')
        except:
            return Decimal('0.00')

class ProductoProveedor(models.Model):
    """Relación entre productos y proveedores con precios y disponibilidad"""
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='producto_proveedores')
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='proveedor_productos')
    
    # Precios del proveedor
    precio_compra = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Precio de Compra'
    )
    precio_compra_anterior = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Precio Anterior'
    )
    
    # Disponibilidad
    disponible = models.BooleanField(default=True, verbose_name='Disponible')
    tiempo_entrega_dias = models.PositiveIntegerField(default=7, verbose_name='Días de Entrega')
    cantidad_minima_pedido = models.PositiveIntegerField(default=1, verbose_name='Cantidad Mínima')
    
    # Términos específicos
    descuento_volumen = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name='% Descuento por Volumen'
    )
    cantidad_descuento = models.PositiveIntegerField(
        default=0, 
        verbose_name='Cantidad para Descuento'
    )
    
    # Metadatos de precio
    fecha_ultimo_precio = models.DateTimeField(auto_now=True, verbose_name='Última Actualización')
    usuario_actualizo = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Preferencias
    proveedor_preferido = models.BooleanField(default=False, verbose_name='Proveedor Preferido')
    activo = models.BooleanField(default=True, verbose_name='Relación Activa')
    
    # Notas
    notas = models.TextField(blank=True, verbose_name='Notas y Observaciones')
    
    class Meta:
        verbose_name = 'Producto-Proveedor'
        verbose_name_plural = 'Productos-Proveedores'
        unique_together = ['producto', 'proveedor']
        ordering = ['proveedor_preferido', 'precio_compra']
    
    def __str__(self):
        return f"{self.producto.codigo} - {self.proveedor.nombre}: ${self.precio_compra}"
    
    @property
    def tiene_descuento(self):
        """Indica si tiene descuento por volumen"""
        return self.descuento_volumen > 0 and self.cantidad_descuento > 0
    
    @property
    def precio_con_descuento(self):
        """Precio con descuento por volumen aplicado"""
        if self.tiene_descuento:
            return self.precio_compra * (1 - (self.descuento_volumen / Decimal('100')))
        return self.precio_compra
    
    @property
    def variacion_precio(self):
        """Porcentaje de variación respecto al precio anterior"""
        if self.precio_compra_anterior and self.precio_compra_anterior > 0:
            variacion = ((self.precio_compra - self.precio_compra_anterior) / self.precio_compra_anterior) * 100
            return variacion
        return 0
    
    @property
    def estado_disponibilidad(self):
        """Estado legible de disponibilidad"""
        if not self.disponible:
            return "No Disponible"
        elif self.stock_proveedor == 0:
            return "Sin Stock"
        elif self.stock_proveedor < 10:
            return "Stock Bajo"
        else:
            return "Disponible"

class VarianteProducto(models.Model):
    """Variantes de productos (tallas, colores, etc.)"""
    TIPO_VARIANTE_CHOICES = [
        ('talla', 'Talla'),
        ('color', 'Color'),
    ]
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='variantes')
    tipo_variante = models.CharField(max_length=20, choices=TIPO_VARIANTE_CHOICES, verbose_name='Tipo')
    valor = models.CharField(max_length=50, verbose_name='Valor')
    codigo_variante = models.CharField(max_length=50, unique=True, verbose_name='Código variante')
    
    # Precios específicos de la variante (opcional)
    costo_promedio = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Costo promedio específico'
    )
    precio_minorista = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Precio minorista específico'
    )
    precio_mayorista = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Precio mayorista específico'
    )
    
    activa = models.BooleanField(default=True, verbose_name='Activa')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Variante de producto'
        verbose_name_plural = 'Variantes de productos'
        unique_together = ['producto', 'tipo_variante', 'valor']
        ordering = ['producto__codigo', 'tipo_variante', 'valor']
    
    def __str__(self):
        return f"{self.producto.codigo} - {self.get_tipo_variante_display()}: {self.valor}"
    
    def save(self, *args, **kwargs):
        # Generar código de variante automático
        if not self.codigo_variante:
            self.codigo_variante = f"{self.producto.codigo}-{self.valor.upper()}"
        super().save(*args, **kwargs)

class Bodega(models.Model):
    """Bodegas/Sucursales para control de inventario"""
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    direccion = models.TextField(verbose_name='Dirección')
    telefono = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    activa = models.BooleanField(default=True, verbose_name='Activa')
    es_principal = models.BooleanField(default=False, verbose_name='Bodega principal')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # Link de ubicación para módulo de rutas
    link_ubicacion = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='Link de Ubicación',
        help_text='URL de Google Maps, Waze u otro servicio de mapas para facilitar la navegación'
    )
    
    class Meta:
        verbose_name = 'Bodega'
        verbose_name_plural = 'Bodegas'
        ordering = ['-es_principal', 'nombre']
    
    def __str__(self):
        return self.nombre

class Stock(models.Model):
    """Control de stock por producto/variante en cada bodega"""
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='stock')
    variante = models.ForeignKey(VarianteProducto, on_delete=models.CASCADE, null=True, blank=True)
    bodega = models.ForeignKey(Bodega, on_delete=models.CASCADE)
    
    cantidad = models.IntegerField(default=0, verbose_name='Cantidad')
    cantidad_reservada = models.IntegerField(default=0, verbose_name='Cantidad reservada')
    
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Stock'
        verbose_name_plural = 'Stocks'
        unique_together = ['producto', 'variante', 'bodega']
        ordering = ['bodega__nombre', 'producto__codigo']
    
    def __str__(self):
        if self.variante:
            return f"{self.producto.codigo} ({self.variante.valor}) - {self.bodega.nombre}: {self.cantidad}"
        return f"{self.producto.codigo} - {self.bodega.nombre}: {self.cantidad}"
    
    @property
    def cantidad_disponible(self):
        """Cantidad disponible para venta (total - reservada)"""
        return self.cantidad - self.cantidad_reservada
    
    def reservar(self, cantidad, usuario=None, pedido_id=None, observaciones=""):
        """Reserva stock para una venta"""
        if self.cantidad_disponible >= cantidad:
            self.cantidad_reservada += cantidad
            self.save()
            
            # Registrar movimiento de reserva
            MovimientoInventario.registrar_reserva(
                producto=self.producto,
                variante=self.variante,
                bodega=self.bodega,
                cantidad=cantidad,
                costo_unitario=self.producto.costo_promedio,
                usuario=usuario,
                pedido_id=pedido_id,
                observaciones=observaciones
            )
            return True
        return False
    
    def liberar_reserva(self, cantidad, usuario=None, pedido_id=None, observaciones=""):
        """Libera stock reservado"""
        cantidad_a_liberar = min(cantidad, self.cantidad_reservada)
        if cantidad_a_liberar > 0:
            self.cantidad_reservada -= cantidad_a_liberar
            self.save()
            
            # Registrar movimiento de liberación
            MovimientoInventario.liberar_reserva(
                producto=self.producto,
                variante=self.variante,
                bodega=self.bodega,
                cantidad=cantidad_a_liberar,
                costo_unitario=self.producto.costo_promedio,
                usuario=usuario,
                pedido_id=pedido_id,
                observaciones=observaciones
            )
            return cantidad_a_liberar
        return 0
    
    def confirmar_venta(self, cantidad, usuario=None, pedido_id=None, factura_id=None, observaciones=""):
        """Confirma una venta descontando del stock físico y liberando reserva"""
        if self.cantidad >= cantidad:
            # Descontar del stock físico
            self.cantidad -= cantidad
            
            # Liberar de reserva si estaba reservado
            if self.cantidad_reservada >= cantidad:
                self.cantidad_reservada -= cantidad
            
            self.save()
            
            # Registrar movimiento de venta
            MovimientoInventario.registrar_venta(
                producto=self.producto,
                variante=self.variante,
                bodega=self.bodega,
                cantidad=cantidad,
                costo_unitario=self.producto.costo_promedio,
                usuario=usuario,
                pedido_id=pedido_id,
                factura_id=factura_id,
                observaciones=observaciones
            )
            return True
        return False

class MovimientoInventario(models.Model):
    """Registro de todos los movimientos de inventario"""
    TIPO_MOVIMIENTO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
        ('transferencia', 'Transferencia'),
    ]
    
    MOTIVO_CHOICES = [
        ('compra', 'Compra'),
        ('venta', 'Venta'),
        ('reserva', 'Reserva para venta'),
        ('liberacion_reserva', 'Liberación de reserva'),
        ('devolucion_cliente', 'Devolución cliente'),
        ('devolucion_proveedor', 'Devolución proveedor'),
        ('ajuste_inventario', 'Ajuste inventario'),
        ('transferencia', 'Transferencia entre bodegas'),
        ('producto_dañado', 'Producto dañado'),
        ('producto_vencido', 'Producto vencido'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Producto y bodega afectados
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    variante = models.ForeignKey(VarianteProducto, on_delete=models.CASCADE, null=True, blank=True)
    bodega = models.ForeignKey(Bodega, on_delete=models.CASCADE)
    
    # Detalles del movimiento
    tipo_movimiento = models.CharField(max_length=20, choices=TIPO_MOVIMIENTO_CHOICES)
    motivo = models.CharField(max_length=30, choices=MOTIVO_CHOICES)
    cantidad = models.IntegerField(verbose_name='Cantidad')
    costo_unitario = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Costo unitario'
    )
    
    # Referencias
    documento_referencia = models.CharField(max_length=100, blank=True, verbose_name='Documento referencia')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    
    # Referencias específicas para integración con ventas
    pedido_referencia = models.UUIDField(null=True, blank=True, verbose_name='ID Pedido referencia')
    factura_referencia = models.UUIDField(null=True, blank=True, verbose_name='ID Factura referencia')
    
    # Auditoría
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    
    # Para transferencias
    bodega_destino = models.ForeignKey(
        Bodega, 
        on_delete=models.CASCADE, 
        related_name='movimientos_recibidos', 
        null=True, 
        blank=True,
        verbose_name='Bodega destino'
    )
    
    class Meta:
        verbose_name = 'Movimiento de inventario'
        verbose_name_plural = 'Movimientos de inventario'
        ordering = ['-fecha_movimiento']
    
    def __str__(self):
        return f"{self.get_tipo_movimiento_display()} - {self.producto.codigo} - {self.cantidad} - {self.fecha_movimiento}"
    
    @staticmethod
    def registrar_venta(producto, variante, bodega, cantidad, costo_unitario, usuario, pedido_id=None, factura_id=None, observaciones=""):
        """Registra una salida por venta"""
        return MovimientoInventario.objects.create(
            producto=producto,
            variante=variante,
            bodega=bodega,
            tipo_movimiento='salida',
            motivo='venta',
            cantidad=cantidad,
            costo_unitario=costo_unitario,
            usuario=usuario,
            pedido_referencia=pedido_id,
            factura_referencia=factura_id,
            documento_referencia=f"VENTA-{pedido_id or factura_id}",
            observaciones=observaciones
        )
    
    @staticmethod
    def registrar_reserva(producto, variante, bodega, cantidad, costo_unitario, usuario, pedido_id, observaciones=""):
        """Registra una reserva de producto para venta"""
        return MovimientoInventario.objects.create(
            producto=producto,
            variante=variante,
            bodega=bodega,
            tipo_movimiento='salida',
            motivo='reserva',
            cantidad=0,  # Las reservas no afectan stock físico, solo reservado
            costo_unitario=costo_unitario,
            usuario=usuario,
            pedido_referencia=pedido_id,
            documento_referencia=f"RESERVA-{pedido_id}",
            observaciones=observaciones
        )
    
    @staticmethod
    def liberar_reserva(producto, variante, bodega, cantidad, costo_unitario, usuario, pedido_id, observaciones=""):
        """Registra la liberación de una reserva"""
        return MovimientoInventario.objects.create(
            producto=producto,
            variante=variante,
            bodega=bodega,
            tipo_movimiento='entrada',
            motivo='liberacion_reserva',
            cantidad=0,  # Las liberaciones no afectan stock físico, solo reservado
            costo_unitario=costo_unitario,
            usuario=usuario,
            pedido_referencia=pedido_id,
            documento_referencia=f"LIBERA-{pedido_id}",
            observaciones=observaciones
        )

class OrdenCompraStock(models.Model):
    """Orden de compra generada por alertas de stock"""
    
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('enviada', 'Enviada al Proveedor'),
        ('confirmada', 'Confirmada'),
        ('parcial', 'Recibida Parcial'),
        ('completa', 'Recibida Completa'),
        ('cancelada', 'Cancelada'),
    ]
    
    codigo = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name='Código de Orden'
    )
    proveedor = models.ForeignKey(
        Proveedor, 
        on_delete=models.CASCADE, 
        related_name='ordenes_compra',
        verbose_name='Proveedor'
    )
    
    # Fechas importantes
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_envio = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Envío')
    fecha_entrega_esperada = models.DateField(null=True, blank=True, verbose_name='Entrega Esperada')
    fecha_recepcion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Recepción')
    
    # Estado y gestión
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador')
    usuario_creacion = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Totales
    subtotal = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name='Subtotal'
    )
    descuento_total = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name='Descuento Total'
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
    
    # Observaciones y notas
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    notas_internas = models.TextField(blank=True, verbose_name='Notas Internas')
    
    # Generación automática
    generada_por_alerta = models.BooleanField(default=False, verbose_name='Generada por Alerta de Stock')
    
    class Meta:
        verbose_name = 'Orden de Compra'
        verbose_name_plural = 'Órdenes de Compra'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.codigo} - {self.proveedor.nombre}"
    
    def save(self, *args, **kwargs):
        if not self.codigo:
            # Generar código automático OC-YYYYMMDD-####
            from datetime import datetime
            fecha = datetime.now().strftime('%Y%m%d')
            ultimo_codigo = OrdenCompraStock.objects.filter(
                codigo__regex=rf'^OC-{fecha}-\d{{4}}$'
            ).order_by('codigo').last()
            
            if ultimo_codigo:
                numero = int(ultimo_codigo.codigo[-4:]) + 1
            else:
                numero = 1
            
            self.codigo = f"OC-{fecha}-{numero:04d}"
        
        super().save(*args, **kwargs)
    
    @property
    def estado_display_class(self):
        """Clase CSS para mostrar el estado"""
        estado_classes = {
            'borrador': 'bg-gray-100 text-gray-800',
            'enviada': 'bg-blue-100 text-blue-800',
            'confirmada': 'bg-yellow-100 text-yellow-800',
            'parcial': 'bg-orange-100 text-orange-800',
            'completa': 'bg-green-100 text-green-800',
            'cancelada': 'bg-red-100 text-red-800',
        }
        return estado_classes.get(self.estado, 'bg-gray-100 text-gray-800')
    
    def calcular_totales(self):
        """Calcula los totales de la orden"""
        items = self.items.all()
        
        self.subtotal = sum(item.total for item in items)
        
        # Calcular descuento total basado en descuentos por volumen
        self.descuento_total = sum(item.descuento_total for item in items)
        
        # Por ahora impuestos en 0, se puede configurar después
        self.impuestos = Decimal('0.00')
        
        self.total = self.subtotal - self.descuento_total + self.impuestos
        self.save(update_fields=['subtotal', 'descuento_total', 'impuestos', 'total'])

class ItemOrdenCompraStock(models.Model):
    """Item individual de una orden de compra"""
    
    orden_compra = models.ForeignKey(
        OrdenCompraStock, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    producto = models.ForeignKey(
        'Producto', 
        on_delete=models.CASCADE,
        verbose_name='Producto'
    )
    presentacion = models.ForeignKey(
        'PresentacionProducto',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Presentación',
        help_text='Presentación específica del producto (unidad, caja x6, etc.)'
    )
    presentacion_proveedor = models.ForeignKey(
        'PresentacionProveedorProducto',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Presentación del Proveedor',
        help_text='Presentación específica que ofrece el proveedor para este producto'
    )
    
    # Cantidades
    cantidad_solicitada = models.PositiveIntegerField(verbose_name='Cantidad Solicitada')
    cantidad_recibida = models.PositiveIntegerField(default=0, verbose_name='Cantidad Recibida')
    
    # Precios
    precio_unitario = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Precio Unitario'
    )
    descuento_porcentaje = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name='% Descuento'
    )
    
    # Referencia al proveedor específico
    producto_proveedor = models.ForeignKey(
        ProductoProveedor, 
        on_delete=models.CASCADE,
        verbose_name='Producto-Proveedor',
        help_text='Relación específica producto-proveedor de donde se tomaron precio y condiciones'
    )
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    
    class Meta:
        verbose_name = 'Item de Orden de Compra'
        verbose_name_plural = 'Items de Orden de Compra'
        unique_together = ['orden_compra', 'producto']
    
    def __str__(self):
        return f"{self.orden_compra.codigo} - {self.producto.codigo}"
    
    @property
    def total(self):
        """Total del item sin descuento"""
        return self.precio_unitario * self.cantidad_solicitada
    
    @property
    def descuento_total(self):
        """Descuento total aplicado"""
        return (self.total * self.descuento_porcentaje) / Decimal('100')
    
    @property
    def total_con_descuento(self):
        """Total con descuento aplicado"""
        return self.total - self.descuento_total
    
    @property
    def cantidad_pendiente(self):
        """Cantidad que falta por recibir"""
        return self.cantidad_solicitada - self.cantidad_recibida
    
    @property
    def porcentaje_recibido(self):
        """Porcentaje recibido de la cantidad solicitada"""
        if self.cantidad_solicitada > 0:
            return (self.cantidad_recibida / self.cantidad_solicitada) * 100
        return 0
    
    @property
    def unidades_individuales_solicitadas(self):
        """Cantidad de unidades individuales solicitadas (considerando la presentación)"""
        presentacion = self.presentacion_proveedor.presentacion_base if self.presentacion_proveedor else self.presentacion
        if presentacion:
            return self.cantidad_solicitada * presentacion.unidades_por_presentacion
        return self.cantidad_solicitada
    
    @property
    def unidades_individuales_recibidas(self):
        """Cantidad de unidades individuales recibidas (considerando la presentación)"""
        presentacion = self.presentacion_proveedor.presentacion_base if self.presentacion_proveedor else self.presentacion
        if presentacion:
            return self.cantidad_recibida * presentacion.unidades_por_presentacion
        return self.cantidad_recibida
    
    @property
    def precio_por_unidad_individual(self):
        """Precio por unidad individual calculado desde la presentación"""
        presentacion = self.presentacion_proveedor.presentacion_base if self.presentacion_proveedor else self.presentacion
        if presentacion and presentacion.unidades_por_presentacion > 0:
            return self.precio_unitario / presentacion.unidades_por_presentacion
        return self.precio_unitario
    
    @property
    def presentacion_mostrar(self):
        """Presentación a mostrar (prioriza la del proveedor)"""
        if self.presentacion_proveedor:
            return self.presentacion_proveedor.presentacion_base
        return self.presentacion
    
    @property
    def nombre_presentacion(self):
        """Nombre de la presentación para mostrar"""
        presentacion = self.presentacion_mostrar
        return presentacion.nombre if presentacion else 'Unidad'
    
    @property
    def codigo_proveedor_presentacion(self):
        """Código que usa el proveedor para esta presentación"""
        if self.presentacion_proveedor and self.presentacion_proveedor.codigo_proveedor:
            return self.presentacion_proveedor.codigo_proveedor
        return self.producto.codigo


class DevolucionVentas(models.Model):
    """Registro de devoluciones de ventas que deben ser recibidas por bodega"""
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Recibir'),
        ('parcial', 'Recibida Parcialmente'),
        ('completa', 'Recibida Completamente'),
        ('rechazada', 'Rechazada por Bodega'),
    ]
    
    MOTIVO_CHOICES = [
        ('cliente_rechazo', 'Cliente Rechazó Producto'),
        ('producto_danado', 'Producto Dañado'),
        ('producto_vencido', 'Producto Vencido'),
        ('falta_dinero', 'Cliente Sin Dinero'),
        ('cambio_pedido', 'Cliente Cambió Pedido'),
        ('error_despacho', 'Error en Despacho'),
        ('otro', 'Otro Motivo'),
    ]
    
    CONDICION_CHOICES = [
        ('excelente', 'Excelente Estado'),
        ('buena', 'Buen Estado'),
        ('regular', 'Estado Regular'),
        ('mala', 'Mal Estado - No Vendible'),
        ('dañado', 'Dañado - Pérdida Total'),
    ]
    
    # Información básica
    numero_devolucion = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name='Número de Devolución',
        help_text='Número único de la devolución'
    )
    
    # Relaciones
    repartidor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='devoluciones_realizadas',
        verbose_name='Repartidor'
    )
    
    bodeguero_recibe = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='devoluciones_recibidas',
        verbose_name='Bodeguero que Recibe'
    )
    
    cliente_nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre del Cliente'
    )
    
    cliente_direccion = models.TextField(
        blank=True,
        verbose_name='Dirección del Cliente'
    )
    
    # Información de la entrega original
    pedido_numero = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Número de Pedido Original'
    )
    
    fecha_entrega = models.DateTimeField(
        verbose_name='Fecha de Entrega Original'
    )
    
    # Detalles de la devolución
    motivo = models.CharField(
        max_length=20,
        choices=MOTIVO_CHOICES,
        verbose_name='Motivo de Devolución'
    )
    
    observaciones_repartidor = models.TextField(
        blank=True,
        verbose_name='Observaciones del Repartidor'
    )
    
    # Control de estado
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name='Estado'
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    fecha_recepcion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Recepción en Bodega'
    )
    
    observaciones_bodega = models.TextField(
        blank=True,
        verbose_name='Observaciones de Bodega'
    )
    
    total_valor_devuelto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Valor Total Devuelto'
    )
    
    class Meta:
        verbose_name = 'Devolución de Ventas'
        verbose_name_plural = 'Devoluciones de Ventas'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Devolución {self.numero_devolucion} - {self.cliente_nombre}"
    
    def save(self, *args, **kwargs):
        if not self.numero_devolucion:
            # Generar número único de devolución
            import datetime
            fecha = datetime.datetime.now()
            self.numero_devolucion = f"DEV-{fecha.strftime('%Y%m%d%H%M%S')}"
        super().save(*args, **kwargs)
    
    @property
    def dias_pendiente(self):
        """Días que lleva pendiente la devolución"""
        if self.estado == 'pendiente':
            from django.utils import timezone
            return (timezone.now().date() - self.fecha_creacion.date()).days
        return 0
    
    @property
    def cantidad_items_devueltos(self):
        """Cantidad total de items en la devolución"""
        return self.items.aggregate(
            total=models.Sum('cantidad_devuelta')
        )['total'] or 0
    
    @property
    def cantidad_items_recibidos(self):
        """Cantidad total de items recibidos en bodega"""
        return self.items.aggregate(
            total=models.Sum('cantidad_recibida')
        )['total'] or 0


class DevolucionItem(models.Model):
    """Items específicos de una devolución"""
    
    devolucion = models.ForeignKey(
        DevolucionVentas,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Devolución'
    )
    
    producto = models.ForeignKey(
        'Producto',
        on_delete=models.CASCADE,
        verbose_name='Producto'
    )
    
    # Cantidades
    cantidad_original = models.PositiveIntegerField(
        verbose_name='Cantidad en Pedido Original',
        help_text='Cantidad que se pidió originalmente'
    )
    
    cantidad_entregada = models.PositiveIntegerField(
        verbose_name='Cantidad Entregada',
        help_text='Cantidad que se logró entregar al cliente'
    )
    
    cantidad_devuelta = models.PositiveIntegerField(
        verbose_name='Cantidad Devuelta',
        help_text='Cantidad que regresa a bodega'
    )
    
    cantidad_recibida = models.PositiveIntegerField(
        default=0,
        verbose_name='Cantidad Recibida en Bodega',
        help_text='Cantidad que bodega ha confirmado recibir'
    )
    
    # Precios y valores
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Precio Unitario'
    )
    
    valor_devuelto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Valor Total Devuelto'
    )
    
    # Condición del producto devuelto
    condicion = models.CharField(
        max_length=20,
        choices=DevolucionVentas.CONDICION_CHOICES,
        default='excelente',
        verbose_name='Condición del Producto'
    )
    
    # Ubicación en bodega
    ubicacion_bodega = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Ubicación en Bodega',
        help_text='Donde se colocó el producto devuelto'
    )
    
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones'
    )
    
    fecha_recepcion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Recepción'
    )
    
    class Meta:
        verbose_name = 'Item de Devolución'
        verbose_name_plural = 'Items de Devolución'
        unique_together = ['devolucion', 'producto']
    
    def __str__(self):
        return f"{self.producto.nombre} - {self.cantidad_devuelta} unidades"
    
    def save(self, *args, **kwargs):
        # Calcular valor devuelto
        self.valor_devuelto = self.cantidad_devuelta * self.precio_unitario
        super().save(*args, **kwargs)
        
        # Actualizar total en devolución padre
        self.devolucion.total_valor_devuelto = self.devolucion.items.aggregate(
            total=models.Sum('valor_devuelto')
        )['total'] or 0
        self.devolucion.save(update_fields=['total_valor_devuelto'])
    
    @property
    def cantidad_pendiente_recibir(self):
        """Cantidad que falta por recibir en bodega"""
        return self.cantidad_devuelta - self.cantidad_recibida
    
    @property
    def porcentaje_recibido(self):
        """Porcentaje recibido de la cantidad devuelta"""
        if self.cantidad_devuelta > 0:
            return (self.cantidad_recibida / self.cantidad_devuelta) * 100
        return 0
    
    @property
    def debe_aumentar_inventario(self):
        """Si el producto debe aumentar el inventario disponible"""
        return self.condicion in ['excelente', 'buena', 'regular']


class RecomendacionReposicion(models.Model):
    """Modelo para recomendaciones automáticas de reposición de inventario"""
    
    PRIORIDAD_CHOICES = [
        ('critica', 'Crítica - Sin Stock'),
        ('alta', 'Alta - Stock Muy Bajo'),
        ('media', 'Media - Stock Bajo'),
        ('baja', 'Baja - Preventiva'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'En Proceso'),
        ('rechazada', 'Rechazada'),
        ('completada', 'Completada'),
    ]
    
    TIPO_ANALISIS_CHOICES = [
        ('stock_minimo', 'Basado en Stock Mínimo'),
        ('patron_ventas', 'Basado en Patrón de Ventas'),
        ('tendencia_historica', 'Basado en Tendencia Histórica'),
        ('estacional', 'Basado en Comportamiento Estacional'),
        ('predictivo', 'Análisis Predictivo'),
    ]
    
    # Relaciones
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='recomendaciones')
    proveedor_sugerido = models.ForeignKey(
        Proveedor, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='recomendaciones'
    )
    
    # Información de la recomendación
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    prioridad = models.CharField(max_length=20, choices=PRIORIDAD_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    tipo_analisis = models.CharField(max_length=30, choices=TIPO_ANALISIS_CHOICES)
    
    # Datos del análisis
    stock_actual = models.PositiveIntegerField()
    stock_minimo = models.PositiveIntegerField()
    cantidad_sugerida = models.PositiveIntegerField()
    dias_cobertura_actual = models.IntegerField(default=0, help_text='Días que durará el stock actual')
    
    # Análisis de ventas
    promedio_ventas_diario = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Promedio de unidades vendidas por día'
    )
    promedio_ventas_semanal = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Promedio de unidades vendidas por semana'
    )
    tendencia_porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='% de crecimiento/decrecimiento en ventas'
    )
    
    # Datos de costos y precios
    precio_sugerido = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Precio sugerido del proveedor'
    )
    valor_total_sugerido = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Valor total de la compra sugerida'
    )
    
    # Fechas calculadas
    fecha_agotamiento_estimada = models.DateField(
        null=True, 
        blank=True,
        help_text='Fecha estimada de agotamiento del stock'
    )
    fecha_pedido_sugerida = models.DateField(
        null=True,
        blank=True, 
        help_text='Fecha sugerida para realizar el pedido'
    )
    
    # Razones y justificación
    razon_principal = models.CharField(
        max_length=200, 
        help_text='Razón principal de la recomendación'
    )
    factores_considerados = models.TextField(
        blank=True,
        help_text='Factores adicionales considerados en el análisis'
    )
    
    # Control de procesamiento
    procesado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text='Usuario que procesó la recomendación'
    )
    notas_procesamiento = models.TextField(
        blank=True,
        help_text='Notas del procesamiento de la recomendación'
    )
    
    # Flags de sistema
    es_automatica = models.BooleanField(
        default=True,
        help_text='Si fue generada automáticamente por el sistema'
    )
    activa = models.BooleanField(
        default=True,
        help_text='Si la recomendación está activa'
    )
    
    class Meta:
        verbose_name = 'Recomendación de Reposición'
        verbose_name_plural = 'Recomendaciones de Reposición'
        ordering = ['-fecha_generacion', 'prioridad']
        indexes = [
            models.Index(fields=['producto', 'estado']),
            models.Index(fields=['prioridad', 'fecha_generacion']),
            models.Index(fields=['estado', 'activa']),
        ]
    
    def __str__(self):
        return f"{self.producto.codigo} - {self.get_prioridad_display()} - {self.cantidad_sugerida} unidades"
    
    @property
    def urgencia_nivel(self):
        """Nivel numérico de urgencia (mayor número = más urgente)"""
        niveles = {'baja': 1, 'media': 2, 'alta': 3, 'critica': 4}
        return niveles.get(self.prioridad, 0)
    
    @property
    def color_prioridad(self):
        """Color CSS basado en la prioridad"""
        colores = {
            'critica': 'red',
            'alta': 'orange', 
            'media': 'yellow',
            'baja': 'blue'
        }
        return colores.get(self.prioridad, 'gray')
    
    @property 
    def icono_prioridad(self):
        """Icono FontAwesome basado en la prioridad"""
        iconos = {
            'critica': 'fas fa-exclamation-triangle',
            'alta': 'fas fa-exclamation-circle',
            'media': 'fas fa-info-circle', 
            'baja': 'fas fa-check-circle'
        }
        return iconos.get(self.prioridad, 'fas fa-circle')
    
    @property
    def es_urgente(self):
        """Si la recomendación es urgente (crítica o alta prioridad)"""
        return self.prioridad in ['critica', 'alta']
    
    @property
    def descripcion_cobertura(self):
        """Descripción legible de los días de cobertura"""
        if self.dias_cobertura_actual <= 0:
            return "Sin stock"
        elif self.dias_cobertura_actual <= 3:
            return f"{self.dias_cobertura_actual} días (crítico)"
        elif self.dias_cobertura_actual <= 7:
            return f"{self.dias_cobertura_actual} días (bajo)"
        elif self.dias_cobertura_actual <= 14:
            return f"{self.dias_cobertura_actual} días (medio)"
        else:
            return f"{self.dias_cobertura_actual} días (bueno)"
    
    def marcar_procesada(self, usuario, notas=""):
        """Marca la recomendación como procesada"""
        self.estado = 'procesando'
        self.procesado_por = usuario
        self.notas_procesamiento = notas
        self.save(update_fields=['estado', 'procesado_por', 'notas_procesamiento'])
    
    def marcar_completada(self, usuario, notas=""):
        """Marca la recomendación como completada"""
        self.estado = 'completada' 
        self.activa = False
        self.procesado_por = usuario
        if notas:
            self.notas_procesamiento += f"\n{notas}" if self.notas_procesamiento else notas
        self.save(update_fields=['estado', 'activa', 'procesado_por', 'notas_procesamiento'])
    
    def marcar_rechazada(self, usuario, razon):
        """Marca la recomendación como rechazada"""
        self.estado = 'rechazada'
        self.activa = False
        self.procesado_por = usuario
        self.notas_procesamiento = f"Rechazada: {razon}"
        self.save(update_fields=['estado', 'activa', 'procesado_por', 'notas_procesamiento'])


class AlertaStock(models.Model):
    """Alertas automáticas de stock bajo"""
    
    TIPO_ALERTA_CHOICES = [
        ('stock_bajo', 'Stock Bajo'),
        ('agotado', 'Producto Agotado'),
        ('cerca_minimo', 'Cerca del Mínimo'),
    ]
    
    NIVEL_CHOICES = [
        ('info', 'Información'),
        ('advertencia', 'Advertencia'),
        ('critico', 'Crítico'),
    ]
    
    producto = models.ForeignKey(
        Producto, 
        on_delete=models.CASCADE, 
        related_name='alertas_stock',
        verbose_name='Producto'
    )
    
    tipo_alerta = models.CharField(
        max_length=20, 
        choices=TIPO_ALERTA_CHOICES,
        verbose_name='Tipo de Alerta'
    )
    
    nivel = models.CharField(
        max_length=15, 
        choices=NIVEL_CHOICES,
        default='advertencia',
        verbose_name='Nivel de Alerta'
    )
    
    mensaje = models.TextField(verbose_name='Mensaje de la Alerta')
    
    stock_actual = models.IntegerField(
        default=0,
        verbose_name='Stock Actual al momento de la alerta'
    )
    
    stock_minimo = models.IntegerField(
        default=0,
        verbose_name='Stock Mínimo'
    )
    
    activa = models.BooleanField(
        default=True,
        verbose_name='Alerta Activa'
    )
    
    vista = models.BooleanField(
        default=False,
        verbose_name='Vista por usuario'
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    fecha_resuelto = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Resolución'
    )
    
    resuelto_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Resuelto por'
    )
    
    class Meta:
        verbose_name = 'Alerta de Stock'
        verbose_name_plural = 'Alertas de Stock'
        ordering = ['-fecha_creacion', 'nivel', 'producto__codigo']
        unique_together = ['producto', 'tipo_alerta']
    
    def __str__(self):
        return f"Alerta {self.get_nivel_display()}: {self.producto.codigo} - {self.get_tipo_alerta_display()}"
    
    def marcar_como_vista(self, usuario=None):
        """Marca la alerta como vista por un usuario"""
        self.vista = True
        if usuario:
            # Aquí se podría agregar un log de quién la vio
            pass
        self.save(update_fields=['vista'])
    
    def resolver_alerta(self, usuario=None):
        """Marca la alerta como resuelta"""
        from django.utils import timezone
        
        self.activa = False
        self.fecha_resuelto = timezone.now()
        if usuario:
            self.resuelto_por = usuario
        
        self.save(update_fields=['activa', 'fecha_resuelto', 'resuelto_por'])
    
    def actualizar_stock(self, nuevo_stock):
        """Actualiza el stock actual en la alerta"""
        from django.utils import timezone
        
        self.stock_actual = nuevo_stock
        self.fecha_actualizacion = timezone.now()
        
        # Si el stock ya no está bajo, resolver automáticamente
        if nuevo_stock > self.stock_minimo:
            self.resolver_alerta()
        
        self.save(update_fields=['stock_actual', 'fecha_actualizacion'])
    
    @property
    def dias_desde_creacion(self):
        """Días transcurridos desde que se creó la alerta"""
        from django.utils import timezone
        
        delta = timezone.now() - self.fecha_creacion
        return delta.days
    
    @property
    def requiere_atencion_urgente(self):
        """Determina si requiere atención urgente"""
        return (
            self.nivel == 'critico' or 
            (self.nivel == 'advertencia' and self.dias_desde_creacion > 3) or
            self.stock_actual == 0
        )
    
    @classmethod
    def generar_alerta_automatica(cls, producto):
        """Genera o actualiza una alerta automática para un producto"""
        from django.utils import timezone
        
        # Calcular stock actual (simplificado)
        try:
            # Aquí iría la lógica real de cálculo de stock
            stock_actual = max(0, producto.stock_minimo - 2)  # Simulación
        except:
            stock_actual = 0
        
        # Determinar tipo y nivel de alerta
        if stock_actual == 0:
            tipo_alerta = 'agotado'
            nivel = 'critico'
            mensaje = f"PRODUCTO AGOTADO: {producto.nombre} no tiene stock disponible"
        elif stock_actual <= producto.stock_minimo:
            tipo_alerta = 'stock_bajo'
            nivel = 'critico' if stock_actual <= producto.stock_minimo * 0.5 else 'advertencia'
            mensaje = f"STOCK BAJO: {producto.nombre} - Stock actual: {stock_actual}, Mínimo: {producto.stock_minimo}"
        elif stock_actual <= producto.stock_minimo * 1.2:  # 20% por encima del mínimo
            tipo_alerta = 'cerca_minimo'
            nivel = 'advertencia'
            mensaje = f"CERCA DEL MÍNIMO: {producto.nombre} - Stock actual: {stock_actual}, Mínimo: {producto.stock_minimo}"
        else:
            # No necesita alerta
            # Resolver alertas existentes si las hay
            cls.objects.filter(producto=producto, activa=True).update(
                activa=False,
                fecha_resuelto=timezone.now()
            )
            return None
        
        # Crear o actualizar alerta
        alerta, created = cls.objects.get_or_create(
            producto=producto,
            tipo_alerta=tipo_alerta,
            defaults={
                'nivel': nivel,
                'mensaje': mensaje,
                'stock_actual': stock_actual,
                'stock_minimo': producto.stock_minimo,
                'activa': True,
            }
        )
        
        if not created:
            # Actualizar alerta existente
            alerta.mensaje = mensaje
            alerta.stock_actual = stock_actual
            alerta.nivel = nivel
            alerta.activa = True
            alerta.fecha_actualizacion = timezone.now()
            alerta.save()
        
        return alerta
    
    @classmethod
    def obtener_alertas_dashboard(cls, usuario=None, limit=10):
        """Obtiene alertas para mostrar en el dashboard"""
        alertas = cls.objects.filter(activa=True).select_related('producto', 'producto__categoria')
        
        # Ordenar por prioridad: críticas primero, luego por fecha
        alertas = alertas.order_by(
            models.Case(
                models.When(nivel='critico', then=models.Value(1)),
                models.When(nivel='advertencia', then=models.Value(2)),
                models.When(nivel='info', then=models.Value(3)),
                default=models.Value(4),
                output_field=models.IntegerField(),
            ),
            '-fecha_creacion'
        )[:limit]
        
        return alertas
