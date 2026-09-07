"""Selectors — лише читання (ecommerce_business_logic_skill), без мутацій."""
from django.db.models import Case, IntegerField, QuerySet, When

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


def _match_ids_by_name_or_sku(query: str) -> list[int]:
    """Unicode casefold — Postgres lc_collate=C не згортає кирилицю в ILIKE/lower()."""
    needle = query.casefold()
    matched: list[int] = []
    qs = (
        Product.objects.filter(is_available=True)
        .prefetch_related("weight_options")
        .only("id", "name")
        .order_by("name")
    )
    for product in qs.iterator(chunk_size=200):
        if needle in product.name.casefold():
            matched.append(product.id)
            continue
        for option in product.weight_options.all():
            if needle in (option.sku or "").casefold():
                matched.append(product.id)
                break
    return matched


def search_products(query: str) -> QuerySet[Product]:
    """Пошук за назвою або артикулом (sitemap /search/)."""
    query = (query or "").strip()
    if not query:
        return Product.objects.none()
    ids = _match_ids_by_name_or_sku(query)
    if not ids:
        return Product.objects.none()
    preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ids)], output_field=IntegerField())
    return (
        Product.objects.filter(pk__in=ids)
        .select_related("category")
        .prefetch_related("weight_options", "images")
        .annotate(_search_order=preserved)
        .order_by("_search_order")
    )


def suggest_products(query: str, *, limit: int = 8) -> list[Product]:
    """Підказки для шапки: назви доступних товарів, від 2 символів."""
    query = (query or "").strip()
    if len(query) < 2:
        return []
    needle = query.casefold()
    matches: list[Product] = []
    qs = (
        Product.objects.filter(is_available=True)
        .select_related("category")
        .order_by("name")
    )
    for product in qs.iterator(chunk_size=200):
        if needle in product.name.casefold():
            matches.append(product)
            if len(matches) >= limit:
                break
    return matches
