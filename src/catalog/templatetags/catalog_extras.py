from django import template

from src.catalog.utils import format_weight

register = template.Library()


@register.filter(name="format_weight")
def format_weight_filter(value):
    if value in (None, ""):
        return ""
    return format_weight(value)
