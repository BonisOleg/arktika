"""Заповнити російські поля HomePage (раніше дублювали українські дефолти)."""

from django.db import migrations

RU_VALUES = {
    "hero_title_line1_ru": "Рыба, которую мы",
    "hero_title_line2_ru": "делаем сами",
    "hero_subtitle_ru": "Коптим, солим и вялим. Доставляем по Украине.",
    "hero_image_alt_ru": "Красная и чёрная икра, юкола форели и копчёная скумбрия",
    "hero_cta_catalog_ru": "Перейти в каталог",
    "hero_cta_hits_ru": "Смотреть хиты",
    "hits_title_ru": "Хиты продаж",
    "hits_subtitle_ru": "Популярные позиции для розничного заказа.",
    "news_title_ru": "Новинки",
    "news_subtitle_ru": "Свежие позиции ассортимента.",
    "trust1_title_ru": "Собственное производство",
    "trust1_text_ru": "Классическая технология копчения и посола.",
    "trust2_title_ru": "Доставка НП",
    "trust2_text_ru": "По Украине, оплата по тарифам перевозчика.",
    "trust3_title_ru": "Онлайн-оплата",
    "trust3_text_ru": "Безопасная оплата картой через WayForPay.",
}

UK_VALUES = {
    "hero_title_line1_uk": "Риба яку ми",
    "hero_title_line2_uk": "робимо самі",
    "hero_subtitle_uk": "Коптимо, солимо та в'ялим. Доставляємо по Україні.",
    "hero_image_alt_uk": "Червона та чорна ікра, юкола форелі та копчена скумбрія",
    "hero_cta_catalog_uk": "Перейти до каталогу",
    "hero_cta_hits_uk": "Дивитись хіти",
    "hits_title_uk": "Хіти продажу",
    "hits_subtitle_uk": "Популярні позиції для роздрібного замовлення.",
    "news_title_uk": "Новинки",
    "news_subtitle_uk": "Свіжі позиції асортименту.",
    "trust1_title_uk": "Власне виробництво",
    "trust1_text_uk": "Класична технологія копчення та посолу.",
    "trust2_title_uk": "Доставка НП",
    "trust2_text_uk": "По Україні, оплата за тарифами перевізника.",
    "trust3_title_uk": "Онлайн-оплата",
    "trust3_text_uk": "Безпечна оплата карткою через WayForPay.",
}


def seed_home_i18n(apps, schema_editor):
    HomePage = apps.get_model("content", "HomePage")
    page, _ = HomePage.objects.get_or_create(pk=1)
    for field, value in {**UK_VALUES, **RU_VALUES}.items():
        setattr(page, field, value)
    page.save(update_fields=list({**UK_VALUES, **RU_VALUES}.keys()))


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0004_homepage_singleton"),
    ]

    operations = [
        migrations.RunPython(seed_home_i18n, noop),
    ]
