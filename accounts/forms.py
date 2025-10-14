from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group
from .models import User


class BaseUserForm(forms.ModelForm):
    """Clase base para formularios de usuario con estilos Bootstrap"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if isinstance(self.fields[field].widget, forms.CheckboxInput):
                self.fields[field].widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(self.fields[field].widget, forms.Select):
                self.fields[field].widget.attrs.update({'class': 'form-select'})
            else:
                self.fields[field].widget.attrs.update({'class': 'form-control'})


class UserCreateForm(UserCreationForm, BaseUserForm):
    """Formulario para crear nuevos usuarios"""
    
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True, label="Nombres")
    last_name = forms.CharField(max_length=30, required=True, label="Apellidos")
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'role', 'telefono', 'documento', 'activo'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Nombre de usuario único'}),
            'email': forms.EmailInput(attrs={'placeholder': 'correo@empresa.com'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Nombres del usuario'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Apellidos del usuario'}),
            'telefono': forms.TextInput(attrs={'placeholder': 'Ej: +57 300 1234567'}),
            'documento': forms.TextInput(attrs={'placeholder': 'Número de documento'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar campos requeridos
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['role'].required = True
        
        # Configurar help text
        self.fields['username'].help_text = "Solo letras, números y @/./+/-/_ permitidos."
        self.fields['password1'].help_text = "Mínimo 8 caracteres. No puede ser muy común."
        self.fields['password2'].help_text = "Confirme la contraseña anterior."
        self.fields['role'].help_text = "Seleccione el rol que determina los permisos del usuario."
        
        # Configurar activo por defecto
        self.fields['activo'].initial = True
    
    def clean_email(self):
        """Validar que el email sea único"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("Ya existe un usuario con este email.")
        return email
    
    def clean_documento(self):
        """Validar documento único si se proporciona"""
        documento = self.cleaned_data.get('documento')
        if documento:
            # Limpiar formato
            documento = documento.replace(' ', '').replace('-', '').replace('.', '')
            
            # Verificar que sea numérico
            if not documento.isdigit():
                raise ValidationError("El documento debe contener solo números.")
            
            # Verificar unicidad
            if User.objects.filter(documento=documento).exists():
                raise ValidationError("Ya existe un usuario con este documento.")
            
            return documento
        return documento
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
            # Asignar grupo basado en el rol
            self._assign_group(user)
        
        return user
    
    def _assign_group(self, user):
        """Asignar grupo basado en el rol seleccionado"""
        # Remover de todos los grupos primero
        user.groups.clear()
        
        # Mapeo de roles a grupos
        role_group_mapping = {
            'administrador': 'Administradores',
            'vendedor': 'Vendedores',
            'almacenista': 'Almacenistas',
            'operativo': 'Operativos',
            'consulta': 'Consultas'
        }
        
        group_name = role_group_mapping.get(user.role)
        if group_name:
            try:
                group = Group.objects.get(name=group_name)
                user.groups.add(group)
            except Group.DoesNotExist:
                # Crear el grupo si no existe
                group = Group.objects.create(name=group_name)
                user.groups.add(group)


class UserUpdateForm(UserChangeForm, BaseUserForm):
    """Formulario para actualizar usuarios existentes"""
    
    # Remover el campo de contraseña del formulario de edición
    password = None
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'role', 'telefono', 'documento', 'activo',
            'bodega', 'is_staff', 'is_superuser'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Nombre de usuario único'}),
            'email': forms.EmailInput(attrs={'placeholder': 'correo@empresa.com'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Nombres del usuario'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Apellidos del usuario'}),
            'telefono': forms.TextInput(attrs={'placeholder': 'Ej: +57 300 1234567'}),
            'documento': forms.TextInput(attrs={'placeholder': 'Número de documento'}),
        }
    
    def __init__(self, *args, **kwargs):
        # Extraer request si se pasa como argumento
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Configurar campos requeridos
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['role'].required = True
        
        # Solo superusuarios pueden cambiar is_staff e is_superuser
        if self.request and not self.request.user.is_superuser:
            if 'is_staff' in self.fields:
                del self.fields['is_staff']
            if 'is_superuser' in self.fields:
                del self.fields['is_superuser']
    
    def clean_email(self):
        """Validar que el email sea único"""
        email = self.cleaned_data.get('email')
        if email and User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise ValidationError("Ya existe otro usuario con este email.")
        return email
    
    def clean_documento(self):
        """Validar documento único si se proporciona"""
        documento = self.cleaned_data.get('documento')
        if documento:
            # Limpiar formato
            documento = documento.replace(' ', '').replace('-', '').replace('.', '')
            
            # Verificar que sea numérico
            if not documento.isdigit():
                raise ValidationError("El documento debe contener solo números.")
            
            # Verificar unicidad
            if User.objects.exclude(pk=self.instance.pk).filter(documento=documento).exists():
                raise ValidationError("Ya existe otro usuario con este documento.")
            
            return documento
        return documento
    
    def save(self, commit=True):
        user = super().save(commit=commit)
        
        if commit:
            # Actualizar grupo basado en el nuevo rol
            self._update_group(user)
        
        return user
    
    def _update_group(self, user):
        """Actualizar grupo basado en el rol"""
        # Remover de todos los grupos primero
        user.groups.clear()
        
        # Mapeo de roles a grupos
        role_group_mapping = {
            'administrador': 'Administradores',
            'vendedor': 'Vendedores', 
            'almacenista': 'Almacenistas',
            'operativo': 'Operativos',
            'consulta': 'Consultas'
        }
        
        group_name = role_group_mapping.get(user.role)
        if group_name:
            try:
                group = Group.objects.get(name=group_name)
                user.groups.add(group)
            except Group.DoesNotExist:
                # Crear el grupo si no existe
                group = Group.objects.create(name=group_name)
                user.groups.add(group)


class UserSearchForm(forms.Form):
    """Formulario para búsqueda de usuarios"""
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, email o documento...'
        })
    )
    
    role = forms.ChoiceField(
        choices=[('all', 'Todos los roles')] + User.ROLE_CHOICES,
        required=False,
        initial='all',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    activo = forms.ChoiceField(
        choices=[('all', 'Todos'), ('true', 'Activos'), ('false', 'Inactivos')],
        required=False,
        initial='all',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ChangePasswordForm(forms.Form):
    """Formulario para cambiar contraseña de usuario"""
    
    new_password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Mínimo 8 caracteres. No puede ser muy común."
    )
    
    new_password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Confirme la contraseña anterior."
    )
    
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise ValidationError("Las contraseñas no coinciden.")
        
        return password2
    
    def save(self, user):
        """Guardar la nueva contraseña"""
        password = self.cleaned_data['new_password1']
        user.set_password(password)
        user.save()
        return user