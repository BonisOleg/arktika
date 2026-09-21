"""Спільні mixin адмінки: TinyMCE (admin_skill) + закладки мов Unfold."""
from tinymce.widgets import TinyMCE

from src.core.html import sanitize_cms_html

LANG_UK_TAB = "Українська"
LANG_RU_TAB = "Русский"


def language_tabs(*, shared=(), uk_fields=(), ru_fields=(), extra=()):
    """Fieldsets: спільні поля + закладки uk/ru + хвости (статуси, collapse)."""
    fieldsets = []
    if shared:
        fieldsets.append((None, {"fields": tuple(shared)}))
    fieldsets.append((LANG_UK_TAB, {"classes": ("tab",), "fields": tuple(uk_fields)}))
    fieldsets.append((LANG_RU_TAB, {"classes": ("tab",), "fields": tuple(ru_fields)}))
    fieldsets.extend(extra)
    return tuple(fieldsets)


def seo_lang_fields(lang: str) -> tuple[str, ...]:
    return (
        f"seo_title_{lang}",
        f"seo_description_{lang}",
        f"seo_h1_{lang}",
        f"seo_keywords_{lang}",
    )


class TinyMCEAdminMixin:
    """Великі TextField → django-tinymce; sanitize на збереженні (SEC-04)."""

    tinymce_fields: tuple[str, ...] = ()

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tinymce_fields:
            kwargs["widget"] = TinyMCE()
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        for name in self.tinymce_fields:
            value = getattr(obj, name, None)
            if value:
                setattr(obj, name, sanitize_cms_html(value))
        super().save_model(request, obj, form, change)
