"""Nova Poshta — Фаза 0.5 (novaposhta_skill): без NP_API_KEY працюємо на fixture-довіднику.

Коли клієнт надасть ключ (docs/Питання_без_відповіді.md 4.5) — `sync_cities_and_warehouses()`
підмінюється на реальні запити до `https://api.novaposhta.ua/v2.0/json/`, сигнатура викликів
(`get_cities`, `get_warehouses`) лишається незмінною для views/forms.
"""
import logging

from django.conf import settings

from .models import NPCity, NPWarehouse

logger = logging.getLogger("src.shipping")

NP_API_URL = "https://api.novaposhta.ua/v2.0/json/"


def is_live_mode() -> bool:
    return bool(settings.NP_API_KEY)


def get_cities(query: str = ""):
    """Автокомпліт міста в checkout. Фаза 0.5: LIKE-пошук по fixture-довіднику."""
    qs = NPCity.objects.filter(is_active=True)
    if query:
        qs = qs.filter(name__icontains=query)
    return qs.order_by("name")[:20]


def get_warehouses(city_id: int, query: str = ""):
    qs = NPWarehouse.objects.filter(city_id=city_id, is_active=True)
    if query:
        qs = qs.filter(number__icontains=query)
    return qs.order_by("number")[:50]


def sync_cities_and_warehouses() -> None:
    """Фаза 1+ (потрібен NP_API_KEY): підвантажити довідник з живого API.

    Поки ключа немає — no-op з логом; fixture (`shipping/fixtures/np_demo.json`)
    вантажиться через `loaddata` при первинному деплої/сіді.
    """
    if not is_live_mode():
        logger.info("NP_API_KEY відсутній — довідник НП лишається на fixture-даних (Фаза 0.5).")
        return
    logger.warning("sync_cities_and_warehouses(): live-режим ще не реалізовано (потрібен ключ клієнта).")


def create_ttn(order) -> str | None:
    """Фаза 3 (після оплати) — створення ТТН. Поки без ключа — повертає None, не крашить checkout."""
    if not is_live_mode():
        logger.info("Створення ТТН для замовлення %s відкладено — немає NP_API_KEY.", order.order_number)
        return None
    logger.warning("create_ttn(): live-режим ще не реалізовано (потрібен ключ клієнта).")
    return None
