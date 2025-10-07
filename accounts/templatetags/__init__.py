from django import template
from django.contrib.auth.models import AnonymousUser

register = template.Library()

@register.filter
def is_admin_user(user):
    """
    Filtro de template para verificar si el usuario es administrador
    """
    if isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False
    
    # Verificar si es superusuario o tiene rol de administrador
    return (
        user.is_superuser or 
        user.role in ['superadmin', 'administrador']
    )

@register.filter
def can_see_costs(user):
    """
    Filtro para verificar si el usuario puede ver costos
    """
    if isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False
    
    return user.can_see_costs()

@register.filter
def can_adjust_inventory(user):
    """
    Filtro para verificar si el usuario puede ajustar inventario
    """
    if isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False
    
    return user.can_adjust_inventory()

@register.filter  
def can_manage_users(user):
    """
    Filtro para verificar si el usuario puede gestionar otros usuarios
    """
    if isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False
    
    return user.can_manage_users()

@register.filter
def can_create_sales(user):
    """
    Filtro para verificar si el usuario puede crear ventas
    """
    if isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False
    
    return user.can_create_sales()

@register.filter
def can_view_inventory(user):
    """
    Filtro para verificar si el usuario puede ver inventario
    """
    if isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False
    
    return user.can_view_inventory()