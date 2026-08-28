from django.conf import settings
from django.urls import translate_url

from src.content.models import SiteSettings


def site_settings(request):
    """Глобальні налаштування сайту (мін. сума замовлення, телефон) — SiteSettings singleton."""
    return {"site_settings": SiteSettings.load()}


def hreflang_urls(request):
    """SEO/SKILL.md §1.1/§4 — canonical (без query params), self-referencing hreflang (uk/ru)
    + x-default (LANGUAGE_CODE=uk)."""
    tags = [
        {"lang": lang_code, "url": request.build_absolute_uri(translate_url(request.path, lang_code))}
        for lang_code, _label in settings.LANGUAGES
    ]
    default_url = request.build_absolute_uri(translate_url(request.path, settings.LANGUAGE_CODE))
    return {
        "hreflang_urls": tags,
        "hreflang_default_url": default_url,
        "canonical_url": request.build_absolute_uri(request.path),
    }
