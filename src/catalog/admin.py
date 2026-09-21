from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from unfold.admin import ModelAdmin, TabularInline

from src.core.admin_utils import TinyMCEAdminMixin, language_tabs, seo_lang_fields

from .models import Category, Product, ProductImage, ProductWeightOption


class ProductWeightOptionInline(TabularInline):
    model = ProductWeightOption
    extra = 1
    fields = ("label", "unit", "price", "min_quantity", "approx_unit_weight", "sku", "is_default", "sort_order")


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "alt", "is_primary", "sort_order")


@admin.register(Category)
class CategoryAdmin(TranslationAdmin, ModelAdmin):
    list_display = ("name", "slug", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name_uk",)}
    fieldsets = language_tabs(
        shared=("slug", "image", "sort_order", "is_active"),
        uk_fields=("name_uk", *seo_lang_fields("uk")),
        ru_fields=("name_ru", *seo_lang_fields("ru")),
    )


@admin.register(Product)
class ProductAdmin(TinyMCEAdminMixin, TranslationAdmin, ModelAdmin):
    tinymce_fields = ("description_uk", "description_ru", "description")
    list_display = ("name", "category", "is_available", "is_hit", "is_new", "default_price", "sale_mode")
    list_editable = ("is_available", "is_hit", "is_new")
    list_filter = ("category", "is_available", "is_hit", "is_new")
    search_fields = ("name", "weight_options__sku")
    prepopulated_fields = {"slug": ("name_uk",)}
    inlines = (ProductWeightOptionInline, ProductImageInline)
    fieldsets = language_tabs(
        shared=("category", "slug"),
        uk_fields=("name_uk", "description_uk", *seo_lang_fields("uk")),
        ru_fields=("name_ru", "description_ru", *seo_lang_fields("ru")),
        extra=(("Статуси", {"fields": ("is_available", "is_hit", "is_new")}),),
    )

    @admin.display(description="Ціна від")
    def default_price(self, obj: Product):
        option = obj.default_option
        return f"{option.price} грн/{option.get_unit_display()}" if option else "—"

    @admin.display(description="Тип")
    def sale_mode(self, obj: Product):
        return "Ваговий (кг)" if obj.is_weighted else "Штучний"
