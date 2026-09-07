from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin
from unfold.admin import ModelAdmin, TabularInline

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
class CategoryAdmin(TabbedTranslationAdmin, ModelAdmin):
    list_display = ("name", "slug", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        (None, {"fields": ("name", "slug", "image", "sort_order", "is_active")}),
        ("SEO", {"fields": ("seo_title", "seo_description", "seo_h1", "seo_keywords"), "classes": ("collapse",)}),
    )


@admin.register(Product)
class ProductAdmin(TabbedTranslationAdmin, ModelAdmin):
    list_display = ("name", "category", "is_available", "is_hit", "is_new", "default_price", "sale_mode")
    list_editable = ("is_available", "is_hit", "is_new")
    list_filter = ("category", "is_available", "is_hit", "is_new")
    search_fields = ("name", "weight_options__sku")
    prepopulated_fields = {"slug": ("name",)}
    inlines = (ProductWeightOptionInline, ProductImageInline)
    fieldsets = (
        (None, {"fields": ("category", "name", "slug", "description")}),
        ("Статуси", {"fields": ("is_available", "is_hit", "is_new")}),
        ("SEO", {"fields": ("seo_title", "seo_description", "seo_h1", "seo_keywords"), "classes": ("collapse",)}),
    )

    @admin.display(description="Ціна від")
    def default_price(self, obj: Product):
        option = obj.default_option
        return f"{option.price} грн/{option.get_unit_display()}" if option else "—"

    @admin.display(description="Тип")
    def sale_mode(self, obj: Product):
        return "Ваговий (кг)" if obj.is_weighted else "Штучний"
