from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from src.catalog.models import Category, Product


class HomeSitemap(Sitemap):
    """Головна — найвищий пріоритет (SEO/SKILL.md §1.3: головна 1.0 → категорії 0.8 → сторінки 0.6)."""

    i18n = True
    changefreq = "daily"
    priority = 1.0

    def items(self):
        return ["core:home"]

    def location(self, item):
        return reverse(item)


class StaticViewSitemap(Sitemap):
    """Каталог + інфосторінки — sitemap.xml обидві мови."""

    i18n = True
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return [
            "catalog:list",
            "content:about",
            "content:delivery",
            "content:contacts",
            "content:offer",
            "content:privacy",
        ]

    def location(self, item):
        return reverse(item)


class CategorySitemap(Sitemap):
    i18n = True
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Category.objects.filter(is_active=True)

    def location(self, obj):
        return obj.get_absolute_url()


class ProductSitemap(Sitemap):
    i18n = True
    changefreq = "daily"
    priority = 0.7

    def items(self):
        return Product.objects.filter(is_available=True).select_related("category")

    def location(self, obj):
        return obj.get_absolute_url()

    def lastmod(self, obj):
        return obj.updated_at


sitemaps = {
    "home": HomeSitemap,
    "static": StaticViewSitemap,
    "categories": CategorySitemap,
    "products": ProductSitemap,
}
