from modeltranslation.translator import TranslationOptions, register

from .models import AboutPage, ContactsPage, DeliveryPage, OfferPage, PrivacyPage, SiteSettings
from .models_home import HomePage

# Якщо значення == default поля, modeltranslation вважає його «порожнім» і бере
# наступну мову з FALLBACK (часто ru). Для CMS з українськими default це ламає uk.
# None = порожнім вважається лише None, не збіг із default.
_CMS_FALLBACK_UNDEFINED = None

HOME_I18N_FIELDS = (
    "hero_title_line1",
    "hero_title_line2",
    "hero_subtitle",
    "hero_image_alt",
    "hero_cta_catalog",
    "hero_cta_hits",
    "hits_title",
    "hits_subtitle",
    "news_title",
    "news_subtitle",
    "trust1_title",
    "trust1_text",
    "trust2_title",
    "trust2_text",
    "trust3_title",
    "trust3_text",
)


@register(HomePage)
class HomePageTranslationOptions(TranslationOptions):
    fields = HOME_I18N_FIELDS
    fallback_undefined = _CMS_FALLBACK_UNDEFINED


@register(AboutPage)
class AboutPageTranslationOptions(TranslationOptions):
    fields = ("body", "seo_title", "seo_description", "seo_h1", "seo_keywords")
    fallback_undefined = _CMS_FALLBACK_UNDEFINED


@register(DeliveryPage)
class DeliveryPageTranslationOptions(TranslationOptions):
    fields = ("body", "seo_title", "seo_description", "seo_h1", "seo_keywords")
    fallback_undefined = _CMS_FALLBACK_UNDEFINED


@register(OfferPage)
class OfferPageTranslationOptions(TranslationOptions):
    fields = ("body", "seo_title", "seo_description", "seo_h1", "seo_keywords")
    fallback_undefined = _CMS_FALLBACK_UNDEFINED


@register(PrivacyPage)
class PrivacyPageTranslationOptions(TranslationOptions):
    fields = ("body", "seo_title", "seo_description", "seo_h1", "seo_keywords")
    fallback_undefined = _CMS_FALLBACK_UNDEFINED


@register(ContactsPage)
class ContactsPageTranslationOptions(TranslationOptions):
    fields = ("intro_text", "seo_title", "seo_description", "seo_h1", "seo_keywords")
    fallback_undefined = _CMS_FALLBACK_UNDEFINED


@register(SiteSettings)
class SiteSettingsTranslationOptions(TranslationOptions):
    fields = ("footer_blurb",)
    fallback_undefined = _CMS_FALLBACK_UNDEFINED
