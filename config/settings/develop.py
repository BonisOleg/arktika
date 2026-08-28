from decouple import config

from .base import *  # noqa: F401,F403

SECRET_KEY = config("SECRET_KEY", default="dev-only-insecure-key-do-not-use-in-prod")
DEBUG = True
ALLOWED_HOSTS = ["*"]

CONTENT_SECURITY_POLICY["DIRECTIVES"]["script-src"].append("'unsafe-eval'")  # Alpine/Unfold у DEBUG

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
