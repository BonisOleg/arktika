from decimal import Decimal

from django.conf import settings
from django.db import models

from src.catalog.models import UNIT_CHOICES, Product, ProductWeightOption
from src.catalog.utils import format_weight
from src.core.models import TimeStampedModel
from src.shipping.models import NPCity, NPWarehouse

CART_STATUS_CHOICES = [
    ("active", "Активний"),
    ("converted", "Перетворено в замовлення"),
    ("abandoned", "Покинутий"),
]

ORDER_STATUS_CHOICES = [
    ("new", "Нове"),
    ("processing", "В обробці"),
    ("shipped", "Відправлено"),
    ("done", "Виконано"),
    ("cancelled", "Скасовано"),
]

PAYMENT_STATUS_CHOICES = [
    ("pending", "Очікує оплати"),
    ("paid", "Оплачено"),
    ("failed", "Помилка оплати"),
]


class Cart(TimeStampedModel):
    session_key = models.CharField("Ключ сесії", max_length=64, null=True, blank=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Користувач", on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField("Статус", max_length=20, choices=CART_STATUS_CHOICES, default="active")

    class Meta:
        verbose_name = "Кошик"
        verbose_name_plural = "Кошики"

    def __str__(self) -> str:
        return f"Кошик #{self.pk} ({self.get_status_display()})"


class CartItem(TimeStampedModel):
    """Без поля ціни (SEC-06) — ціна завжди live з weight_option.price."""

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    weight_option = models.ForeignKey(ProductWeightOption, on_delete=models.CASCADE)
    quantity = models.DecimalField(
        "Кількість", max_digits=8, decimal_places=2, default=Decimal("1"),
        help_text="Для вагових товарів (кг) — дробове значення з кроком 0.1.",
    )

    class Meta:
        verbose_name = "Товар у кошику"
        verbose_name_plural = "Товари у кошику"
        constraints = [
            models.UniqueConstraint(fields=["cart", "weight_option"], name="unique_cart_weight_option"),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} × {self.quantity}"

    @property
    def line_total(self):
        return (self.weight_option.price * self.quantity).quantize(Decimal("0.01"))

    @property
    def quantity_display(self) -> str:
        """«700 г»/«1.5 кг» для вагових; «2 шт»/«3 пач» — для штучних."""
        return self.weight_option.format_quantity(self.quantity)


class Order(TimeStampedModel):
    order_number = models.CharField("Номер", max_length=32, unique=True)
    session_key = models.CharField("Ключ сесії", max_length=64, null=True, blank=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Користувач", on_delete=models.SET_NULL, null=True, blank=True)

    status = models.CharField("Статус", max_length=20, choices=ORDER_STATUS_CHOICES, default="new")
    payment_status = models.CharField("Оплата", max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending")

    customer_name = models.CharField("Покупець", max_length=255)
    customer_phone = models.CharField("Телефон", max_length=32)
    customer_email = models.EmailField("Email", null=True, blank=True)

    np_city_ref = models.ForeignKey(NPCity, verbose_name="Місто НП", on_delete=models.SET_NULL, null=True, blank=True)
    np_warehouse_ref = models.ForeignKey(NPWarehouse, verbose_name="Відділення НП", on_delete=models.SET_NULL, null=True, blank=True)
    np_city_name = models.CharField("Місто", max_length=255, blank=True)
    np_warehouse_name = models.CharField("Відділення", max_length=255, blank=True)

    subtotal_amount = models.DecimalField("Сума товарів", max_digits=10, decimal_places=2)
    vat_amount = models.DecimalField("в т.ч. ПДВ", max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField("До сплати", max_digits=10, decimal_places=2)

    consent_gdpr = models.BooleanField("Згода на обробку ПД", default=False)
    comment = models.TextField("Коментар", blank=True)

    class Meta:
        verbose_name = "Замовлення"
        verbose_name_plural = "Замовлення"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)

    product_name = models.CharField("Назва", max_length=255)
    weight_option_label = models.CharField("Фасування", max_length=50)
    unit = models.CharField("Одиниця", max_length=10, choices=UNIT_CHOICES, default="pcs")
    sku = models.CharField("Артикул", max_length=64)
    unit_price = models.DecimalField("Ціна", max_digits=10, decimal_places=2)
    quantity = models.DecimalField("Кількість", max_digits=8, decimal_places=2)
    line_total = models.DecimalField("Сума", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Позиція"
        verbose_name_plural = "Склад замовлення"

    def __str__(self) -> str:
        return f"{self.product_name} ({self.weight_option_label}) × {self.quantity}"

    @property
    def is_weighted(self) -> bool:
        return self.unit == "kg"

    @property
    def quantity_display(self) -> str:
        if self.is_weighted:
            return format_weight(self.quantity)
        as_int = self.quantity.to_integral_value()
        text = str(as_int) if self.quantity == as_int else str(self.quantity.normalize())
        return f"{text} {self.get_unit_display()}"


class OrderStatusLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_log")
    status = models.CharField("Статус", max_length=40)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    note = models.CharField("Примітка", max_length=255, blank=True)
    created_at = models.DateTimeField("Дата", auto_now_add=True)

    class Meta:
        verbose_name = "Запис статусу"
        verbose_name_plural = "Історія статусів"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.order.order_number}: {self.status}"


class Payment(TimeStampedModel):
    """WayForPay — canonical (27.08.2026). Структура webhook — за паттерном liqpay_skill."""

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    provider = models.CharField("Провайдер", max_length=32, default="wayforpay")
    order_reference = models.CharField("orderReference", max_length=64, unique=True)
    amount = models.DecimalField("Сума", max_digits=10, decimal_places=2)
    currency = models.CharField("Валюта", max_length=8, default="UAH")
    transaction_status = models.CharField("Статус транзакції", max_length=32, null=True, blank=True)
    signature_verified = models.BooleanField("Підпис перевірено", default=False)
    raw_callback = models.JSONField("Callback payload", null=True, blank=True)
    paid_at = models.DateTimeField("Оплачено", null=True, blank=True)

    class Meta:
        verbose_name = "Оплата"
        verbose_name_plural = "Оплати"

    def __str__(self) -> str:
        return f"Payment({self.order_reference})"
