from django.db import models

from src.core.models import SanitizedHtmlMixin, SeoFieldsMixin, SingletonModel, TimeStampedModel

from .models_home import HomePage  # noqa: F401

DEFAULT_MIN_ORDER_AMOUNT = "500.00"


class AboutPage(SanitizedHtmlMixin, SingletonModel, TimeStampedModel, SeoFieldsMixin):
    html_fields = ("body",)
    body = models.TextField("Текст", blank=True)

    class Meta:
        verbose_name = "Про нас"
        verbose_name_plural = "Про нас"

    def __str__(self) -> str:
        return "Про нас"


class DeliveryPage(SanitizedHtmlMixin, SingletonModel, TimeStampedModel, SeoFieldsMixin):
    html_fields = ("body",)
    body = models.TextField("Текст", blank=True)

    class Meta:
        verbose_name = "Доставка і оплата"
        verbose_name_plural = "Доставка і оплата"

    def __str__(self) -> str:
        return "Доставка і оплата"


class OfferPage(SanitizedHtmlMixin, SingletonModel, TimeStampedModel, SeoFieldsMixin):
    html_fields = ("body",)
    body = models.TextField("Текст оферти", blank=True)

    class Meta:
        verbose_name = "Оферта"
        verbose_name_plural = "Оферта"

    def __str__(self) -> str:
        return "Оферта"


class PrivacyPage(SanitizedHtmlMixin, SingletonModel, TimeStampedModel, SeoFieldsMixin):
    html_fields = ("body",)
    body = models.TextField("Текст політики конфіденційності", blank=True)

    class Meta:
        verbose_name = "Конфіденційність"
        verbose_name_plural = "Конфіденційність"

    def __str__(self) -> str:
        return "Політика конфіденційності"


class ContactsPage(SanitizedHtmlMixin, SingletonModel, TimeStampedModel, SeoFieldsMixin):
    html_fields = ("intro_text",)
    intro_text = models.TextField("Текст над формою", blank=True)
    wholesale_link_url = models.URLField(
        "Посилання на опт", default="https://rk-arctica.com.ua/"
    )
    phone = models.CharField("Телефон", max_length=32, blank=True)
    address = models.CharField("Адреса", max_length=255, blank=True)

    class Meta:
        verbose_name = "Контакти"
        verbose_name_plural = "Контакти"

    def __str__(self) -> str:
        return "Контакти"


class ContactMessage(models.Model):
    name = models.CharField("Ім'я", max_length=255)
    phone = models.CharField("Телефон", max_length=32, blank=True)
    email = models.EmailField("Email", blank=True)
    message = models.TextField("Повідомлення")
    consent_gdpr = models.BooleanField("Згода на обробку ПД", default=False)
    is_read = models.BooleanField("Прочитано", default=False)
    created_at = models.DateTimeField("Дата", auto_now_add=True)

    class Meta:
        verbose_name = "Звернення"
        verbose_name_plural = "Звернення"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.created_at:%d.%m.%Y})"


class SiteSettings(SingletonModel):
    """Singleton — SiteSettings.load(). min_order_amount поза каноном skill (розділ 2 плану)."""

    min_order_amount = models.DecimalField("Мін. сума замовлення", max_digits=10, decimal_places=2, default=DEFAULT_MIN_ORDER_AMOUNT)
    phone = models.CharField("Телефон", max_length=32, blank=True, default="+38 (000) 000-00-00")
    telegram_notify_orders = models.BooleanField("Сповіщати в Telegram про замовлення", default=True)
    footer_blurb = models.CharField(
        "Текст під логотипом у футері",
        max_length=255,
        blank=True,
        default="Роздрібний інтернет-магазин рибної продукції власного виробництва. Доставка по Україні.",
    )

    class Meta:
        verbose_name = "Налаштування"
        verbose_name_plural = "Налаштування"

    def __str__(self) -> str:
        return "Налаштування"
