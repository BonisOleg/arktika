"""Services — усі мутації кошика/замовлення (ecommerce_business_logic_skill).

SEC-02/06: ціна ніколи не приймається з POST — лише `weight_option.price` з БД
у момент `place_order()`. CartItem не має власного поля ціни.
"""
import logging
import secrets
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from src.catalog.models import Product, ProductWeightOption
from src.content.models import SiteSettings

from .exceptions import EmptyCartError, MinOrderNotReachedError, ProductUnavailableError
from .models import Cart, CartItem, Order, OrderItem, OrderStatusLog, Payment

logger = logging.getLogger("src.commerce")

VAT_RATE = Decimal("0.20")  # інформаційний розріз «в т.ч. ПДВ» — ціни вже включають ПДВ


def get_or_create_cart(session_key: str) -> Cart:
    cart, _ = Cart.objects.get_or_create(session_key=session_key, status="active")
    return cart


def add_to_cart(session_key: str, product_id: int, weight_option_id: int, quantity: Decimal = Decimal("1")) -> Cart:
    weight_option = ProductWeightOption.objects.select_related("product").get(pk=weight_option_id, product_id=product_id)
    if not weight_option.product.is_available:
        raise ProductUnavailableError(weight_option.product.name)

    quantity = weight_option.normalize_quantity(quantity)
    cart = get_or_create_cart(session_key)
    item, created = CartItem.objects.get_or_create(
        cart=cart,
        weight_option=weight_option,
        defaults={"product_id": product_id, "quantity": quantity},
    )
    if not created:
        item.quantity = weight_option.normalize_quantity(item.quantity + quantity)
        item.save(update_fields=["quantity", "updated_at"])
    return cart


def update_cart_item_quantity(session_key: str, item_id: int, quantity: Decimal) -> Cart:
    cart = get_or_create_cart(session_key)
    item = cart.items.filter(pk=item_id).select_related("weight_option").first()
    if not item:
        return cart
    if quantity <= 0:
        item.delete()
    else:
        item.quantity = item.weight_option.normalize_quantity(quantity)
        item.save(update_fields=["quantity", "updated_at"])
    return cart


def remove_cart_item(session_key: str, item_id: int) -> Cart:
    cart = get_or_create_cart(session_key)
    cart.items.filter(pk=item_id).delete()
    return cart


def merge_guest_cart(from_session_key: str, to_session_key: str) -> None:
    """Хук на майбутнє (кабінет покупця, поза MVP) — переносить активний кошик на нову сесію
    (напр. після ре-генерації session_key при логіні, щоб уникнути session fixation)."""
    old_cart = Cart.objects.filter(session_key=from_session_key, status="active").first()
    if not old_cart:
        return
    new_cart = Cart.objects.filter(session_key=to_session_key, status="active").first()
    if not new_cart:
        old_cart.session_key = to_session_key
        old_cart.save(update_fields=["session_key"])
        return
    for item in old_cart.items.all():
        existing = new_cart.items.filter(weight_option=item.weight_option).first()
        if existing:
            existing.quantity = item.weight_option.normalize_quantity(existing.quantity + item.quantity)
            existing.save(update_fields=["quantity"])
        else:
            item.cart = new_cart
            item.save(update_fields=["cart"])
    old_cart.delete()


def _generate_order_number() -> str:
    return f"ARK-{timezone.now():%y%m}-{secrets.randbelow(900000) + 100000}"


@transaction.atomic
def place_order(*, session_key: str, cart: Cart, customer_data: dict) -> Order:
    """Ревалідує ціни/наявність з БД (SEC-02/06), перевіряє мін. суму (SiteSettings),
    робить price-snapshot у OrderItem, створює Payment(pending) і Telegram-сповіщення."""
    items = list(cart.items.select_related("product", "weight_option").all())
    if not items:
        raise EmptyCartError("Кошик порожній")

    subtotal = Decimal("0")
    for item in items:
        item.product.refresh_from_db()
        item.weight_option.refresh_from_db()
        if not item.product.is_available:
            raise ProductUnavailableError(item.product.name)
        subtotal += item.line_total

    min_order = SiteSettings.load().min_order_amount
    if subtotal < min_order:
        raise MinOrderNotReachedError(min_order, subtotal)

    vat_amount = (subtotal * VAT_RATE / (1 + VAT_RATE)).quantize(Decimal("0.01"))

    order = Order.objects.create(
        order_number=_generate_order_number(),
        session_key=session_key,
        status="new",
        payment_status="pending",
        subtotal_amount=subtotal,
        vat_amount=vat_amount,
        total_amount=subtotal,
        **customer_data,
    )

    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=order,
                product=item.product,
                product_name=item.product.name,
                weight_option_label=item.weight_option.label,
                unit=item.weight_option.unit,
                sku=item.weight_option.sku,
                unit_price=item.weight_option.price,
                quantity=item.quantity,
                line_total=item.line_total,
            )
            for item in items
        ]
    )

    OrderStatusLog.objects.create(order=order, status="new", note="Замовлення створено")

    Payment.objects.create(
        order=order,
        order_reference=order.order_number,
        amount=order.total_amount,
    )

    cart.status = "converted"
    cart.save(update_fields=["status", "updated_at"])

    _notify_new_order(order)
    return order


def _notify_new_order(order: Order) -> None:
    try:
        from src.core.services.telegram import notify_new_order

        # items уже в БД після bulk_create; підвантажуємо для тексту сповіщення
        order = Order.objects.prefetch_related("items").get(pk=order.pk)
        notify_new_order(order)
    except Exception:  # noqa: BLE001 — сповіщення не повинне ламати checkout
        logger.exception("Не вдалося надіслати сповіщення про замовлення %s", order.order_number)
