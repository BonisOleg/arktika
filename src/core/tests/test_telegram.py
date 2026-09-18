from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from src.content.models import SiteSettings
from src.core.services.telegram import notify_new_order, notify_payment_result


def _order(**overrides):
    data = {
        "order_number": "ARK-26-100001",
        "customer_name": "Іван",
        "customer_phone": "+380000000000",
        "np_city_name": "Київ",
        "np_warehouse_name": "Відділення 1",
        "items": SimpleNamespace(all=lambda: []),
        "total_amount": Decimal("500.00"),
        "customer_email": "",
        "comment": "",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


class TelegramOrderNotifyTests(TestCase):
    def test_new_order_skipped_when_flag_off(self):
        settings = SiteSettings.load()
        settings.telegram_notify_orders = False
        settings.save(update_fields=["telegram_notify_orders"])

        with patch("src.core.services.telegram.send_telegram_message") as send:
            notify_new_order(_order())
        send.assert_not_called()

    def test_new_order_sent_when_flag_on(self):
        SiteSettings.load()

        with patch("src.core.services.telegram.send_telegram_message") as send:
            notify_new_order(_order())
        send.assert_called_once()
        text = send.call_args[0][0]
        self.assertIn("Нове замовлення", text)
        self.assertIn("ARK-26-100001", text)

    def test_payment_skipped_when_flag_off(self):
        settings = SiteSettings.load()
        settings.telegram_notify_orders = False
        settings.save(update_fields=["telegram_notify_orders"])

        with patch("src.core.services.telegram.send_telegram_message") as send:
            notify_payment_result(_order(), approved=True, provider_status="Approved")
        send.assert_not_called()

    def test_payment_approved_and_failed_texts(self):
        SiteSettings.load()

        with patch("src.core.services.telegram.send_telegram_message") as send:
            notify_payment_result(_order(), approved=True, provider_status="Approved")
            notify_payment_result(_order(), approved=False, provider_status="Declined")

        self.assertEqual(send.call_count, 2)
        self.assertIn("Оплата підтверджена", send.call_args_list[0][0][0])
        self.assertIn("Проблема з оплатою", send.call_args_list[1][0][0])
        self.assertIn("Declined", send.call_args_list[1][0][0])
