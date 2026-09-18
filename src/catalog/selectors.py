"""Selectors — лише читання (ecommerce_business_logic_skill), без мутацій."""
from django.db.models import Case, F, IntegerField, Min, QuerySet, When

from .models import Category, Product

# і/ї/є/ґ ↔ и/е/г — інакше «икра» не знаходить «Ікра», «скумбрия» — «Скумбрія».
_CYR_FOLD = str.maketrans({"і": "и", "ї": "и", "є": "е", "ґ": "г"})


def _fold_cyr(text: str) -> str:
    return (text or "").casefold().translate(_CYR_FOLD)


def _needle_stems(query: str) -> list[str]:
    needle = _fold_cyr(query).strip()
    if not needle:
        return []
    stems = [needle]
    if len(needle) >= 4:
        trimmed = needle.rstrip("ьъйы")
        if len(trimmed) >= 4 and trimmed not in stems:
            stems.append(trimmed)
        short = needle[:-1]
        if len(short) >= 4 and short not in stems:
            stems.append(short)
    return stems


def _matches_haystack(query: str, *parts: str) -> bool:
    hay = _fold_cyr(" ".join(p for p in parts if p))
    if not hay:
        return False
    return any(stem in hay for stem in _needle_stems(query))


def _product_name_parts(product: Product) -> list[str]:
    return [
        product.name,
        getattr(product, "name_uk", "") or "",
        getattr(product, "name_ru", "") or "",
    ]


def _product_sku_parts(product: Product) -> list[str]:
    return [option.sku or "" for option in product.weight_options.all()]


def _product_search_parts(product: Product) -> list[str]:
    return [
        *_product_name_parts(product),
        product.description,
        getattr(product, "description_uk", "") or "",
        getattr(product, "description_ru", "") or "",
        *_product_sku_parts(product),
    ]


def _product_matches_query(product: Product, query: str) -> bool:
    return _matches_haystack(query, *_product_search_parts(product))


def _suggest_name_skus(product: Product) -> tuple[list[str], list[str]]:
    names = [_fold_cyr(part) for part in _product_name_parts(product) if part]
    skus = [_fold_cyr(part) for part in _product_sku_parts(product) if part]
    return names, skus


def _suggest_matches(product: Product, query: str) -> bool:
    """Короткий запит — лише префікс назви/слова; від 4 символів — входження."""
    stems = _needle_stems(query)
    if not stems:
        return False
    names, skus = _suggest_name_skus(product)
    short = len(_fold_cyr(query).strip()) < 4
    for stem in stems:
        if any(stem in sku for sku in skus):
            return True
        for name in names:
            if name.startswith(stem):
                return True
            if any(word.startswith(stem) for word in name.split()):
                return True
            if not short and stem in name:
                return True
    return False


def _suggest_rank(product: Product, query: str) -> int:
    """0 — префікс назви, 1 — слово в назві, 2 — артикул, 3 — входження в назву."""
    stems = _needle_stems(query)
    names, skus = _suggest_name_skus(product)
    best = 9
    for stem in stems:
        for name in names:
            if name.startswith(stem):
                best = min(best, 0)
            elif any(word.startswith(stem) for word in name.split()):
                best = min(best, 1)
            elif stem in name:
                best = min(best, 3)
        if any(stem in sku for sku in skus):
            best = min(best, 2)
    return best

# price_* — Min(weight_options.price) = те саме «від … грн» на картці.
# Прямий order_by(weight_options__price) дає JOIN → дублікати й кривий порядок.
SORT_OPTIONS = {
    "popularity": ("-is_hit", "-created_at", "name"),
    "price_asc": (F("sort_price").asc(nulls_last=True), "name"),
    "price_desc": (F("sort_price").desc(nulls_last=True), "name"),
    "new": ("-created_at", "name"),
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
        .annotate(sort_price=Min("weight_options__price"))
    )
    if category_slug:
        qs = qs.filter(category__slug=category_slug)
    tag_field = TAG_FILTERS.get(tag or "")
    if tag_field:
        qs = qs.filter(**{tag_field: True})
    order_by = SORT_OPTIONS.get(sort or "popularity", SORT_OPTIONS["popularity"])
    return qs.order_by(*order_by)


def _match_ids_by_name_or_sku(query: str) -> list[int]:
    """Кирилиця в Python (Postgres lc_collate=C не згортає ILIKE) + uk/ru поля."""
    matched: list[int] = []
    qs = (
        Product.objects.filter(is_available=True)
        .prefetch_related("weight_options")
        .order_by("name")
    )
    for product in qs:
        if _product_matches_query(product, query):
            matched.append(product.id)
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
    """Підказки шапки: назва uk/ru + артикул, без опису; релевантність, не алфавіт."""
    query = (query or "").strip()
    if len(query) < 2:
        return []
    matches: list[Product] = []
    qs = (
        Product.objects.filter(is_available=True, category__is_active=True)
        .select_related("category")
        .prefetch_related("weight_options", "images")
    )
    for product in qs:
        if _suggest_matches(product, query):
            matches.append(product)
    matches.sort(key=lambda product: (_suggest_rank(product, query), _fold_cyr(product.name)))
    return matches[:limit]
