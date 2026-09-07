"""Selectors — читання кошика/замовлень. Мутації — лише в services.py."""
from decimal import Decimal

from django.db.models import QuerySet

from .models import Cart, Order
from .utils import vat_from_gross


def get_active_cart(session_key: str) -> Cart | None:
    return (
        Cart.objects.filter(session_key=session_key, status="active")
        .prefetch_related("items__product", "items__weight_option")
        .first()
    )


def get_cart_items_count(session_key: str) -> int:
    """К-сть позицій (рядків) у кошику, а не сума quantity — інакше вагові товари
    (напр. 0.7 кг) робили б бейдж дробовим/незрозумілим при змішаному кошику."""
    cart = get_active_cart(session_key)
    if not cart:
        return 0
    return cart.items.count()


def get_cart_totals(cart: Cart) -> dict:
    items = list(cart.items.select_related("weight_option", "product").all())
    subtotal = sum((item.line_total for item in items), start=Decimal("0"))
    return {
        "items": items,
        "subtotal": subtotal,
        "vat_amount": vat_from_gross(subtotal),
    }


def get_order_for_guest(order_id: int, session_key: str) -> Order | None:
    """SEC-01: гість бачить лише своє замовлення — фільтр по session_key, не по «вгаданому» pk."""
    return Order.objects.filter(pk=order_id, session_key=session_key).prefetch_related("items", "shipment").first()


def get_orders_queryset() -> QuerySet[Order]:
    return Order.objects.select_related("payment", "shipment").prefetch_related("items").all()
