"""Nova Poshta: checkout читає локальний довідник; синк — live API при NP_API_KEY."""
import logging

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from .client import iter_pages, parse_ref
from .models import NPCity, NPWarehouse

logger = logging.getLogger("src.shipping")


def is_live_mode() -> bool:
    return bool(settings.NP_API_KEY)


def get_cities(query: str = ""):
    qs = NPCity.objects.filter(is_active=True)
    if query:
        qs = qs.filter(name__icontains=query)
    return qs.order_by("name")[:20]


def get_warehouses(city_id: int, query: str = ""):
    qs = NPWarehouse.objects.filter(city_id=city_id, is_active=True)
    if query:
        qs = qs.filter(Q(number__icontains=query) | Q(description__icontains=query))
    return qs.order_by("number")[:50]


def sync_cities_and_warehouses() -> dict[str, int]:
    """Фаза 1: повний довідник з API. Без ключа — no-op (fixture лишається)."""
    if not is_live_mode():
        logger.info("NP_API_KEY відсутній — довідник НП лишається на fixture-даних (Фаза 0.5).")
        return {"cities": 0, "warehouses": 0}

    now = timezone.now()
    city_count = _sync_cities(now)
    warehouse_count = _sync_warehouses(now)
    logger.info("NP sync done: cities=%s warehouses=%s", city_count, warehouse_count)
    return {"cities": city_count, "warehouses": warehouse_count}


def _sync_cities(now) -> int:
    seen: set = set()
    for row in iter_pages("Address", "getCities"):
        ref = parse_ref(row.get("Ref"))
        if ref is None:
            continue
        seen.add(ref)
        NPCity.objects.update_or_create(
            ref=ref,
            defaults={
                "name": (row.get("Description") or "")[:255],
                "area": (row.get("AreaDescription") or "")[:255],
                "is_active": True,
                "synced_at": now,
            },
        )
    if seen:
        NPCity.objects.exclude(ref__in=seen).update(is_active=False)
    return len(seen)


def _sync_warehouses(now) -> int:
    cities = {city.ref: city for city in NPCity.objects.all()}
    seen: set = set()
    skipped = 0
    for row in iter_pages("Address", "getWarehouses"):
        ref = parse_ref(row.get("Ref"))
        city_ref = parse_ref(row.get("CityRef"))
        city = cities.get(city_ref) if city_ref else None
        if ref is None or city is None:
            skipped += 1
            continue
        seen.add(ref)
        NPWarehouse.objects.update_or_create(
            ref=ref,
            defaults={
                "city": city,
                "number": str(row.get("Number") or "")[:64],
                "description": (row.get("Description") or "")[:255],
                "is_active": True,
                "synced_at": now,
            },
        )
    if seen:
        NPWarehouse.objects.exclude(ref__in=seen).update(is_active=False)
    if skipped:
        logger.warning("NP warehouses skipped (bad ref / unknown city): %s", skipped)
    return len(seen)


def create_ttn(order) -> str | None:
    """Фаза 3 — ТТН. Поки лише каркас, checkout не чіпає."""
    if not is_live_mode():
        logger.info("Створення ТТН для замовлення %s відкладено — немає NP_API_KEY.", order.order_number)
        return None
    logger.warning("create_ttn(): live-режим ще не реалізовано (потрібен ключ клієнта).")
    return None
