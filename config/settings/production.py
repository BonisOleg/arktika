from decouple import config

from .base import *  # noqa: F401,F403

DEBUG = False

# django-docker-nginx: static/media віддає nginx (alias на STATIC_ROOT/MEDIA_ROOT),
# WhiteNoise у контейнері backend — лишній шар.
MIDDLEWARE = [m for m in MIDDLEWARE if m != "whitenoise.middleware.WhiteNoiseMiddleware"]  # noqa: F405

# django-docker-ssl: TLS у nginx. Gunicorn завжди HTTP — інакше /healthz/ ловить 301.
# USE_HTTPS=True лише після certbot: Secure-cookies + HSTS. Редірект http→https — nginx.
USE_HTTPS = config("USE_HTTPS", default=False, cast=bool)

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = USE_HTTPS
CSRF_COOKIE_SECURE = USE_HTTPS
SESSION_COOKIE_SAMESITE = "Strict"
CSRF_COOKIE_SAMESITE = "Strict"
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30 if USE_HTTPS else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = USE_HTTPS
SECURE_HSTS_PRELOAD = USE_HTTPS

CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="",
    cast=lambda v: [s.strip() for s in v.split(",") if s.strip()],
)

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
