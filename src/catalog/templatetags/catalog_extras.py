from django import template

from src.catalog.utils import format_weight

register = template.Library()


@register.filter(name="format_weight")
def format_weight_filter(value):
    if value in (None, ""):
        return ""
    return format_weight(value)


def pick_grid_columns(count: int, *, mobile: bool = False, max_cols: int = 5) -> int:
    """Десктоп: 5/4/3 (≤ max_cols). Мобільна: 2. Неповний ряд центрує flex (product-grid skill)."""
    count = int(count or 0)
    if mobile or count <= 0:
        return 2
    if count <= 2:
        return min(3, max_cols)

    allowed = tuple(c for c in (5, 4, 3) if c <= max_cols)
    for cols in allowed:
        if count % cols == 0:
            return cols

    for cols in tuple(c for c in (4, 5, 3) if c <= max_cols):
        if count % cols >= 3:
            return cols

    for cols in tuple(c for c in (3, 5, 4) if c <= max_cols):
        if count % cols == 2:
            return cols

    return min(3, max_cols) if allowed else 2


@register.filter(name="pick_grid_columns")
def pick_grid_columns_filter(count, max_cols=5):
    try:
        max_cols = int(max_cols)
    except (TypeError, ValueError):
        max_cols = 5
    return pick_grid_columns(count, max_cols=max_cols)
