from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import RedirectView, TemplateView

from src.commerce.webhook_views import wayforpay_webhook
from src.core.sitemaps import sitemaps
from src.core.views import healthz

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("tinymce/", include("tinymce.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    path("healthz/", healthz),
    path("webhooks/wayforpay/", wayforpay_webhook, name="wayforpay_webhook"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path(
        "favicon.ico",
        RedirectView.as_view(url=settings.STATIC_URL + "favicon/favicon.ico", permanent=True),
    ),
]

urlpatterns += i18n_patterns(
    path("", include("src.core.urls")),
    path("catalog/", include("src.catalog.urls")),
    path("product/", include("src.catalog.product_urls")),
    path("", include("src.commerce.urls")),
    path("", include("src.content.urls")),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
