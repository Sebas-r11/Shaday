from django import forms
from django.db import models
from django.contrib.auth import get_user_model
from .models import Oportunidad, Actividad, NotaOportunidad, EstadoOportunidad, PrioridadOportunidad, FuenteOportunidad, TipoActividad
from ventas.models import Cliente

User = get_user_model()

class OportunidadForm(forms.ModelForm):
    """Formulario para crear/editar oportunidades"""
    
    class Meta:
        model = Oportunidad
        fields = [
            'nombre', 'cliente', 'valor_estimado', 'probabilidad', 
            'estado', 'prioridad', 'fuente', 'fecha_cierre_estimada',
            'vendedor', 'descripcion', 'productos_interes', 'competencia'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Nombre descriptivo de la oportunidad'
            }),
            'cliente': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'valor_estimado': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '0',
                'step': '0.01'
            }),
            'probabilidad': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '0',
                'max': '100',
                'value': '50'
            }),
            'estado': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'prioridad': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'fuente': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'fecha_cierre_estimada': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'type': 'date'
            }),
            'vendedor': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Descripción detallada de la oportunidad...'
            }),
            'productos_interes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Productos o servicios de interés del cliente...'
            }),
            'competencia': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Información sobre competidores...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar solo usuarios con permisos de ventas
        self.fields['vendedor'].queryset = User.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')
        
        # Clientes activos
        self.fields['cliente'].queryset = Cliente.objects.filter(
            activo=True
        ).order_by('nombre')

class OportunidadFilterForm(forms.Form):
    """Formulario para filtros de oportunidades"""
    
    estado = forms.ChoiceField(
        choices=[('all', 'Todos los estados')] + list(EstadoOportunidad.choices),
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    prioridad = forms.ChoiceField(
        choices=[('', 'Todas las prioridades')] + list(PrioridadOportunidad.choices),
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    vendedor = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label="Todos los vendedores",
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Buscar por nombre, cliente o descripción...'
        })
    )

class ActividadForm(forms.ModelForm):
    """Formulario para crear/editar actividades"""
    
    class Meta:
        model = Actividad
        fields = [
            'oportunidad', 'tipo', 'asunto', 'descripcion',
            'fecha_actividad', 'duracion_minutos', 'responsable',
            'completada', 'resultado', 'proxima_accion'
        ]
        widgets = {
            'oportunidad': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'tipo': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'asunto': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Asunto de la actividad'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Descripción detallada de la actividad...'
            }),
            'fecha_actividad': forms.DateTimeInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'type': 'datetime-local'
            }),
            'duracion_minutos': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '5',
                'max': '480',
                'value': '30'
            }),
            'responsable': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'completada': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'resultado': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Resultado de la actividad...'
            }),
            'proxima_accion': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Próximos pasos a seguir...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Solo usuarios activos como responsables
        self.fields['responsable'].queryset = User.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')
        
        # Solo oportunidades abiertas para nuevas actividades
        if not self.instance.pk:
            self.fields['oportunidad'].queryset = Oportunidad.objects.exclude(
                estado__in=['cerrado_ganado', 'cerrado_perdido']
            ).select_related('cliente').order_by('-fecha_creacion')

class NotaOportunidadForm(forms.ModelForm):
    """Formulario para agregar notas a oportunidades"""
    
    class Meta:
        model = NotaOportunidad
        fields = ['contenido', 'es_publica']
        widgets = {
            'contenido': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Escribe tu nota aquí...'
            }),
            'es_publica': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            })
        }

class ActividadRapidaForm(forms.Form):
    """Formulario para crear actividades rápidas desde el dashboard"""
    
    oportunidad = forms.ModelChoiceField(
        queryset=Oportunidad.objects.none(),
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    tipo = forms.ChoiceField(
        choices=TipoActividad.choices,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    asunto = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Asunto de la actividad'
        })
    )
    
    fecha_actividad = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'type': 'datetime-local'
        })
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Solo oportunidades del usuario o sin asignar
        if user:
            self.fields['oportunidad'].queryset = Oportunidad.objects.exclude(
                estado__in=['cerrado_ganado', 'cerrado_perdido']
            ).filter(
                models.Q(vendedor=user) | models.Q(vendedor__isnull=True)
            ).select_related('cliente').order_by('-fecha_creacion')