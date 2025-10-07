"""
Vistas especializadas para autenticación y manejo de contraseñas
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User
from .forms import ChangePasswordForm

@login_required
def change_user_password(request, pk):
    """Cambiar contraseña de un usuario"""
    if not request.user.can_manage_users():
        messages.error(request, "No tienes permisos para cambiar contraseñas.")
        return redirect('accounts:dashboard')
    
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            form.save(user)
            messages.success(request, f'Contraseña actualizada para {user.username}.')
            return redirect('accounts:user_detail', pk=user.pk)
    else:
        form = ChangePasswordForm()
    
    return render(request, 'accounts/change_password.html', {
        'form': form,
        'usuario': user,
        'title': f'Cambiar Contraseña: {user.username}'
    })