"""WayForPay — canonical рішення (27.08.2026). Структура сервісу за паттерном `liqpay_skill`
(service class + serviceUrl webhook як primary confirmation + HMAC-підпис + idempotency),
конкретні поля/порядок підпису — з офіційної документації WayForPay (wiki.wayforpay.com),
бо canonical-skill для WayForPay у vault відсутній (розділ 2 плану).

Docs: https://wiki.wayforpay.com/en/view/852102 (Purchase) та /852194 (serviceUrl callback).
"""
import hashlib
import hmac
import logging

from django.conf import settings

logger = logging.getLogger("src.commerce.wayforpay")

WAYFORPAY_CHECKOUT_URL = "https://secure.wayforpay.com/pay"


class WayForPayService:
    def __init__(self, merchant_login: str, secret_key: str, domain: str):
        self.merchant_login = merchant_login
        self.secret_key = secret_key
        self.domain = domain

    def _sign(self, fields: list[str]) -> str:
        query = ";".join(str(f) for f in fields)
        return hmac.new(
            self.secret_key.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.md5,
        ).hexdigest()

    def build_purchase_form(
        self,
        *,
        order_reference: str,
        order_date: int,
        amount: str,
        currency: str,
        product_names: list[str],
        product_counts: list,
        product_prices: list[str],
        service_url: str,
        return_url: str,
    ) -> dict:
        """Дані для форми payment_init (Purchase). Підпис — HMAC_MD5 за wiki.wayforpay.com/view/852102."""
        # Нормалізація: WFP HMAC чутливий до формату; дробовий productCount → 1113.
        amount_s = f"{float(amount):.2f}"
        counts_s = [self._fmt_count(c) for c in product_counts]
        if any("." in c for c in counts_s):
            raise ValueError(
                "WayForPay productCount має бути цілим (дробова вага — через line_total і count=1)."
            )
        prices_s = [f"{float(p):.2f}" for p in product_prices]
        order_date_s = str(int(order_date))

        signature = self._sign(
            [
                self.merchant_login,
                self.domain,
                order_reference,
                order_date_s,
                amount_s,
                currency,
                *product_names,
                *counts_s,
                *prices_s,
            ]
        )
        return {
            "merchantAccount": self.merchant_login,
            "merchantAuthType": "SimpleSignature",
            "merchantDomainName": self.domain,
            "merchantTransactionSecureType": "AUTO",
            "orderReference": order_reference,
            "orderDate": order_date_s,
            "amount": amount_s,
            "currency": currency,
            "productName": product_names,
            "productCount": counts_s,
            "productPrice": prices_s,
            "serviceUrl": service_url,
            "returnUrl": return_url,
            "merchantSignature": signature,
            "checkout_url": WAYFORPAY_CHECKOUT_URL,
        }

    @staticmethod
    def _fmt_count(value) -> str:
        n = float(value)
        if n == int(n):
            return str(int(n))
        return f"{n:.2f}".rstrip("0").rstrip(".")

    def verify_webhook_signature(self, payload: dict) -> bool:
        """serviceUrl callback (SEC-07): merchantAccount;orderReference;amount;currency;
        authCode;cardPan;transactionStatus;reasonCode."""
        expected = self._sign(
            [
                self.merchant_login,
                payload.get("orderReference", ""),
                payload.get("amount", ""),
                payload.get("currency", ""),
                payload.get("authCode", ""),
                payload.get("cardPan", ""),
                payload.get("transactionStatus", ""),
                payload.get("reasonCode", ""),
            ]
        )
        received = payload.get("merchantSignature", "")
        ok = hmac.compare_digest(expected, received)
        if not ok:
            logger.warning("WayForPay: підпис webhook не збігається для orderReference=%s", payload.get("orderReference"))
        return ok

    def build_accept_response(self, order_reference: str, status: str = "accept") -> dict:
        """Відповідь мерчанта на webhook (обов'язково — інакше WFP ретраїть)."""
        import time

        ts = int(time.time())
        signature = self._sign([order_reference, status, ts])
        return {"orderReference": order_reference, "status": status, "time": ts, "signature": signature}


def get_wayforpay_service() -> WayForPayService | None:
    if not settings.WAYFORPAY_MERCHANT_LOGIN or not settings.WAYFORPAY_MERCHANT_SECRET_KEY:
        logger.info("WayForPay merchant-акаунт не налаштований (5.3, docs/Питання_без_відповіді.md) — sandbox-заглушка.")
        return None
    return WayForPayService(
        settings.WAYFORPAY_MERCHANT_LOGIN,
        settings.WAYFORPAY_MERCHANT_SECRET_KEY,
        settings.WAYFORPAY_DOMAIN,
    )


APPROVED_STATUSES = frozenset({"Approved"})
DECLINED_STATUSES = frozenset({"Declined", "Expired", "Refunded", "Voided"})


def apply_wayforpay_result(payload: dict, *, source: str = "webhook") -> bool:
    """Ідемпотентно оновлює Payment/Order зі статусом WayForPay (serviceUrl або returnUrl).

    На localhost serviceUrl від WFP не доходить — тому returnUrl з валідним підписом
    теж застосовує статус (той самий рядок HMAC, що й webhook).
    """
    from django.db import transaction
    from django.utils import timezone

    from .models import OrderStatusLog, Payment

    order_reference = str(payload.get("orderReference") or "")
    transaction_status = str(payload.get("transactionStatus") or "")
    if not order_reference or not transaction_status:
        return False

    try:
        with transaction.atomic():
            payment = (
                Payment.objects.select_for_update()
                .select_related("order")
                .get(order_reference=order_reference)
            )
            if payment.transaction_status == transaction_status and payment.signature_verified:
                return True

            payment.transaction_status = transaction_status
            payment.signature_verified = True
            payment.raw_callback = payload

            order = payment.order
            notify_kind = None
            if transaction_status in APPROVED_STATUSES:
                payment.paid_at = timezone.now()
                order.payment_status = "paid"
                order.status = "processing"
                OrderStatusLog.objects.create(
                    order=order,
                    status="paid",
                    note=f"WayForPay: Approved ({source})",
                )
                notify_kind = "paid"
            elif transaction_status in DECLINED_STATUSES:
                order.payment_status = "failed"
                OrderStatusLog.objects.create(
                    order=order,
                    status="payment_failed",
                    note=f"WayForPay: {transaction_status} ({source})",
                )
                notify_kind = "failed"

            payment.save()
            order.save(update_fields=["payment_status", "status", "updated_at"])

            if notify_kind:
                order_id = order.pk
                approved = notify_kind == "paid"
                wfp_status = transaction_status
                transaction.on_commit(
                    lambda oid=order_id, ok=approved, st=wfp_status: _notify_payment_result(
                        oid, approved=ok, provider_status=st
                    )
                )
        logger.info(
            "WayForPay %s: orderReference=%s status=%s",
            source,
            order_reference,
            transaction_status,
        )
        return True
    except Payment.DoesNotExist:
        logger.warning("WayForPay %s: orderReference=%s не знайдено", source, order_reference)
        return False


def _notify_payment_result(order_id: int, *, approved: bool, provider_status: str) -> None:
    try:
        from src.core.services.telegram import notify_payment_result

        from .models import Order

        order = Order.objects.get(pk=order_id)
        notify_payment_result(order, approved=approved, provider_status=provider_status)
    except Exception:  # noqa: BLE001 — сповіщення не повинне ламати webhook
        logger.exception("Не вдалося надіслати Telegram про оплату замовлення %s", order_id)
