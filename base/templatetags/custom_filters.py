from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def sum_total(order_items):
    return sum(item.unit_price * item.quantity for item in order_items) 