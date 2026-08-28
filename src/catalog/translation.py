from modeltranslation.translator import TranslationOptions, register

from .models import Category, Product


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ("name", "seo_title", "seo_description", "seo_h1", "seo_keywords")
    # slug — НЕ перекладається (спільний slug на uk/ru, lock у docs/sitemap.md)
    fallback_undefined = None


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ("name", "description", "seo_title", "seo_description", "seo_h1", "seo_keywords")
    fallback_undefined = None
