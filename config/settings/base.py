"""Спільні налаштування Arctica. Секрети — лише через .env (python-decouple)."""
from pathlib import Path

from decouple import Csv, config
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from src.core.admin_url import ADMIN_URL_FALLBACK, resolve_admin_url

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY")  # без default — прод падає без .env
DEBUG = False
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())

ADMIN_URL = resolve_admin_url(config("ADMIN_URL", default=ADMIN_URL_FALLBACK))

INSTALLED_APPS = [
    # Unfold перед django.contrib.admin
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    # modeltranslation — ОБОВ'ЯЗКОВО перед django.contrib.admin (не після, як у
    # деяких старих нотатках admin_skill): інакше admin.autodiscover() реєструє
    # ModelAdmin для Category/Product ДО того, як модель зареєстрована для
    # перекладу → modeltranslation.translator.NotRegistered при старті проєкту.
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
    # 3rd-party
    "django_htmx",
    "csp",
    "django_recaptcha",
    # Arctica apps
    "src.core",
    "src.accounts",
    "src.catalog",
    "src.commerce",
    "src.shipping",
    "src.content",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "csp.middleware.CSPMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "src.core.context_processors.site_settings",
                "src.core.context_processors.hreflang_urls",
                "src.catalog.context_processors.header_catalog",
                "src.commerce.context_processors.cart_summary",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB", default="arctica"),
        "USER": config("POSTGRES_USER", default="arctica"),
        "PASSWORD": config("POSTGRES_PASSWORD", default=""),
        "HOST": config("POSTGRES_HOST", default="db"),
        "PORT": config("POSTGRES_PORT", default="5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── i18n (uk дефолт без префіксу, ru з /ru/) ────────────────────────────────
LANGUAGE_CODE = "uk"
LANGUAGES = [
    ("uk", "Українська"),
    ("ru", "Русский"),
]
MODELTRANSLATION_DEFAULT_LANGUAGE = "uk"
MODELTRANSLATION_LANGUAGES = ("uk", "ru")
MODELTRANSLATION_FALLBACK_LANGUAGES = ("uk", "ru")
LOCALE_PATHS = [BASE_DIR / "locale"]

TIME_ZONE = "Europe/Kyiv"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SITE_DOMAIN = config("SITE_DOMAIN", default="localhost:8000")
SITE_PROTOCOL = config("SITE_PROTOCOL", default="http")

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 днів — досить для guest-кошика

LOGIN_URL = "admin:login"

# ── Nova Poshta (Фаза 0.5+) ─────────────────────────────────────────────────
NP_API_KEY = config("NP_API_KEY", default="")
NP_SENDER_REF = config("NP_SENDER_REF", default="")
NP_SENDER_CITY_REF = config("NP_SENDER_CITY_REF", default="")
NP_SENDER_CONTACT_REF = config("NP_SENDER_CONTACT_REF", default="")
NP_SENDER_PHONE = config("NP_SENDER_PHONE", default="")
# True = місто/відділення лише зі списку НП (потрібні fixtures або NP_API_KEY).
# False = тимчасово достатньо вільного тексту (для тестів без ключа НП).
NP_REQUIRE_REF_SELECTION = config("NP_REQUIRE_REF_SELECTION", default=False, cast=bool)

# ── WayForPay (canonical, sandbox доки немає мерчант-ключів) ───────────────
WAYFORPAY_MERCHANT_LOGIN = config("WAYFORPAY_MERCHANT_LOGIN", default="")
WAYFORPAY_MERCHANT_SECRET_KEY = config("WAYFORPAY_MERCHANT_SECRET_KEY", default="")
WAYFORPAY_DOMAIN = config("WAYFORPAY_DOMAIN", default=SITE_DOMAIN)

# ── Telegram notifier (env-gated, без токена — лише лог) ───────────────────
TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_CHAT_ID = config("TELEGRAM_CHAT_ID", default="")

# ── reCAPTCHA v2 (вимкнено без ключів) ──────────────────────────────────────
RECAPTCHA_PUBLIC_KEY = config("RECAPTCHA_PUBLIC_KEY", default="")
RECAPTCHA_PRIVATE_KEY = config("RECAPTCHA_PRIVATE_KEY", default="")
SILENCED_SYSTEM_CHECKS = ["django_recaptcha.recaptcha_test_key_error"]

# ── Мінімальна сума замовлення — фолбек, канонічне значення в SiteSettings ─
DEFAULT_MIN_ORDER_AMOUNT = "500.00"

# ── CSP (day one, django-csp 4.0 dict-based формат) ─────────────────────────
CONTENT_SECURITY_POLICY = {
    # Unfold/Alpine.js потребують unsafe-eval в адмінці — виняток лише для ADMIN_URL
    "EXCLUDE_URL_PREFIXES": [f"/{ADMIN_URL}"],
    "DIRECTIVES": {
        "default-src": ["'self'"],
        "script-src": ["'self'"],
        "style-src": ["'self'", "https://fonts.googleapis.com"],
        "font-src": ["'self'", "https://fonts.gstatic.com"],
        "img-src": ["'self'", "data:"],
        "connect-src": ["'self'"],
        "frame-src": ["https://www.google.com"],  # reCAPTCHA
        "frame-ancestors": ["'none'"],
    },
}

UNFOLD = {
    "SITE_TITLE": "Арктика",
    "SITE_HEADER": "Арктика",
    "SITE_SYMBOL": "ac_unit",
    "SHOW_LANGUAGES": True,
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "any",
            "type": "image/x-icon",
            "href": "/static/favicon/favicon.ico",
        },
    ],
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("Каталог"),
                "separator": True,
                "items": [
                    {
                        "title": _("Товари"),
                        "icon": "inventory_2",
                        "link": reverse_lazy("admin:catalog_product_changelist"),
                    },
                    {
                        "title": _("Категорії"),
                        "icon": "category",
                        "link": reverse_lazy("admin:catalog_category_changelist"),
                    },
                ],
            },
            {
                "title": _("Продажі"),
                "separator": True,
                "items": [
                    {
                        "title": _("Замовлення"),
                        "icon": "shopping_bag",
                        "link": reverse_lazy("admin:commerce_order_changelist"),
                    },
                ],
            },
            {
                "title": _("Нова Пошта"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Відправлення"),
                        "icon": "local_shipping",
                        "link": reverse_lazy("admin:shipping_shipment_changelist"),
                    },
                    {
                        "title": _("Міста"),
                        "icon": "location_city",
                        "link": reverse_lazy("admin:shipping_npcity_changelist"),
                    },
                    {
                        "title": _("Відділення"),
                        "icon": "warehouse",
                        "link": reverse_lazy("admin:shipping_npwarehouse_changelist"),
                    },
                ],
            },
            {
                "title": _("Сайт"),
                "separator": True,
                "items": [
                    {
                        "title": _("Головна"),
                        "icon": "home",
                        "link": reverse_lazy("admin:content_homepage_changelist"),
                    },
                    {
                        "title": _("Налаштування"),
                        "icon": "settings",
                        "link": reverse_lazy("admin:content_sitesettings_changelist"),
                    },
                    {
                        "title": _("Звернення"),
                        "icon": "mail",
                        "link": reverse_lazy("admin:content_contactmessage_changelist"),
                    },
                    {
                        "title": _("Про нас"),
                        "icon": "info",
                        "link": reverse_lazy("admin:content_aboutpage_changelist"),
                    },
                    {
                        "title": _("Доставка і оплата"),
                        "icon": "payments",
                        "link": reverse_lazy("admin:content_deliverypage_changelist"),
                    },
                    {
                        "title": _("Контакти"),
                        "icon": "call",
                        "link": reverse_lazy("admin:content_contactspage_changelist"),
                    },
                    {
                        "title": _("Оферта"),
                        "icon": "description",
                        "link": reverse_lazy("admin:content_offerpage_changelist"),
                    },
                    {
                        "title": _("Конфіденційність"),
                        "icon": "privacy_tip",
                        "link": reverse_lazy("admin:content_privacypage_changelist"),
                    },
                ],
            },
            {
                "title": _("Доступ"),
                "separator": True,
                "items": [
                    {
                        "title": _("Користувачі"),
                        "icon": "person",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                    },
                ],
            },
        ],
    },
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "src": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
