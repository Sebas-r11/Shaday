from django import forms
from django.contrib.auth import get_user_model
from .models import Cliente, Cotizacion, Factura, Pedido

User = get_user_model()

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['tipo_documento', 'numero_documento', 'nombre_completo', 
                  'telefono', 'direccion', 'ciudad', 'enlace_maps', 'tipo_cliente',
                  'limite_credito', 'dias_credito']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer campos más amigables
        self.fields['tipo_documento'].widget.attrs.update({'class': 'form-control'})
        self.fields['numero_documento'].widget.attrs.update({'class': 'form-control'})
        self.fields['nombre_completo'].widget.attrs.update({'class': 'form-control'})
        self.fields['telefono'].widget.attrs.update({'class': 'form-control'})
        self.fields['direccion'].widget.attrs.update({'class': 'form-control'})
        self.fields['ciudad'].widget.attrs.update({'class': 'form-control'})
        self.fields['enlace_maps'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'https://maps.google.com/...'
        })
        self.fields['tipo_cliente'].widget.attrs.update({'class': 'form-control'})
        self.fields['limite_credito'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '0.00'
        })
        self.fields['dias_credito'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '0'
        })

class ClienteFilterForm(forms.Form):
    search = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Buscar por documento, nombre, teléfono...'
    }))
    ciudad = forms.CharField(max_length=100, required=False)
    tipo_cliente = forms.ChoiceField(
        choices=[('', 'Todos')] + Cliente.TIPO_CLIENTE_CHOICES, 
        required=False
    )
    vendedor = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        empty_label='Todos los vendedores'
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Solo mostrar campo vendedor si el usuario no es vendedor
        if user and hasattr(user, 'role') and user.role == 'vendedor':
            del self.fields['vendedor']
        else:
            # Cargar vendedores disponibles
            from django.contrib.auth import get_user_model
            User = get_user_model()
            self.fields['vendedor'].queryset = User.objects.filter(
                is_active=True
            ).order_by('first_name', 'last_name')

class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = ['cliente']  # Solo cliente, número se genera automáticamente

class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = ['cliente', 'numero']

class PedidoForm(forms.ModelForm):
    # Campo de búsqueda para clientes (no se guarda en BD)
    cliente_search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Escriba para buscar cliente...',
            'autocomplete': 'off'
        }),
        label='Buscar Cliente'
    )
    
    class Meta:
        model = Pedido
        fields = ['cliente']  # Solo cliente, número se genera automáticamente
        widgets = {
            'cliente': forms.HiddenInput(),  # Campo oculto para almacenar la selección
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Personalizar etiquetas
        self.fields['cliente'].required = True
        
        # Si hay un usuario, podemos personalizar el queryset de clientes si es necesario
        if user:
            # Por ahora mantenemos todos los clientes disponibles
            pass


class ItemRechazadoForm(forms.Form):
    """Formulario para manejar items rechazados durante la entrega"""
    
    def __init__(self, entrega, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entrega = entrega
        
        # Crear campos dinámicos para cada item del pedido
        for item in entrega.pedido.items.all():
            # Checkbox para marcar si el item fue rechazado
            self.fields[f'item_rechazado_{item.id}'] = forms.BooleanField(
                required=False,
                label=f'¿Fue rechazado {item.producto.nombre}?',
                widget=forms.CheckboxInput(attrs={
                    'class': 'form-check-input',
                    'onchange': f'toggleRechazoFields({item.id})'
                })
            )
            
            # Cantidad rechazada
            self.fields[f'cantidad_rechazada_{item.id}'] = forms.DecimalField(
                max_digits=10,
                decimal_places=2,
                required=False,
                initial=0,
                max_value=item.cantidad,
                min_value=0,
                label=f'Cantidad rechazada (máx: {item.cantidad})',
                widget=forms.NumberInput(attrs={
                    'class': 'form-control',
                    'step': '0.01',
                    'max': str(item.cantidad),
                    'min': '0',
                    'disabled': True,
                    'id': f'cantidad_rechazada_{item.id}'
                })
            )
            
            # Motivo del rechazo
            from .models import ItemRechazado
            self.fields[f'motivo_rechazo_{item.id}'] = forms.ChoiceField(
                choices=ItemRechazado.MOTIVOS_RECHAZO,
                required=False,
                initial='otro',
                label='Motivo del rechazo',
                widget=forms.Select(attrs={
                    'class': 'form-control',
                    'disabled': True,
                    'id': f'motivo_rechazo_{item.id}'
                })
            )
            
            # Observaciones del rechazo
            self.fields[f'observaciones_rechazo_{item.id}'] = forms.CharField(
                required=False,
                max_length=500,
                label='Observaciones adicionales',
                widget=forms.Textarea(attrs={
                    'class': 'form-control',
                    'rows': 2,
                    'placeholder': 'Observaciones sobre el rechazo...',
                    'disabled': True,
                    'id': f'observaciones_rechazo_{item.id}'
                })
            )
    
    def clean(self):
        cleaned_data = super().clean()
        errors = []
        
        for item in self.entrega.pedido.items.all():
            item_rechazado = cleaned_data.get(f'item_rechazado_{item.id}')
            cantidad_rechazada = cleaned_data.get(f'cantidad_rechazada_{item.id}')
            
            if item_rechazado:
                if not cantidad_rechazada or cantidad_rechazada <= 0:
                    errors.append(f'Debe especificar una cantidad válida rechazada para {item.producto.nombre}')
                elif cantidad_rechazada > item.cantidad:
                    errors.append(f'La cantidad rechazada no puede ser mayor a la cantidad del pedido para {item.producto.nombre}')
        
        if errors:
            raise forms.ValidationError(errors)
        
        return cleaned_data


class CompletarEntregaForm(forms.Form):
    """Formulario principal para completar una entrega"""
    
    persona_recibe = forms.CharField(
        max_length=200,
        required=True,
        label='Persona que recibe',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de quien recibe la entrega'
        })
    )
    
    observaciones = forms.CharField(
        required=False,
        max_length=1000,
        label='Observaciones de la entrega',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones adicionales sobre la entrega...'
        })
    )
    
    firma_digital = forms.CharField(
        required=False,
        label='Firma digital (base64)',
        widget=forms.HiddenInput()
    )
    
    foto_evidencia = forms.ImageField(
        required=False,
        label='Foto de evidencia',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
