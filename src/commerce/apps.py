from django.apps import AppConfig


class CommerceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.commerce"
    label = "commerce"
    verbose_name = "Продажі"
