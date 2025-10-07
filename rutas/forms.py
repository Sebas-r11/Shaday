from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db import models
from ventas.models import Cliente
from .models import AsignacionCliente, VisitaCliente, ConfiguracionRutas


User = get_user_model()


class AsignacionClienteForm(forms.ModelForm):
    """Formulario para crear/editar asignaciones de clientes"""
    
    class Meta:
        model = AsignacionCliente
        fields = [
            'cliente', 'vendedor', 'frecuencia_visita', 
            'activa', 'notas'
        ]
        widgets = {
            'cliente': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Selecciona un cliente'
            }),
            'vendedor': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Selecciona un vendedor'
            }),
            'frecuencia_visita': forms.Select(attrs={
                'class': 'form-select'
            }),
            'activa': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas adicionales sobre esta asignación...'
            }),
        }
        labels = {
            'cliente': 'Cliente',
            'vendedor': 'Vendedor',
            'frecuencia_visita': 'Frecuencia de Visita',
            'activa': 'Asignación Activa',
            'notas': 'Notas',
        }
        help_texts = {
            'activa': 'Si está activa, el vendedor debe realizar visitas según la frecuencia',
            'notas': 'Información adicional sobre la asignación o instrucciones especiales',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar vendedores activos con rol de vendedor
        self.fields['vendedor'].queryset = User.objects.filter(
            groups__name='vendedor',
            is_active=True
        ).order_by('first_name', 'last_name')
        
        # Si estamos editando, no filtrar clientes por asignación
        if self.instance.pk:
            # Edición: mostrar el cliente actual y otros no asignados
            self.fields['cliente'].queryset = Cliente.objects.filter(
                models.Q(id=self.instance.cliente.id) | 
                models.Q(asignacion_vendedor__isnull=True),
                activo=True
            ).order_by('nombre_completo')
        else:
            # Creación: solo clientes sin asignar
            self.fields['cliente'].queryset = Cliente.objects.filter(
                asignacion_vendedor__isnull=True,
                activo=True
            ).order_by('nombre_completo')

    def clean(self):
        cleaned_data = super().clean()
        cliente = cleaned_data.get('cliente')
        vendedor = cleaned_data.get('vendedor')
        
        # Verificar que el cliente no esté ya asignado a otro vendedor
        if cliente and not self.instance.pk:
            if AsignacionCliente.objects.filter(cliente=cliente, activa=True).exists():
                raise forms.ValidationError(
                    f'El cliente {cliente.nombre_completo} ya está asignado a otro vendedor.'
                )
        
        # Verificar que el vendedor esté activo
        if vendedor and not vendedor.is_active:
            raise forms.ValidationError(
                f'El vendedor {vendedor.get_full_name()} no está activo.'
            )
        
        return cleaned_data


class VisitaClienteForm(forms.ModelForm):
    """Formulario para registrar visitas a clientes"""
    
    # Campo personalizado para búsqueda de cliente
    cliente_busqueda = forms.CharField(
        label='Cliente',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Escriba el nombre del cliente...',
            'list': 'clientes-list'
        }),
        help_text='Escriba el nombre del cliente para buscarlo'
    )
    
    class Meta:
        model = VisitaCliente
        fields = [
            'fecha_programada', 'observaciones', 'requiere_seguimiento'
        ]
        widgets = {
            'fecha_programada': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe lo que aconteció durante la visita...'
            }),
            'requiere_seguimiento': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'fecha_programada': 'Fecha de Visita',
            'observaciones': 'Observaciones',
            'requiere_seguimiento': 'Requiere Seguimiento',
        }
        help_texts = {
            'fecha_programada': 'Fecha y hora de la visita',
            'observaciones': 'Describe los detalles de la visita, temas tratados, resultados, etc.',
            'requiere_seguimiento': 'Marca si esta visita requiere acciones de seguimiento específicas',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Si estamos editando una visita existente, prellenar el campo de búsqueda
        if self.instance and self.instance.pk and hasattr(self.instance, 'asignacion'):
            self.fields['cliente_busqueda'].initial = self.instance.asignacion.cliente.nombre_completo

    def clean_cliente_busqueda(self):
        cliente_texto = self.cleaned_data.get('cliente_busqueda')
        
        if not cliente_texto:
            raise forms.ValidationError('Este campo es obligatorio.')
        
        # Buscar la asignación basada en el nombre del cliente
        if self.user and not self.user.is_superuser:
            asignacion = AsignacionCliente.objects.filter(
                vendedor=self.user,
                activa=True,
                cliente__nombre_completo__icontains=cliente_texto
            ).select_related('cliente').first()
        else:
            asignacion = AsignacionCliente.objects.filter(
                activa=True,
                cliente__nombre_completo__icontains=cliente_texto
            ).select_related('cliente').first()
        
        if not asignacion:
            raise forms.ValidationError(
                f'No se encontró un cliente con el nombre "{cliente_texto}" asignado.'
            )
        
        return asignacion

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Asignar la asignación encontrada en la validación
        asignacion = self.cleaned_data.get('cliente_busqueda')
        if asignacion:
            instance.asignacion = asignacion
        
        if commit:
            instance.save()
        
        return instance


class ConfiguracionRutasForm(forms.ModelForm):
    """Formulario para configurar el sistema de rutas"""
    
    class Meta:
        model = ConfiguracionRutas
        fields = [
            'frecuencia_default', 'dias_alerta_vencimiento',
            'max_clientes_por_vendedor', 'auto_reprogramar'
        ]
        widgets = {
            'frecuencia_default': forms.Select(attrs={
                'class': 'form-select'
            }),
            'dias_alerta_vencimiento': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 30
            }),
            'max_clientes_por_vendedor': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 200
            }),
            'auto_reprogramar': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'frecuencia_default': 'Frecuencia por Defecto',
            'dias_alerta_vencimiento': 'Días de Alerta (antes del vencimiento)',
            'max_clientes_por_vendedor': 'Máximo Clientes por Vendedor',
            'auto_reprogramar': 'Auto-reprogramar Visitas',
        }
        help_texts = {
            'dias_alerta_vencimiento': 'Cuántos días antes de que venza una visita se debe alertar',
            'max_clientes_por_vendedor': 'Número máximo de clientes que se pueden asignar a un vendedor',
            'auto_reprogramar': 'Programar automáticamente la siguiente visita al completar una',
        }

    def clean(self):
        cleaned_data = super().clean()
        hora_inicio = cleaned_data.get('hora_inicio_jornada')
        hora_fin = cleaned_data.get('hora_fin_jornada')
        
        # Validar que hora_fin sea posterior a hora_inicio
        if hora_inicio and hora_fin and hora_fin <= hora_inicio:
            raise forms.ValidationError(
                'La hora de fin de jornada debe ser posterior a la hora de inicio.'
            )
        
        return cleaned_data


class FiltroAsignacionesForm(forms.Form):
    """Formulario para filtrar asignaciones"""
    
    vendedor = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name='vendedor', is_active=True),
        required=False,
        empty_label="Todos los vendedores",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    estado = forms.ChoiceField(
        choices=[
            ('', 'Todos los estados'),
            ('activa', 'Activas'),
            ('inactiva', 'Inactivas'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    frecuencia = forms.ChoiceField(
        choices=[('', 'Todas las frecuencias')] + AsignacionCliente.FRECUENCIA_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    visitas_vencidas = forms.BooleanField(
        required=False,
        label="Solo visitas vencidas",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )