from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from modeltranslation.admin import TabbedTranslationAdmin
from unfold.admin import ModelAdmin

from .models import (
    AboutPage,
    ContactMessage,
    ContactsPage,
    DeliveryPage,
    OfferPage,
    PrivacyPage,
    SiteSettings,
)
from .models_home import HomePage


class SingletonAdminMixin:
    """600i2 — рівно один рядок; changelist одразу веде на change-форму pk=1."""

    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = self.model.load()
        return redirect(
            reverse(
                f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
                args=[obj.pk],
            )
        )


@admin.register(HomePage)
class HomePageAdmin(SingletonAdminMixin, TabbedTranslationAdmin, ModelAdmin):
    readonly_fields = ("hero_image_preview",)
    fieldsets = (
        (
            "Hero",
            {
                "fields": (
                    "hero_title_line1",
                    "hero_title_line2",
                    "hero_subtitle",
                    "hero_image",
                    "hero_image_preview",
                    "hero_image_alt",
                    "hero_cta_catalog",
                    "hero_cta_hits",
                )
            },
        ),
        ("Хіти продажу", {"fields": ("hits_title", "hits_subtitle")}),
        ("Новинки", {"fields": ("news_title", "news_subtitle")}),
        (
            "Переваги",
            {
                "fields": (
                    "trust1_title",
                    "trust1_text",
                    "trust2_title",
                    "trust2_text",
                    "trust3_title",
                    "trust3_text",
                )
            },
        ),
    )

    @admin.display(description="Попередній перегляд")
    def hero_image_preview(self, obj: HomePage):
        if not obj or not obj.hero_image:
            return "—"
        return format_html('<img src="{}" alt="" width="320" height="180">', obj.hero_image.url)


@admin.register(AboutPage)
class AboutPageAdmin(SingletonAdminMixin, TabbedTranslationAdmin, ModelAdmin):
    fieldsets = (
        (None, {"fields": ("body",)}),
        ("SEO", {"fields": ("seo_title", "seo_description", "seo_h1", "seo_keywords"), "classes": ("collapse",)}),
    )


@admin.register(DeliveryPage)
class DeliveryPageAdmin(SingletonAdminMixin, TabbedTranslationAdmin, ModelAdmin):
    fieldsets = AboutPageAdmin.fieldsets


@admin.register(OfferPage)
class OfferPageAdmin(SingletonAdminMixin, TabbedTranslationAdmin, ModelAdmin):
    fieldsets = AboutPageAdmin.fieldsets


@admin.register(PrivacyPage)
class PrivacyPageAdmin(SingletonAdminMixin, TabbedTranslationAdmin, ModelAdmin):
    fieldsets = AboutPageAdmin.fieldsets


@admin.register(ContactsPage)
class ContactsPageAdmin(SingletonAdminMixin, TabbedTranslationAdmin, ModelAdmin):
    fieldsets = (
        (None, {"fields": ("intro_text", "wholesale_link_url", "phone", "address")}),
        ("SEO", {"fields": ("seo_title", "seo_description", "seo_h1", "seo_keywords"), "classes": ("collapse",)}),
    )


@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonAdminMixin, TabbedTranslationAdmin, ModelAdmin):
    fieldsets = (
        ("Замовлення", {"fields": ("min_order_amount", "telegram_notify_orders")}),
        ("Контакти", {"fields": ("phone",)}),
        ("Футер", {"fields": ("footer_blurb",)}),
    )


@admin.register(ContactMessage)
class ContactMessageAdmin(ModelAdmin):
    list_display = ("name", "phone", "email", "short_message", "is_read", "created_at")
    list_editable = ("is_read",)
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "phone", "email", "message")
    readonly_fields = ("name", "phone", "email", "message", "consent_gdpr", "created_at")
    ordering = ("-created_at",)

    @admin.display(description="Текст")
    def short_message(self, obj: ContactMessage) -> str:
        text = (obj.message or "").strip()
        return text if len(text) <= 60 else f"{text[:57]}…"
