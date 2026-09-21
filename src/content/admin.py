from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from modeltranslation.admin import TranslationAdmin
from unfold.admin import ModelAdmin

from src.core.admin_utils import TinyMCEAdminMixin, language_tabs, seo_lang_fields

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
from .translation import HOME_I18N_FIELDS


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


_PAGE_BODY_TINYMCE = ("body_uk", "body_ru", "body")
_PAGE_FIELDSETS = language_tabs(
    uk_fields=("body_uk", *seo_lang_fields("uk")),
    ru_fields=("body_ru", *seo_lang_fields("ru")),
)


@admin.register(HomePage)
class HomePageAdmin(SingletonAdminMixin, TranslationAdmin, ModelAdmin):
    readonly_fields = ("hero_image_preview",)
    fieldsets = language_tabs(
        shared=("hero_image", "hero_image_preview"),
        uk_fields=tuple(f"{name}_uk" for name in HOME_I18N_FIELDS),
        ru_fields=tuple(f"{name}_ru" for name in HOME_I18N_FIELDS),
    )

    @admin.display(description="Попередній перегляд")
    def hero_image_preview(self, obj: HomePage):
        if not obj or not obj.hero_image:
            return "—"
        return format_html('<img src="{}" alt="" width="320" height="180">', obj.hero_image.url)


@admin.register(AboutPage)
class AboutPageAdmin(TinyMCEAdminMixin, SingletonAdminMixin, TranslationAdmin, ModelAdmin):
    tinymce_fields = _PAGE_BODY_TINYMCE
    fieldsets = _PAGE_FIELDSETS


@admin.register(DeliveryPage)
class DeliveryPageAdmin(TinyMCEAdminMixin, SingletonAdminMixin, TranslationAdmin, ModelAdmin):
    tinymce_fields = _PAGE_BODY_TINYMCE
    fieldsets = _PAGE_FIELDSETS


@admin.register(OfferPage)
class OfferPageAdmin(TinyMCEAdminMixin, SingletonAdminMixin, TranslationAdmin, ModelAdmin):
    tinymce_fields = _PAGE_BODY_TINYMCE
    fieldsets = _PAGE_FIELDSETS


@admin.register(PrivacyPage)
class PrivacyPageAdmin(TinyMCEAdminMixin, SingletonAdminMixin, TranslationAdmin, ModelAdmin):
    tinymce_fields = _PAGE_BODY_TINYMCE
    fieldsets = _PAGE_FIELDSETS


@admin.register(ContactsPage)
class ContactsPageAdmin(TinyMCEAdminMixin, SingletonAdminMixin, TranslationAdmin, ModelAdmin):
    tinymce_fields = ("intro_text_uk", "intro_text_ru", "intro_text")
    fieldsets = language_tabs(
        shared=("wholesale_link_url", "phone", "address"),
        uk_fields=("intro_text_uk", *seo_lang_fields("uk")),
        ru_fields=("intro_text_ru", *seo_lang_fields("ru")),
    )


@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonAdminMixin, TranslationAdmin, ModelAdmin):
    fieldsets = language_tabs(
        shared=("min_order_amount", "telegram_notify_orders", "phone"),
        uk_fields=("footer_blurb_uk",),
        ru_fields=("footer_blurb_ru",),
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
