from decimal import ROUND_HALF_UP, Decimal

from django.db import models
from django.urls import reverse

from src.core.models import SeoFieldsMixin, TimeStampedModel

from .utils import format_weight

UNIT_CHOICES = [
    ("kg", "кг"),
    ("pcs", "шт"),
    ("pack", "пач"),
    ("pkg", "уп"),
    ("box", "ящик"),
]

# Одиниці, для яких товар вважається "ваговим" — дробова кількість з кроком 0.1 кг
# (клієнт обирає вагу, а не штуки). Усе інше — "штучний" товар (крок 1).
WEIGHT_UNITS = {"kg"}
WEIGHT_STEP = Decimal("0.1")
PIECE_STEP = Decimal("1")


class Category(TimeStampedModel, SeoFieldsMixin):
    """L1-категорія каталогу — адмін-керована (is_active), без підкатегорій у MVP."""

    name = models.CharField("Назва", max_length=255)
    slug = models.SlugField("Слаг", max_length=255, unique=True)
    image = models.ImageField("Зображення", upload_to="categories/", null=True, blank=True)
    sort_order = models.PositiveSmallIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("catalog:category", kwargs={"slug": self.slug})


class Product(TimeStampedModel, SeoFieldsMixin):
    """Товар. Власної ціни/SKU немає — завжди через ProductWeightOption ([[600i3]])."""

    category = models.ForeignKey(Category, verbose_name="Категорія", on_delete=models.PROTECT, related_name="products")
    name = models.CharField("Назва", max_length=255)
    slug = models.SlugField("Слаг", max_length=255, unique=True)
    description = models.TextField("Опис", blank=True)
    is_available = models.BooleanField(
        "В наявності", default=True, help_text="Просте boolean — без точної кількості (клієнт підтвердив 3.3)."
    )
    is_hit = models.BooleanField("Хіт продажу", default=False, help_text="Показ у блоці «Хіти продажу» на головній.")
    is_new = models.BooleanField("Новинка", default=False, help_text="Показ у блоці «Новинки» на головній.")

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товари"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("product:detail", kwargs={"slug": self.slug})

    @property
    def default_option(self):
        return next((o for o in self.weight_options.all() if o.is_default), None) or self.weight_options.first()

    @property
    def min_price(self):
        options = list(self.weight_options.all())
        return min((o.price for o in options), default=None)

    @property
    def is_weighted(self):
        """True, якщо основний варіант — ваговий (кг). Використовується лише для довідки
        в адмінці; реальний UI/крок кількості завжди визначається по `weight_option.unit`,
        бо один товар може мати і ваговий варіант (кг), і штучний (ящик) одночасно."""
        option = self.default_option
        return bool(option and option.unit in WEIGHT_UNITS)


class ProductWeightOption(TimeStampedModel):
    """Варіант фасування — власна ціна+артикул (300г/500г/1кг/ящик), [[600i3]]."""

    product = models.ForeignKey(Product, verbose_name="Товар", on_delete=models.CASCADE, related_name="weight_options")
    label = models.CharField("Фасування", max_length=50, help_text='Напр. «500 г», «1 кг», «ящик 10 кг».')
    unit = models.CharField(
        "Одиниця",
        max_length=10,
        choices=UNIT_CHOICES,
        default="kg",
        help_text=(
            "«кг» — ваговий товар: ціна за 1 кг, покупець обирає вагу з кроком 0.1 кг. "
            "«шт»/«пач»/«уп»/«ящик» — штучний товар: ціна за 1 одиницю, кількість цілими."
        ),
    )
    price = models.DecimalField("Ціна з ПДВ", max_digits=10, decimal_places=2, help_text="Ціна за 1 одиницю з обраного «Одиниця» (за 1 кг, якщо кг; за 1 шт/пач/уп/ящик — якщо штучний).")
    sku = models.CharField("Артикул", max_length=64, unique=True)
    is_default = models.BooleanField("Основний варіант", default=False)
    sort_order = models.PositiveSmallIntegerField("Порядок", default=0)
    min_quantity = models.DecimalField(
        "Мін. кількість замовлення",
        max_digits=6,
        decimal_places=2,
        default=Decimal("1"),
        help_text="Для вагових (кг) — мінімальна вага, напр. 0.3. Для штучних — мінімальна кількість, напр. 1 або 2.",
    )
    approx_unit_weight = models.CharField(
        "Орієнтовна вага 1 од.",
        max_length=100,
        blank=True,
        help_text=(
            "Для вагових товарів (кг) — довідкова вага однієї штуки/риби, напр. «≈ 300–400 г/шт» "
            "або «2–3 шт/кг». Показується на сторінці товару. Порожнє поле — підказка не показується."
        ),
    )

    class Meta:
        verbose_name = "Варіант фасування"
        verbose_name_plural = "Варіанти фасування"
        ordering = ["sort_order", "price"]
        constraints = [
            models.UniqueConstraint(fields=["product", "label"], name="unique_product_label"),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} — {self.label}"

    @property
    def is_weighted(self) -> bool:
        return self.unit in WEIGHT_UNITS

    @property
    def step_quantity(self) -> Decimal:
        return WEIGHT_STEP if self.is_weighted else PIECE_STEP

    def normalize_quantity(self, quantity: Decimal) -> Decimal:
        """Приводить кількість до мін. значення та кроку (0.1 кг для вагових, 1 — для штучних)."""
        quantity = Decimal(quantity)
        step = self.step_quantity
        minimum = self.min_quantity or step
        if quantity < minimum:
            quantity = minimum
        steps = (quantity / step).to_integral_value(rounding=ROUND_HALF_UP)
        normalized = steps * step
        if normalized < minimum:
            normalized = minimum
        return normalized.quantize(Decimal("0.01"))

    def format_quantity(self, quantity: Decimal) -> str:
        """«345/кг» на PDP, «0.7 кг» у кошику; «2 шт»/«3 пач» — для штучних."""
        quantity = Decimal(quantity)
        if self.is_weighted:
            return format_weight(quantity)
        as_int = quantity.to_integral_value()
        text = str(as_int) if quantity == as_int else str(quantity.normalize())
        return f"{text} {self.get_unit_display()}"


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(Product, verbose_name="Товар", on_delete=models.CASCADE, related_name="images")
    image = models.ImageField("Зображення", upload_to="products/")
    alt = models.CharField("Alt-текст", max_length=255, blank=True)
    sort_order = models.PositiveSmallIntegerField("Порядок", default=0)
    is_primary = models.BooleanField("Головне фото", default=False)

    class Meta:
        verbose_name = "Фото товару"
        verbose_name_plural = "Фото товару"
        ordering = ["sort_order"]

    def __str__(self) -> str:
        return f"Фото {self.product.name} #{self.sort_order}"
