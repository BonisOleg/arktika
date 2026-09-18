from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import DetailView, ListView

from . import selectors
from .models import Category, Product

PAGINATE_BY = 12

SORT_CHOICES = [
    ("popularity", _("За популярністю")),
    ("price_asc", _("Ціна: зростання")),
    ("price_desc", _("Ціна: спадання")),
    ("new", _("Новинки")),
]


def _query_string_without_page(request) -> str:
    params = request.GET.copy()
    params.pop("page", None)
    encoded = params.urlencode()
    return f"{encoded}&" if encoded else ""


class CatalogListView(ListView):
    """`/catalog/` і `/catalog/<category>/` — fixed columns, без стрибків між сторінками
    (product_grid_skill: paginated PLP не використовує pick_grid_columns)."""

    template_name = "catalog/list.html"
    context_object_name = "products"
    paginate_by = PAGINATE_BY

    def get_category(self):
        slug = self.kwargs.get("slug")
        if not slug:
            return None
        return get_object_or_404(Category, slug=slug, is_active=True)

    def get_tag(self) -> str | None:
        tag = self.request.GET.get("tag", "").strip()
        return tag if tag in selectors.TAG_FILTERS else None

    def get_queryset(self):
        category = self.get_category()
        sort = self.request.GET.get("sort")
        return selectors.get_catalog_products(
            category_slug=category.slug if category else None,
            sort=sort,
            tag=self.get_tag(),
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        category = self.get_category()
        tag = self.get_tag()
        ctx["categories"] = selectors.get_active_categories()
        ctx["active_category"] = category
        ctx["active_tag"] = tag
        ctx["current_sort"] = self.request.GET.get("sort", "popularity")
        ctx["sort_choices"] = SORT_CHOICES
        if tag == "hits":
            ctx["page_title"] = _("Хіти продажу")
        elif tag == "new":
            ctx["page_title"] = _("Новинки")
        else:
            ctx["page_title"] = category.name if category else _("Каталог")
        ctx["query_string"] = _query_string_without_page(self.request)
        return ctx


class ProductDetailView(DetailView):
    """`/product/<slug>/` — галерея, варіанти фасування, breadcrumbs."""

    model = Product
    template_name = "catalog/detail.html"
    context_object_name = "product"

    def get_queryset(self):
        return Product.objects.filter(is_available=True).select_related("category").prefetch_related(
            "weight_options", "images"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = self.object.seo_title or self.object.name
        ctx["related_products"] = (
            Product.objects.filter(category=self.object.category, is_available=True)
            .exclude(pk=self.object.pk)
            .prefetch_related("weight_options", "images")[:4]
        )
        from decimal import Decimal

        from src.commerce import selectors as cart_selectors
        from src.commerce import services as cart_services
        from src.commerce.utils import get_or_create_session_key
        from src.content.models import SiteSettings

        cart = cart_services.get_or_create_cart(get_or_create_session_key(self.request))
        totals = cart_selectors.get_cart_totals(cart)
        ctx["cart_subtotal"] = totals["subtotal"] or Decimal("0")
        ctx["min_order_amount"] = SiteSettings.load().min_order_amount
        return ctx


class SearchView(ListView):
    """`/search/` — пошук за назвою або артикулом (ТЗ §3, тест-кейс №1)."""

    template_name = "catalog/search.html"
    context_object_name = "products"
    paginate_by = PAGINATE_BY

    def get_queryset(self):
        self.query = self.request.GET.get("q", "").strip()
        return selectors.search_products(self.query)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.query
        ctx["page_title"] = _("Пошук: %(query)s") % {"query": self.query} if self.query else _("Пошук")
        ctx["query_string"] = _query_string_without_page(self.request)
        return ctx


class SearchSuggestView(View):
    """HTMX-підказки шапки: назва/артикул, фото і ціна → PDP."""

    def get(self, request):
        query = request.GET.get("q", "").strip()
        products = selectors.suggest_products(query)
        return render(
            request,
            "catalog/partials/search_suggest.html",
            {"products": products, "query": query},
        )
