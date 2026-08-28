from . import selectors


def header_catalog(request):
    """8 категорій для dropdown у шапці (catalog_dropdown_menu_skill) — усі шаблони."""
    return {"header_categories": selectors.get_active_categories()}
