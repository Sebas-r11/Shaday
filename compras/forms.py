from django import forms
from django.forms import ModelForm, inlineformset_factory
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta

from .models import (
    Proveedor, OrdenCompra, ItemOrdenCompra, 
    RecepcionCompra, ItemRecepcionCompra, 
    EstadoOrdenCompra, CondicionesPago, TipoDocumentoProveedor,
    SolicitudCompra, ItemSolicitudCompra,
    EstadoSolicitudCompra, PrioridadCompra
)
from inventario.models import Producto, VarianteProducto
from ventas.models import Ciudad


class BaseModelForm(ModelForm):
    """Clase base para formularios con estilos Bootstrap"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if isinstance(self.fields[field].widget, forms.CheckboxInput):
                self.fields[field].widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(self.fields[field].widget, forms.Select):
                self.fields[field].widget.attrs.update({'class': 'form-select'})
            elif isinstance(self.fields[field].widget, forms.Textarea):
                self.fields[field].widget.attrs.update({'class': 'form-control', 'rows': 3})
            else:
                self.fields[field].widget.attrs.update({'class': 'form-control'})


class ProveedorForm(BaseModelForm):
    descuento_comercial = forms.DecimalField(
        label='Descuento general otorgado por el proveedor',
        required=True,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 180px; font-size: 1.1em;', 'placeholder': '0', 'step': '0.01', 'max': '100'})
    )

    ciudad = forms.ModelChoiceField(
        label='Ciudad',
        queryset=Ciudad.objects.all().order_by('nombre'),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    """Formulario para crear y editar proveedores"""
    
    class Meta:
        model = Proveedor
        fields = [
            'codigo', 'razon_social', 'nombre_comercial',
            'tipo_documento', 'numero_documento',
            'telefono', 'email', 'sitio_web',
            'direccion', 'ciudad', 'codigo_postal',
            'condiciones_pago', 'limite_credito', 'descuento_comercial',
            'contacto_nombre', 'contacto_cargo', 'contacto_telefono', 'contacto_email',
            'observaciones', 'activo'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={'placeholder': 'Se genera automáticamente si se deja vacío'}),
            'razon_social': forms.TextInput(attrs={'placeholder': 'Razón Social', 'required': 'required'}),
            'nombre_comercial': forms.TextInput(attrs={'placeholder': 'Nombre Comercial'}),
            'tipo_documento': forms.Select(),
            'numero_documento': forms.TextInput(attrs={'placeholder': 'Número de documento', 'required': 'required'}),
            'telefono': forms.TextInput(attrs={'placeholder': 'Teléfono'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
            'sitio_web': forms.URLInput(attrs={'placeholder': 'Sitio Web'}),
            'direccion': forms.TextInput(attrs={'placeholder': 'Dirección'}),
            'codigo_postal': forms.TextInput(attrs={'placeholder': 'Código Postal'}),
            'limite_credito': forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01'}),
            'descuento_comercial': forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01', 'max': '100'}),
            'contacto_nombre': forms.TextInput(attrs={'placeholder': 'Nombre del contacto principal'}),
            'contacto_cargo': forms.TextInput(attrs={'placeholder': 'Cargo del contacto'}),
            'contacto_telefono': forms.TextInput(attrs={'placeholder': 'Teléfono del contacto'}),
            'contacto_email': forms.EmailInput(attrs={'placeholder': 'Email del contacto'}),
            'observaciones': forms.Textarea(attrs={'rows': 2}),
        }
        
    def clean_numero_documento(self):
        """Validar número de documento"""
        numero = self.cleaned_data.get('numero_documento')
        if numero:
            # Remover espacios y guiones
            numero = numero.replace(' ', '').replace('-', '').replace('.', '')
            
            # Validar que solo contenga números
            if not numero.isdigit():
                raise ValidationError("El número de documento debe contener solo números")
            
            # Verificar unicidad
            if self.instance.pk:
                if Proveedor.objects.exclude(pk=self.instance.pk).filter(numero_documento=numero).exists():
                    raise ValidationError("Ya existe un proveedor con este número de documento")
            else:
                if Proveedor.objects.filter(numero_documento=numero).exists():
                    raise ValidationError("Ya existe un proveedor con este número de documento")
            
            return numero
        return numero
    
    def clean_email(self):
        """Validar email único"""
        email = self.cleaned_data.get('email')
        if email:
            if self.instance.pk:
                if Proveedor.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
                    raise ValidationError("Ya existe un proveedor con este email")
            else:
                if Proveedor.objects.filter(email=email).exists():
                    raise ValidationError("Ya existe un proveedor con este email")
        return email
    
    def clean_limite_credito(self):
        """Validar límite de crédito"""
        limite = self.cleaned_data.get('limite_credito')
        if limite is not None and limite < 0:
            raise ValidationError("El límite de crédito no puede ser negativo")
        return limite
    
    def clean_descuento_comercial(self):
        """Validar descuento comercial"""
        descuento = self.cleaned_data.get('descuento_comercial')
        if descuento is not None:
            if descuento < 0 or descuento > 100:
                raise ValidationError("El descuento debe estar entre 0 y 100%")
        return descuento


class OrdenCompraForm(BaseModelForm):
    """Formulario para crear y editar órdenes de compra"""
    
    class Meta:
        model = OrdenCompra
        fields = [
            'proveedor', 'fecha_entrega_estimada', 'observaciones', 
            'condiciones_especiales', 'numero_referencia_proveedor'
        ]
        widgets = {
            'fecha_entrega_estimada': forms.DateInput(attrs={'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Observaciones de la orden'}),
            'condiciones_especiales': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Condiciones especiales de esta orden'}),
            'numero_referencia_proveedor': forms.TextInput(attrs={'placeholder': 'Número de referencia del proveedor'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Solo mostrar proveedores activos
        self.fields['proveedor'].queryset = Proveedor.objects.filter(activo=True).order_by('razon_social')
        
        # Configurar fecha mínima
        self.fields['fecha_entrega_estimada'].widget.attrs['min'] = date.today().isoformat()
        
        # El estado se establece por defecto en el modelo
        
        # Hacer campos requeridos
        self.fields['proveedor'].required = True
        # La fecha de entrega estimada es opcional
    
    def clean_fecha_entrega_estimada(self):
        """Validar fecha de entrega"""
        fecha = self.cleaned_data.get('fecha_entrega_estimada')
        if fecha and fecha < date.today():
            raise ValidationError("La fecha de entrega no puede ser anterior a hoy")
        return fecha


class ItemOrdenCompraForm(BaseModelForm):
    """Formulario para items de orden de compra"""
    
    class Meta:
        model = ItemOrdenCompra
        fields = ['producto', 'variante', 'cantidad', 'precio_unitario', 'descuento_porcentaje', 'observaciones']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'precio_unitario': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'descuento_porcentaje': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100'}),
            'observaciones': forms.TextInput(attrs={'placeholder': 'Observaciones del item'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Solo mostrar productos activos
        self.fields['producto'].queryset = Producto.objects.filter(activo=True).order_by('nombre')
        
        # Hacer campos requeridos
        self.fields['producto'].required = True
        self.fields['cantidad'].required = True
        self.fields['precio_unitario'].required = True
        
        # Configurar variantes dinámicamente con JavaScript
        self.fields['variante'].required = False
        self.fields['variante'].widget.attrs['disabled'] = True
    
    def clean_cantidad(self):
        """Validar cantidad"""
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad is not None and cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero")
        return cantidad
    
    def clean_precio_unitario(self):
        """Validar precio unitario"""
        precio = self.cleaned_data.get('precio_unitario')
        if precio is not None and precio <= 0:
            raise ValidationError("El precio unitario debe ser mayor a cero")
        return precio
    
    def clean_descuento_porcentaje(self):
        """Validar descuento porcentaje"""
        descuento = self.cleaned_data.get('descuento_porcentaje')
        if descuento is not None:
            if descuento < 0 or descuento > 100:
                raise ValidationError("El descuento debe estar entre 0 y 100%")
        return descuento


# Formset para items de orden de compra
ItemOrdenCompraFormSet = inlineformset_factory(
    OrdenCompra, ItemOrdenCompra, 
    form=ItemOrdenCompraForm,
    fields=['producto', 'variante', 'cantidad', 'precio_unitario', 'descuento_porcentaje', 'observaciones'],
    extra=1, 
    can_delete=True,
    validate_min=False,
    validate_max=False
)


class RecepcionCompraForm(BaseModelForm):
    """Formulario para crear recepciones de compra"""
    
    class Meta:
        model = RecepcionCompra
        fields = [
            'orden_compra', 'numero_factura_proveedor', 'numero_remision',
            'transportadora', 'observaciones', 'observaciones_calidad'
        ]
        widgets = {
            'numero_factura_proveedor': forms.TextInput(attrs={'placeholder': 'Número de factura del proveedor'}),
            'numero_remision': forms.TextInput(attrs={'placeholder': 'Número de remisión'}),
            'transportadora': forms.TextInput(attrs={'placeholder': 'Empresa transportadora'}),
            'observaciones': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Observaciones generales de la recepción'}),
            'observaciones_calidad': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Observaciones de calidad'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Solo mostrar órdenes que puedan ser recibidas
        self.fields['orden_compra'].queryset = OrdenCompra.objects.filter(
            estado__in=['enviada', 'confirmada', 'recibida_parcial']
        ).select_related('proveedor').order_by('-fecha_creacion')
        
        # Hacer campos requeridos
        self.fields['orden_compra'].required = True
    
    def clean_numero_factura_proveedor(self):
        """Validar número de factura único por proveedor"""
        numero = self.cleaned_data.get('numero_factura_proveedor')
        orden = self.cleaned_data.get('orden_compra')
        
        if numero and orden:
            if RecepcionCompra.objects.filter(
                orden_compra__proveedor=orden.proveedor,
                numero_factura_proveedor=numero
            ).exists():
                raise ValidationError("Ya existe una recepción con este número de factura para este proveedor")
        
        return numero


class ItemRecepcionCompraForm(BaseModelForm):
    """Formulario para items de recepción"""
    
    class Meta:
        model = ItemRecepcionCompra
        fields = ['item_orden', 'cantidad_recibida', 'observaciones_item']
        widgets = {
            'cantidad_recibida': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'observaciones_item': forms.TextInput(attrs={'placeholder': 'Observaciones del item recibido'}),
        }
    
    def __init__(self, *args, **kwargs):
        orden_compra = kwargs.pop('orden_compra', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar items según la orden de compra
        if orden_compra:
            self.fields['item_orden'].queryset = ItemOrdenCompra.objects.filter(
                orden_compra=orden_compra
            ).select_related('producto', 'variante')
        
        # Hacer campos requeridos
        self.fields['item_orden'].required = True
        self.fields['cantidad_recibida'].required = True
    
    def clean_cantidad_recibida(self):
        """Validar cantidad recibida"""
        cantidad = self.cleaned_data.get('cantidad_recibida')
        item_orden = self.cleaned_data.get('item_orden')
        
        if cantidad is not None and cantidad < 0:
            raise ValidationError("La cantidad recibida no puede ser negativa")
        
        if cantidad is not None and item_orden:
            # Verificar que no se exceda la cantidad pendiente
            cantidad_pendiente = item_orden.cantidad_pendiente()
            if cantidad > cantidad_pendiente:
                raise ValidationError(
                    f"La cantidad recibida ({cantidad}) no puede ser mayor "
                    f"a la cantidad pendiente ({cantidad_pendiente})"
                )
        
        return cantidad


# Formset para items de recepción
ItemRecepcionCompraFormSet = inlineformset_factory(
    RecepcionCompra, ItemRecepcionCompra,
    form=ItemRecepcionCompraForm,
    fields=['item_orden', 'cantidad_recibida', 'observaciones_item'],
    extra=0,
    can_delete=False,
    validate_min=True,
    min_num=1
)


class BusquedaProveedorForm(forms.Form):
    """Formulario para búsqueda de proveedores"""
    
    search = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por razón social, documento o código...'
        })
    )
    
    activo = forms.ChoiceField(
        choices=[('all', 'Todos'), ('true', 'Activos'), ('false', 'Inactivos')],
        required=False,
        initial='all',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class FiltroOrdenCompraForm(forms.Form):
    """Formulario para filtros de órdenes de compra"""
    
    estado = forms.ChoiceField(
        choices=[('all', 'Todos los estados')] + EstadoOrdenCompra.choices,
        required=False,
        initial='all',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    proveedor = forms.ModelChoiceField(
        queryset=Proveedor.objects.filter(activo=True).order_by('razon_social'),
        required=False,
        empty_label="Todos los proveedores",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por número, proveedor...'
        })
    )


class ReporteComprasForm(forms.Form):
    """Formulario para generar reportes de compras"""
    
    fecha_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True
    )
    
    fecha_fin = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True
    )
    
    proveedor = forms.ModelChoiceField(
        queryset=Proveedor.objects.filter(activo=True).order_by('razon_social'),
        required=False,
        empty_label="Todos los proveedores",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    estado = forms.MultipleChoiceField(
        choices=EstadoOrdenCompra.choices,
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar fechas por defecto (mes actual)
        hoy = date.today()
        primer_dia_mes = hoy.replace(day=1)
        self.fields['fecha_inicio'].initial = primer_dia_mes
        self.fields['fecha_fin'].initial = hoy
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            if fecha_inicio > fecha_fin:
                raise ValidationError("La fecha de inicio no puede ser mayor a la fecha de fin")
            
            # Validar que el rango no sea muy amplio (más de 2 años)
            if (fecha_fin - fecha_inicio).days > 730:
                raise ValidationError("El rango de fechas no puede ser mayor a 2 años")
        
        return cleaned_data


# ============= SOLICITUDES DE COMPRA =============

class SolicitudCompraForm(BaseModelForm):
    """Formulario para crear y editar solicitudes de compra"""
    
    class Meta:
        model = SolicitudCompra
        fields = ['prioridad', 'justificacion', 'fecha_requerida']
        widgets = {
            'justificacion': forms.Textarea(attrs={
                'placeholder': 'Describe la justificación para esta solicitud...',
                'rows': 4
            }),
            'fecha_requerida': forms.DateInput(attrs={
                'type': 'date',
                'min': date.today().isoformat()
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Establecer fecha mínima requerida (mañana por defecto)
        mañana = date.today() + timedelta(days=1)
        self.fields['fecha_requerida'].initial = mañana + timedelta(days=7)  # 1 semana por defecto
        
        # Configurar ayudas
        self.fields['prioridad'].help_text = "Selecciona la prioridad de la solicitud"
        self.fields['justificacion'].help_text = "Explica el motivo y necesidad de esta compra"
        self.fields['fecha_requerida'].help_text = "¿Para cuándo necesitas estos productos?"
    
    def clean_fecha_requerida(self):
        fecha_requerida = self.cleaned_data.get('fecha_requerida')
        if fecha_requerida and fecha_requerida <= date.today():
            raise ValidationError("La fecha requerida debe ser posterior a hoy")
        return fecha_requerida


class ItemSolicitudCompraForm(BaseModelForm):
    """Formulario para items de solicitud de compra"""
    
    class Meta:
        model = ItemSolicitudCompra
        fields = ['producto', 'descripcion_item', 'especificaciones', 'cantidad', 'unidad_medida', 'precio_estimado']
        widgets = {
            'descripcion_item': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Descripción del producto o servicio...'
            }),
            'especificaciones': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Especificaciones técnicas (opcional)...'
            }),
            'cantidad': forms.NumberInput(attrs={
                'step': '0.001',
                'min': '0.001',
                'placeholder': '0.000'
            }),
            'precio_estimado': forms.NumberInput(attrs={
                'step': '0.0001',
                'min': '0.0001',
                'placeholder': '0.0000'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar select de productos con search
        if 'producto' in self.fields:
            self.fields['producto'].widget.attrs.update({
                'class': 'form-select select2-producto',
                'data-placeholder': 'Buscar producto (opcional)...'
            })
            # Filtrar solo productos activos
            self.fields['producto'].queryset = Producto.objects.filter(activo=True)
            self.fields['producto'].required = False
        
        # Configurar ayudas
        self.fields['descripcion_item'].help_text = "Descripción del producto o servicio solicitado"
        self.fields['especificaciones'].help_text = "Especificaciones técnicas detalladas (opcional)"
        self.fields['cantidad'].help_text = "Cantidad solicitada"
        self.fields['unidad_medida'].help_text = "Unidad de medida (UND, KG, M, etc.)"
        self.fields['precio_estimado'].help_text = "Precio unitario estimado"
    
    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad and cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero")
        return cantidad
    
    def clean_precio_estimado(self):
        precio = self.cleaned_data.get('precio_estimado')
        if precio and precio < 0:
            raise ValidationError("El precio estimado no puede ser negativo")
        return precio
    
    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        descripcion_item = cleaned_data.get('descripcion_item')
        
        # Si no hay producto, la descripción es obligatoria
        if not producto and not descripcion_item:
            raise ValidationError({
                'descripcion_item': 'La descripción es obligatoria cuando no se selecciona un producto'
            })
        
        return cleaned_data


class AprobarSolicitudForm(forms.Form):
    """Formulario para aprobar/rechazar solicitudes"""
    
    DECISION_CHOICES = [
        ('aprobar', 'Aprobar'),
        ('rechazar', 'Rechazar')
    ]
    
    decision = forms.ChoiceField(
        choices=DECISION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    observaciones = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones sobre la decisión...'
        }),
        help_text="Observaciones sobre la aprobación o rechazo",
        required=False
    )
    
    def clean(self):
        cleaned_data = super().clean()
        decision = cleaned_data.get('decision')
        observaciones = cleaned_data.get('observaciones')
        
        if decision == 'rechazar' and not observaciones:
            raise ValidationError({
                'observaciones': 'Las observaciones son obligatorias cuando se rechaza una solicitud'
            })
        
        return cleaned_data


class CrearOrdenDesdeSolicitudForm(forms.Form):
    """Formulario para crear orden de compra desde solicitud"""
    
    proveedor = forms.ModelChoiceField(
        queryset=Proveedor.objects.filter(activo=True),
        widget=forms.Select(attrs={
            'class': 'form-select select2-proveedor',
            'data-placeholder': 'Seleccionar proveedor...'
        }),
        help_text="Selecciona el proveedor para esta orden"
    )
    
    observaciones = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones adicionales para la orden...'
        }),
        required=False,
        help_text="Observaciones adicionales para incluir en la orden de compra"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar proveedores por razón social
        self.fields['proveedor'].queryset = self.fields['proveedor'].queryset.order_by('razon_social')


# ============= FILTROS DE SOLICITUDES =============

class SolicitudCompraFilterForm(forms.Form):
    """Formulario de filtros para lista de solicitudes"""
    
    estado = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + list(EstadoSolicitudCompra.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    prioridad = forms.ChoiceField(
        choices=[('', 'Todas las prioridades')] + list(PrioridadCompra.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    solicitante = forms.ModelChoiceField(
        queryset=None,  # Se configurará en __init__
        required=False,
        empty_label="Todos los solicitantes",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por código o justificación...'
        }),
        help_text="Busca por código de solicitud o texto en la justificación"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar queryset de solicitantes (usuarios que han hecho solicitudes)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['solicitante'].queryset = User.objects.filter(
            solicitudes_compra__isnull=False
        ).distinct().order_by('first_name', 'last_name')
        
        # Configurar fechas por defecto (último mes)
        hoy = date.today()
        hace_un_mes = hoy - timedelta(days=30)
        self.fields['fecha_desde'].initial = hace_un_mes
        self.fields['fecha_hasta'].initial = hoy