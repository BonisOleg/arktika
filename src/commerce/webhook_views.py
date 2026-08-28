"""WayForPay serviceUrl callback — поза i18n_patterns (server-to-server, без мовного префікса)."""
import json
import logging

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .services_wayforpay import apply_wayforpay_result, get_wayforpay_service

logger = logging.getLogger("src.commerce.webhook")


@csrf_exempt
@require_POST
def wayforpay_webhook(request):
    """SEC-07: підтвердження оплати через серверний webhook з перевіреним підписом."""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return HttpResponse("Bad request", status=400)

    # JSON може віддати int/float — HMAC рахуємо з рядків як у returnUrl form.
    payload = {k: ("" if v is None else str(v)) for k, v in payload.items()}

    service = get_wayforpay_service()
    if service is None:
        logger.warning("WayForPay webhook отримано, але merchant-акаунт не налаштований.")
        return HttpResponse("Merchant not configured", status=503)

    if not service.verify_webhook_signature(payload):
        return HttpResponse("Invalid signature", status=403)

    order_reference = payload.get("orderReference", "")
    try:
        apply_wayforpay_result(payload, source="webhook")
        accept = service.build_accept_response(order_reference)
        return JsonResponse(accept)
    except Exception:  # noqa: BLE001
        logger.exception("WayForPay webhook processing error")
        return HttpResponse("Internal error", status=500)
