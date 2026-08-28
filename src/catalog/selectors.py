"""Selectors — лише читання (ecommerce_business_logic_skill), без мутацій."""
from django.db.models import Q, QuerySet

from .models import Category, Product

SORT_OPTIONS = {
    "popularity": ("-is_hit", "-created_at"),
    "price_asc": ("weight_options__price",),
    "price_desc": ("-weight_options__price",),
    "new": ("-created_at",),
}

TAG_FILTERS = {
    "hits": "is_hit",
    "new": "is_new",
}


def get_active_categories() -> QuerySet[Category]:
    return Category.objects.filter(is_active=True).order_by("sort_order", "name")


def get_catalog_products(
    category_slug: str | None = None,
    sort: str | None = None,
    tag: str | None = None,
) -> QuerySet[Product]:
    qs = (
        Product.objects.filter(is_available=True, category__is_active=True)
        .select_related("category")
        .prefetch_related("weight_options", "images")
    )
    if category_slug:
        qs = qs.filter(category__slug=category_slug)
    tag_field = TAG_FILTERS.get(tag or "")
    if tag_field:
        qs = qs.filter(**{tag_field: True})
    order_by = SORT_OPTIONS.get(sort or "popularity", SORT_OPTIONS["popularity"])
    return qs.order_by(*order_by).distinct()


def search_products(query: str) -> QuerySet[Product]:
    """Пошук за назвою або артикулом (sitemap /search/)."""
    if not query:
        return Product.objects.none()
    return (
        Product.objects.filter(is_available=True)
        .filter(Q(name__icontains=query) | Q(weight_options__sku__icontains=query))
        .select_related("category")
        .prefetch_related("weight_options", "images")
        .distinct()
    )
