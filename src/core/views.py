from django.http import HttpResponse
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from src.catalog.models import Product
from src.content.models_home import HomePage


class HomeView(TemplateView):
    """Головна: CMS-тексти з HomePage + хіти/новинки з каталогу."""

    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Арктика — рибна продукція власного виробництва")
        ctx["home"] = HomePage.load()
        ctx["hits"] = (
            Product.objects.filter(is_available=True, is_hit=True)
            .select_related("category")
            .prefetch_related("weight_options", "images")[:4]
        )
        ctx["new_products"] = (
            Product.objects.filter(is_available=True, is_new=True)
            .select_related("category")
            .prefetch_related("weight_options", "images")[:4]
        )
        return ctx


def healthz(request):
    return HttpResponse("ok")
