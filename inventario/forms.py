from django import forms
from .models import Categoria, Subcategoria, Producto, Proveedor, ProductoProveedor, Bodega
from decimal import Decimal

class ProductoForm(forms.ModelForm):
    """Formulario personalizado para productos con porcentajes de ganancia"""
    
    # Campos de porcentaje de ganancia
    margen_minorista = forms.DecimalField(
        label='Margen Minorista (%)',
        min_value=0,
        max_value=1000,
        decimal_places=2,
        required=False,
        initial=30,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': '30.00',
            'step': '0.01',
            'id': 'id_margen_minorista'
        }),
        help_text='Porcentaje de ganancia sobre el costo'
    )
    
    margen_mayorista = forms.DecimalField(
        label='Margen Mayorista (%)',
        min_value=0,
        max_value=1000,
        decimal_places=2,
        required=False,
        initial=20,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': '20.00',
            'step': '0.01',
            'id': 'id_margen_mayorista'
        }),
        help_text='Porcentaje de ganancia sobre el costo'
    )
    
    class Meta:
        model = Producto
        fields = ['codigo', 'nombre', 'descripcion', 'categoria', 'subcategoria', 
                  'costo_promedio', 'precio_minorista', 'precio_mayorista', 'stock_minimo']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Dejar vacío para generar automáticamente'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Nombre del producto'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Descripción del producto'
            }),
            'categoria': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'id': 'id_categoria'
            }),
            'subcategoria': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'id': 'id_subcategoria'
            }),
            'costo_promedio': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '0.00',
                'step': '0.01',
                'id': 'id_costo_promedio'
            }),
            'precio_minorista': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 bg-gray-100',
                'readonly': True,
                'id': 'id_precio_minorista'
            }),
            'precio_mayorista': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 bg-gray-100',
                'readonly': True,
                'id': 'id_precio_mayorista'
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '0'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Hacer el campo código opcional para permitir generación automática
        self.fields['codigo'].required = False
        
        # Si estamos editando un producto existente, calcular los márgenes actuales
        if self.instance and self.instance.pk:
            if self.instance.costo_promedio and self.instance.costo_promedio > 0:
                # Calcular margen minorista actual
                if self.instance.precio_minorista > self.instance.costo_promedio:
                    margen_min = ((self.instance.precio_minorista - self.instance.costo_promedio) / self.instance.costo_promedio) * 100
                    self.fields['margen_minorista'].initial = margen_min
                
                # Calcular margen mayorista actual
                if self.instance.precio_mayorista > self.instance.costo_promedio:
                    margen_may = ((self.instance.precio_mayorista - self.instance.costo_promedio) / self.instance.costo_promedio) * 100
                    self.fields['margen_mayorista'].initial = margen_may
        
        # Configurar subcategorías basadas en la categoría seleccionada
        if 'categoria' in self.data:
            try:
                categoria_id = int(self.data.get('categoria'))
                self.fields['subcategoria'].queryset = Subcategoria.objects.filter(categoria_id=categoria_id, activa=True)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['subcategoria'].queryset = self.instance.categoria.subcategorias.filter(activa=True)

class ProductoFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Buscar por código o nombre...',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500'
        }),
        label='Buscar'
    )
    
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(activa=True),
        required=False,
        empty_label="Todas las categorías",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500'
        }),
        label='Categoría'
    )
    
    subcategoria = forms.ModelChoiceField(
        queryset=Subcategoria.objects.filter(activa=True),
        required=False,
        empty_label="Todas las subcategorías",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500'
        }),
        label='Subcategoría'
    )
    
    precio_min = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Precio mínimo',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500'
        }),
        label='Precio mínimo'
    )
    
    precio_max = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Precio máximo',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500'
        }),
        label='Precio máximo'
    )
    
    STOCK_CHOICES = [
        ('', 'Cualquier stock'),
        ('sin_stock', 'Sin stock'),
        ('bajo_minimo', 'Bajo el mínimo'),
        ('disponible', 'Con stock disponible'),
    ]
    
    stock_status = forms.ChoiceField(
        choices=STOCK_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500'
        }),
        label='Estado del stock'
    )
    
    activo = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('True', 'Activos'),
            ('False', 'Inactivos'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500'
        }),
        label='Estado'
    )

class ProveedorForm(forms.ModelForm):
    """Formulario para crear y editar proveedores"""
    
    class Meta:
        model = Proveedor
        fields = [
            'codigo', 'nombre', 'nit', 'telefono', 'email', 'direccion', 'ciudad',
            'contacto_principal', 'telefono_contacto', 'calificacion', 'confiable',
            'dias_credito', 'descuento_pronto_pago'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Código del proveedor (opcional - se genera automático)'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Nombre o razón social del proveedor'
            }),
            'nit': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'NIT o cédula'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Teléfono principal'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'correo@ejemplo.com'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Dirección completa'
            }),
            'ciudad': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Ciudad'
            }),
            'contacto_principal': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Nombre del contacto'
            }),
            'telefono_contacto': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Teléfono del contacto'
            }),
            'calificacion': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500'
            }),
            'confiable': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'dias_credito': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '0',
                'min': '0'
            }),
            'descuento_pronto_pago': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            })
        }

class ProductoProveedorForm(forms.ModelForm):
    """Formulario para la relación Producto-Proveedor"""
    
    class Meta:
        model = ProductoProveedor
        fields = [
            'proveedor', 'precio_compra', 'disponible',
            'tiempo_entrega_dias', 'cantidad_minima_pedido', 'descuento_volumen',
            'cantidad_descuento', 'proveedor_preferido', 'notas'
        ]
        widgets = {
            'proveedor': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500'
            }),
            'precio_compra': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'disponible': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'tiempo_entrega_dias': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '7',
                'min': '1'
            }),
            'cantidad_minima_pedido': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '1',
                'min': '1'
            }),
            'descuento_volumen': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'cantidad_descuento': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '0',
                'min': '0'
            }),
            'proveedor_preferido': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
            'notas': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Observaciones sobre este proveedor para este producto...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo proveedores activos
        self.fields['proveedor'].queryset = Proveedor.objects.filter(activo=True)

# Formulario inline para múltiples proveedores
ProductoProveedorFormSet = forms.inlineformset_factory(
    Producto,
    ProductoProveedor,
    form=ProductoProveedorForm,
    extra=1,
    can_delete=True,
    fields=[
        'proveedor', 'precio_compra', 'disponible',
        'tiempo_entrega_dias', 'cantidad_minima_pedido', 'descuento_volumen',
        'cantidad_descuento', 'proveedor_preferido', 'notas'
    ]
)

# Formulario para Bodegas
class BodegaForm(forms.ModelForm):
    """Formulario para crear y editar bodegas con integración de rutas"""
    
    class Meta:
        model = Bodega
        fields = ['nombre', 'direccion', 'telefono', 'link_ubicacion', 'es_principal', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Nombre de la bodega'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Dirección completa de la bodega'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Teléfono de contacto'
            }),
            'link_ubicacion': forms.URLInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'https://maps.google.com/... o https://waze.com/...'
            }),
            'es_principal': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'activa': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Mensajes de ayuda personalizados
        self.fields['link_ubicacion'].help_text = 'URL de Google Maps, Waze u otro servicio de mapas para facilitar la navegación'
        self.fields['es_principal'].help_text = 'Marcar si esta es la bodega principal de la empresa'


class SubcategoriaForm(forms.ModelForm):
    """Formulario para crear y editar subcategorías"""
    
    class Meta:
        model = Subcategoria
        fields = ['categoria', 'nombre', 'descripcion', 'activa']
        widgets = {
            'categoria': forms.Select(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
                'id': 'id_categoria'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
                'placeholder': 'Ej: Computadores de Escritorio, Papel Bond, etc.',
                'maxlength': '100'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
                'rows': 3,
                'placeholder': 'Descripción opcional de la subcategoría...'
            }),
            'activa': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar solo categorías activas para el dropdown
        self.fields['categoria'].queryset = Categoria.objects.filter(activa=True).order_by('nombre')
        self.fields['categoria'].empty_label = "Selecciona una categoría"
        
        # Configurar labels y help_text
        self.fields['categoria'].label = "Categoría Padre"
        self.fields['categoria'].help_text = "La categoría bajo la cual se agrupará esta subcategoría"
        
        self.fields['nombre'].label = "Nombre de la Subcategoría"
        self.fields['nombre'].help_text = "Máximo 100 caracteres. Debe ser único dentro de la categoría padre."
        
        self.fields['descripcion'].label = "Descripción"
        self.fields['descripcion'].help_text = "Descripción opcional de la subcategoría"
        self.fields['descripcion'].required = False
        
        self.fields['activa'].label = "Subcategoría Activa"
        self.fields['activa'].help_text = "Marcar si la subcategoría está disponible para uso"