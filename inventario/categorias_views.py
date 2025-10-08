# inventario/categorias_views.py
"""
Vistas especializadas para gestión de categorías y subcategorías
Extraído de inventario/views.py para mejorar organización
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count
from django.contrib import messages
from django.http import JsonResponse

from .models import Categoria, Subcategoria, Producto
from .forms import SubcategoriaForm, CategoriaForm


class InventarioViewMixin(UserPassesTestMixin):
    """Mixin para permitir ver inventario (incluye bodega)"""
    def test_func(self):
        return (self.request.user.can_adjust_inventory() or 
                self.request.user.can_view_inventory())


class AdminOnlyMixin(UserPassesTestMixin):
    """Mixin para funciones que solo puede usar el administrador"""
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name='admin').exists()


# ============= VISTAS DE CATEGORÍAS =============

class CategoriaListView(InventarioViewMixin, ListView):
    """Lista de categorías con estadísticas"""
    model = Categoria
    template_name = 'inventario/categoria_list.html'
    context_object_name = 'categorias'
    
    def get_queryset(self):
        queryset = Categoria.objects.annotate(
            productos_count=Count('producto'),
            subcategorias_count=Count('subcategorias')
        )
        
        # Filtro por búsqueda
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(descripcion__icontains=search)
            )
        
        return queryset.order_by('nombre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_categorias'] = Categoria.objects.count()
        context['search_query'] = self.request.GET.get('search', '')
        
        # Categorías con más productos
        context['top_categorias'] = Categoria.objects.annotate(
            productos_count=Count('producto')
        ).order_by('-productos_count')[:5]
        
        return context


class CategoriaCreateView(AdminOnlyMixin, CreateView):
    """Crear nueva categoría"""
    model = Categoria
    template_name = 'inventario/categoria_form.html'
    form_class = CategoriaForm
    success_url = reverse_lazy('inventario:categoria_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Categoría "{form.instance.nombre}" creada exitosamente.')
        return super().form_valid(form)


class CategoriaDetailView(InventarioViewMixin, DetailView):
    """Detalle de categoría con productos y subcategorías"""
    model = Categoria
    template_name = 'inventario/categoria_detail.html'
    context_object_name = 'categoria'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Productos de la categoría
        context['productos'] = Producto.objects.filter(
            categoria=self.object
        ).order_by('nombre')[:20]  # Primeros 20
        
        # Subcategorías
        context['subcategorias'] = Subcategoria.objects.filter(
            categoria=self.object
        ).annotate(
            productos_count=Count('producto')
        ).order_by('nombre')
        
        # Estadísticas
        context['total_productos'] = Producto.objects.filter(categoria=self.object).count()
        context['productos_activos'] = Producto.objects.filter(
            categoria=self.object, activo=True
        ).count()
        context['total_subcategorias'] = Subcategoria.objects.filter(
            categoria=self.object
        ).count()
        
        # Valor total del inventario de la categoría
        from django.db.models import F
        productos_categoria = Producto.objects.filter(categoria=self.object)
        valor_total = 0
        for producto in productos_categoria:
            stock_total = producto.stock.aggregate(total=Sum('cantidad'))['total'] or 0
            valor_total += stock_total * producto.costo_promedio
        context['valor_inventario'] = valor_total
        
        return context


class CategoriaUpdateView(AdminOnlyMixin, UpdateView):
    """Editar categoría"""
    model = Categoria
    template_name = 'inventario/categoria_form.html'
    form_class = CategoriaForm
    success_url = reverse_lazy('inventario:categoria_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Categoría "{form.instance.nombre}" actualizada exitosamente.')
        return super().form_valid(form)


class CategoriaDeleteView(AdminOnlyMixin, DeleteView):
    """Eliminar categoría"""
    model = Categoria
    template_name = 'inventario/categoria_confirm_delete.html'
    success_url = reverse_lazy('inventario:categoria_list')
    
    def delete(self, request, *args, **kwargs):
        categoria = self.get_object()
        
        # Verificar si tiene productos asociados
        productos_count = Producto.objects.filter(categoria=categoria).count()
        if productos_count > 0:
            messages.error(
                request, 
                f'No se puede eliminar la categoría "{categoria.nombre}" '
                f'porque tiene {productos_count} productos asociados.'
            )
            return redirect('inventario:categoria_list')
        
        # Verificar si tiene subcategorías asociadas
        subcategorias_count = Subcategoria.objects.filter(categoria=categoria).count()
        if subcategorias_count > 0:
            messages.error(
                request, 
                f'No se puede eliminar la categoría "{categoria.nombre}" '
                f'porque tiene {subcategorias_count} subcategorías asociadas.'
            )
            return redirect('inventario:categoria_list')
        
        messages.success(request, f'Categoría "{categoria.nombre}" eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)


# ============= VISTAS DE SUBCATEGORÍAS =============

class SubcategoriaListView(InventarioViewMixin, ListView):
    """Lista de subcategorías con filtros"""
    model = Subcategoria
    template_name = 'inventario/subcategoria_list.html'
    context_object_name = 'subcategorias'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Subcategoria.objects.select_related('categoria').annotate(
            productos_count=Count('producto')
        )
        
        # Filtro por nombre de subcategoría
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(descripcion__icontains=search)
            )
        
        # Filtro por categoría padre
        categoria_id = self.request.GET.get('categoria')
        if categoria_id:
            try:
                queryset = queryset.filter(categoria_id=categoria_id)
            except (ValueError, TypeError):
                pass
        
        return queryset.order_by('categoria__nombre', 'nombre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Categoria.objects.all().order_by('nombre')
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_categoria'] = self.request.GET.get('categoria', '')
        
        # Contar subcategorías por categoría para mostrar en filtros
        categorias_con_count = Categoria.objects.annotate(
            subcategorias_count=Count('subcategorias')
        ).order_by('nombre')
        context['categorias_con_count'] = categorias_con_count
        
        # Estadísticas
        context['total_subcategorias'] = Subcategoria.objects.count()
        
        return context


class SubcategoriaCreateView(AdminOnlyMixin, CreateView):
    """Crear nueva subcategoría"""
    model = Subcategoria
    template_name = 'inventario/subcategoria_form.html'
    form_class = SubcategoriaForm
    success_url = reverse_lazy('inventario:subcategoria_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Subcategoría "{form.instance.nombre}" creada exitosamente.')
        return super().form_valid(form)


class SubcategoriaDetailView(InventarioViewMixin, DetailView):
    """Detalle de subcategoría con productos"""
    model = Subcategoria
    template_name = 'inventario/subcategoria_detail.html'
    context_object_name = 'subcategoria'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Productos de la subcategoría
        context['productos'] = Producto.objects.filter(
            subcategoria=self.object
        ).order_by('nombre')
        
        # Estadísticas
        context['total_productos'] = context['productos'].count()
        context['productos_activos'] = context['productos'].filter(activo=True).count()
        
        # Valor total del inventario de la subcategoría
        valor_total = 0
        for producto in context['productos']:
            stock_total = producto.stock.aggregate(total=Sum('cantidad'))['total'] or 0
            valor_total += stock_total * producto.costo_promedio
        context['valor_inventario'] = valor_total
        
        return context


class SubcategoriaUpdateView(AdminOnlyMixin, UpdateView):
    """Editar subcategoría"""
    model = Subcategoria
    template_name = 'inventario/subcategoria_form.html'
    form_class = SubcategoriaForm
    success_url = reverse_lazy('inventario:subcategoria_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Subcategoría "{form.instance.nombre}" actualizada exitosamente.')
        return super().form_valid(form)


class SubcategoriaDeleteView(AdminOnlyMixin, DeleteView):
    """Eliminar subcategoría"""
    model = Subcategoria
    template_name = 'inventario/subcategoria_confirm_delete.html'
    success_url = reverse_lazy('inventario:subcategoria_list')
    
    def delete(self, request, *args, **kwargs):
        subcategoria = self.get_object()
        
        # Verificar si tiene productos asociados
        productos_count = Producto.objects.filter(subcategoria=subcategoria).count()
        if productos_count > 0:
            messages.error(
                request, 
                f'No se puede eliminar la subcategoría "{subcategoria.nombre}" '
                f'porque tiene {productos_count} productos asociados.'
            )
            return redirect('inventario:subcategoria_detail', pk=subcategoria.pk)
        
        messages.success(request, f'Subcategoría "{subcategoria.nombre}" eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)


# ============= FUNCIONES DE CATEGORÍAS =============

def obtener_subcategorias_por_categoria(request):
    """API para obtener subcategorías de una categoría específica"""
    if not request.user.can_view_inventory():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    categoria_id = request.GET.get('categoria_id')
    if not categoria_id:
        return JsonResponse([], safe=False)
    
    try:
        subcategorias = Subcategoria.objects.filter(
            categoria_id=categoria_id,
            activa=True
        ).order_by('nombre')
        
        data = [
            {
                'id': sub.id,
                'nombre': sub.nombre,
                'descripcion': sub.descripcion or ''
            }
            for sub in subcategorias
        ]
        
        return JsonResponse(data, safe=False)
    except ValueError:
        return JsonResponse([], safe=False)


def mover_productos_categoria(request, categoria_origen_id, categoria_destino_id):
    """Mover todos los productos de una categoría a otra"""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para mover productos entre categorías.')
        return redirect('inventario:categoria_list')
    
    categoria_origen = get_object_or_404(Categoria, pk=categoria_origen_id)
    categoria_destino = get_object_or_404(Categoria, pk=categoria_destino_id)
    
    productos_movidos = Producto.objects.filter(categoria=categoria_origen).update(
        categoria=categoria_destino
    )
    
    messages.success(
        request, 
        f'{productos_movidos} productos movidos de "{categoria_origen.nombre}" '
        f'a "{categoria_destino.nombre}".'
    )
    
    return redirect('inventario:categoria_detail', pk=categoria_destino_id)


def consolidar_categorias(request):
    """Vista para consolidar categorías duplicadas o similares"""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para consolidar categorías.')
        return redirect('inventario:categoria_list')
    
    # Buscar categorías con nombres similares
    categorias_similares = []
    categorias = Categoria.objects.all().order_by('nombre')
    
    for i, categoria in enumerate(categorias):
        similares = []
        for j, otra_categoria in enumerate(categorias):
            if i != j and categoria.nombre.lower() in otra_categoria.nombre.lower():
                similares.append(otra_categoria)
        
        if similares:
            categorias_similares.append({
                'principal': categoria,
                'similares': similares
            })
    
    context = {
        'categorias_similares': categorias_similares,
        'total_categorias': categorias.count()
    }
    
    return render(request, 'inventario/consolidar_categorias.html', context)


# ============= APIS DE CATEGORÍAS =============

def buscar_categorias_api(request):
    """API para buscar categorías (autocompletado)"""
    if not request.user.can_view_inventory():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    term = request.GET.get('q', '') or request.GET.get('term', '')
    if len(term) < 2:
        return JsonResponse([], safe=False)
    
    categorias = Categoria.objects.filter(
        Q(nombre__icontains=term),
        activa=True
    )[:10]
    
    results = [
        {
            'id': categoria.id,
            'label': categoria.nombre,
            'value': categoria.nombre,
            'descripcion': categoria.descripcion or ''
        }
        for categoria in categorias
    ]
    
    return JsonResponse(results, safe=False)


def estadisticas_categorias_api(request):
    """API para obtener estadísticas de categorías"""
    if not request.user.can_view_inventory():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    # Top 10 categorías por número de productos
    top_categorias = Categoria.objects.annotate(
        productos_count=Count('productos')
    ).order_by('-productos_count')[:10]
    
    data = {
        'top_categorias': [
            {
                'nombre': cat.nombre,
                'productos_count': cat.productos_count,
                'subcategorias_count': cat.subcategorias.count()
            }
            for cat in top_categorias
        ],
        'total_categorias': Categoria.objects.count(),
        'categorias_activas': Categoria.objects.filter(activa=True).count(),
        'total_subcategorias': Subcategoria.objects.count(),
        'subcategorias_activas': Subcategoria.objects.filter(activa=True).count()
    }
    
    return JsonResponse(data)