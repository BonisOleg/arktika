"""Telegram-notifier — тонкий env-gated сервіс (без окремого skill у vault).

Без TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID сервіс лише логує й НЕ ламає checkout/форму
(ТЗ §4.5 — сповіщення протягом 1-2 хв, але відсутність токена не критична помилка).
"""
import html
import logging

import requests
from django.conf import settings

logger = logging.getLogger("src.core.telegram")

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"
REQUEST_TIMEOUT = 5


def _order_notify_enabled() -> bool:
    """SiteSettings.telegram_notify_orders — вимикач без видалення env-токена."""
    from src.content.models import SiteSettings

    enabled = SiteSettings.load().telegram_notify_orders
    if not enabled:
        logger.info("Telegram-сповіщення про замовлення вимкнені (SiteSettings.telegram_notify_orders=False)")
    return enabled


def send_telegram_message(text: str) -> bool:
    """Надсилає text (вже HTML-escaped викликом) у налаштований чат. Повертає True/False."""
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID

    if not token or not chat_id:
        logger.info("Telegram не налаштований (немає токена/chat_id) — повідомлення лише в лог:\n%s", text)
        return False

    try:
        response = requests.post(
            TELEGRAM_API_URL.format(token=token),
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return True
    except requests.RequestException:
        logger.exception("Не вдалося надіслати Telegram-сповіщення")
        return False


def notify_new_order(order) -> None:
    """Сповіщення про нове замовлення: клієнт, доставка, позиції (к-сть/ціна/сума)."""
    if not _order_notify_enabled():
        return

    items = list(order.items.all())
    lines = [
        "🐟 <b>Нове замовлення</b> #%s" % html.escape(order.order_number),
        "Клієнт: %s" % html.escape(order.customer_name),
        "Телефон: %s" % html.escape(order.customer_phone),
        "Доставка: %s, %s"
        % (
            html.escape(order.np_city_name or "—"),
            html.escape(order.np_warehouse_name or "—"),
        ),
        "",
        "<b>Товари:</b>",
    ]
    for item in items:
        name = html.escape(item.product_name)
        pack = html.escape(item.weight_option_label or "")
        qty = html.escape(item.quantity_display)
        price = item.unit_price
        total = item.line_total
        pack_bit = f" ({pack})" if pack else ""
        lines.append(f"• {name}{pack_bit}: {qty} × {price} грн = <b>{total} грн</b>")

    if not items:
        lines.append("• —")

    lines.extend(
        [
            "",
            "<b>Сума: %s грн</b>" % order.total_amount,
        ]
    )
    if order.customer_email:
        lines.append("Email: %s" % html.escape(order.customer_email))
    if order.comment:
        lines.append("Коментар: %s" % html.escape(order.comment))

    send_telegram_message("\n".join(lines))


def notify_payment_result(order, *, approved: bool, provider_status: str = "") -> None:
    """Сповіщення після WayForPay: оплачено або проблема з оплатою."""
    if not _order_notify_enabled():
        return

    title = "✅ <b>Оплата підтверджена</b>" if approved else "❌ <b>Проблема з оплатою</b>"
    lines = [
        f"{title} #{html.escape(order.order_number)}",
        "Клієнт: %s" % html.escape(order.customer_name),
        "Телефон: %s" % html.escape(order.customer_phone),
        "<b>Сума: %s грн</b>" % order.total_amount,
    ]
    if provider_status:
        lines.append("Статус WayForPay: %s" % html.escape(provider_status))
    send_telegram_message("\n".join(lines))


def notify_contact_message(message) -> None:
    lines = [
        "✉️ <b>Нове звернення з /contacts/</b>",
        "Ім'я: %s" % html.escape(message.name),
        "Телефон: %s" % html.escape(message.phone or "—"),
        "Email: %s" % html.escape(message.email or "—"),
        "Повідомлення: %s" % html.escape(message.message),
    ]
    send_telegram_message("\n".join(lines))
