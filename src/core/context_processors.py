from django.conf import settings

from src.content.models import SiteSettings
from src.core.templatetags.i18n_extras import path_for_language


def site_settings(request):
    """Глобальні налаштування сайту (мін. сума замовлення, телефон) — SiteSettings singleton."""
    return {"site_settings": SiteSettings.load()}


def hreflang_urls(request):
    """SEO/SKILL.md §1.1/§4 — canonical (без query params), self-referencing hreflang (uk/ru)
    + x-default (LANGUAGE_CODE=uk). Без translate_url (django-i18n-prefix-switcher)."""
    tags = [
        {"lang": lang_code, "url": request.build_absolute_uri(path_for_language(request.path, lang_code))}
        for lang_code, _label in settings.LANGUAGES
    ]
    default_url = request.build_absolute_uri(path_for_language(request.path, settings.LANGUAGE_CODE))
    return {
        "hreflang_urls": tags,
        "hreflang_default_url": default_url,
        "canonical_url": request.build_absolute_uri(request.path),
    }
