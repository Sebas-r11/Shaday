from django import template
from django.db.models import Sum

register = template.Library()

@register.filter
def stock_total(producto):
    """Calcula el stock total de un producto en todas las bodegas"""
    return producto.stock.aggregate(total=Sum('cantidad'))['total'] or 0

@register.filter
def stock_disponible_total(producto):
    """Calcula el stock disponible total (cantidad - reservada)"""
    stocks = producto.stock.all()
    total = 0
    for stock in stocks:
        total += (stock.cantidad - stock.cantidad_reservada)
    return total

@register.simple_tag
def url_replace(request, field, value):
    """Reemplaza un parámetro en la URL actual manteniendo los otros"""
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()