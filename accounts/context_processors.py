"""
Context processors para el sistema
"""
from .navigation import get_user_navigation, get_user_role_name

def navigation_context(request):
    """
    Context processor que agrega información de navegación
    """
    user = request.user
    
    return {
        'user_navigation': get_user_navigation(user),
        'user_role_name': get_user_role_name(user),
    }