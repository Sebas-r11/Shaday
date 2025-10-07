from django import template

register = template.Library()

@register.filter
def neg(value):
    """Devuelve el valor negativo (valor absoluto si es negativo)"""
    try:
        return abs(value)
    except (ValueError, TypeError):
        return value

@register.filter
def currency(value):
    """Formatea un número como moneda colombiana"""
    try:
        return "${:,.0f}".format(float(value))
    except (ValueError, TypeError):
        return value