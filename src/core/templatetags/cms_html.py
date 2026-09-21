from django import template
from django.utils.safestring import mark_safe

from src.core.html import html_to_plain, sanitize_cms_html

register = template.Library()


@register.filter
def cms_html(value):
    return mark_safe(sanitize_cms_html(value or ""))


@register.filter
def html_plain(value):
    return html_to_plain(value or "")
