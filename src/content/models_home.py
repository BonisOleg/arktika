"""Головна сторінка — синглтон з усіма CMS-текстами секцій."""
from django.db import models

from src.core.models import SingletonModel, TimeStampedModel


def home_hero_upload_to(instance, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    return f"home/hero.{ext}"


class HomePage(SingletonModel, TimeStampedModel):
    """Контент головної: hero, заголовки блоків хітів/новинок, trust-смуга."""

    # —— Hero ——
    hero_title_line1 = models.CharField("Hero: рядок 1 заголовка", max_length=120, default="Риба яку ми")
    hero_title_line2 = models.CharField("Hero: рядок 2 заголовка", max_length=120, default="робимо самі")
    hero_subtitle = models.CharField(
        "Hero: підзаголовок",
        max_length=255,
        default="Коптимо, солимо та в'ялим. Доставляємо по Україні.",
    )
    hero_image = models.ImageField(
        "Hero: фото",
        upload_to=home_hero_upload_to,
        blank=True,
        help_text="Якщо порожньо — використовується стандартне фото з static.",
    )
    hero_image_alt = models.CharField(
        "Hero: alt фото",
        max_length=255,
        blank=True,
        default="Червона та чорна ікра, юкола форелі та копчена скумбрія",
    )
    hero_cta_catalog = models.CharField(
        "Hero: кнопка каталогу",
        max_length=80,
        default="Перейти до каталогу",
    )
    hero_cta_hits = models.CharField(
        "Hero: кнопка хітів",
        max_length=80,
        default="Дивитись хіти",
    )

    # —— Секція хітів ——
    hits_title = models.CharField("Хіти: заголовок", max_length=120, default="Хіти продажу")
    hits_subtitle = models.CharField(
        "Хіти: підзаголовок",
        max_length=255,
        default="Популярні позиції для роздрібного замовлення.",
    )

    # —— Секція новинок ——
    news_title = models.CharField("Новинки: заголовок", max_length=120, default="Новинки")
    news_subtitle = models.CharField(
        "Новинки: підзаголовок",
        max_length=255,
        default="Свіжі позиції асортименту.",
    )

    # —— Trust strip ——
    trust1_title = models.CharField("Перевага 1: заголовок", max_length=80, default="Власне виробництво")
    trust1_text = models.CharField(
        "Перевага 1: текст",
        max_length=255,
        default="Класична технологія копчення та посолу.",
    )
    trust2_title = models.CharField("Перевага 2: заголовок", max_length=80, default="Доставка НП")
    trust2_text = models.CharField(
        "Перевага 2: текст",
        max_length=255,
        default="По Україні, оплата за тарифами перевізника.",
    )
    trust3_title = models.CharField("Перевага 3: заголовок", max_length=80, default="Онлайн-оплата")
    trust3_text = models.CharField(
        "Перевага 3: текст",
        max_length=255,
        default="Безпечна оплата карткою через WayForPay.",
    )

    class Meta:
        verbose_name = "Головна"
        verbose_name_plural = "Головна"

    def __str__(self) -> str:
        return "Головна"

    @property
    def trust_items(self) -> list[dict[str, str]]:
        return [
            {"title": self.trust1_title, "text": self.trust1_text},
            {"title": self.trust2_title, "text": self.trust2_text},
            {"title": self.trust3_title, "text": self.trust3_text},
        ]
