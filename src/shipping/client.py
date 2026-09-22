"""Клієнт Nova Poshta API. Page/Limit — рядки (novaposhta_skill Фаза 1)."""
from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

import requests
from django.conf import settings

logger = logging.getLogger("src.shipping")

NP_API_URL = "https://api.novaposhta.ua/v2.0/json/"
PAGE_LIMIT = 500


class NPAPIError(Exception):
    pass


def parse_ref(value: Any) -> UUID | None:
    try:
        return UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return None


def call(model_name: str, method: str, props: dict[str, str] | None = None) -> list[dict]:
    payload = {
        "apiKey": settings.NP_API_KEY,
        "modelName": model_name,
        "calledMethod": method,
        "methodProperties": props or {},
    }
    response = requests.post(NP_API_URL, json=payload, timeout=60)
    response.raise_for_status()
    body = response.json()
    if not body.get("success"):
        logger.error("NP %s.%s failed: %s", model_name, method, body)
        raise NPAPIError(body.get("errors") or body)
    return body.get("data") or []


def iter_pages(model_name: str, method: str, extra: dict[str, str] | None = None):
    page = 1
    while True:
        props = {"Page": str(page), "Limit": str(PAGE_LIMIT)}
        if extra:
            props.update(extra)
        rows = call(model_name, method, props)
        if not rows:
            break
        yield from rows
        if len(rows) < PAGE_LIMIT:
            break
        page += 1
