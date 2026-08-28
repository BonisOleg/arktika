from django.db import models

SHIPPING_STATUS_CHOICES = [
    ("pending", "Очікує"),
    ("created", "ТТН створено"),
    ("in_transit", "В дорозі"),
    ("delivered", "Доставлено"),
]


class NPCity(models.Model):
    """Довідник міст Нової Пошти. `synced_at=None` = fixture-заглушка Фази 0.5 (novaposhta_skill)."""

    ref = models.UUIDField("Ref (Nova Poshta)", unique=True)
    name = models.CharField("Назва", max_length=255)
    area = models.CharField("Область", max_length=255, blank=True)
    is_active = models.BooleanField("Активне", default=True)
    synced_at = models.DateTimeField("Синхронізовано", null=True, blank=True)

    class Meta:
        verbose_name = "Місто"
        verbose_name_plural = "Міста"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class NPWarehouse(models.Model):
    city = models.ForeignKey(NPCity, on_delete=models.CASCADE, related_name="warehouses")
    ref = models.UUIDField("Ref (Nova Poshta)", unique=True)
    number = models.CharField("Номер", max_length=64)
    description = models.CharField("Опис", max_length=255, blank=True)
    is_active = models.BooleanField("Активне", default=True)
    synced_at = models.DateTimeField("Синхронізовано", null=True, blank=True)

    class Meta:
        verbose_name = "Відділення"
        verbose_name_plural = "Відділення"
        ordering = ["number"]

    def __str__(self) -> str:
        return f"{self.city.name} — {self.number}"


class Shipment(models.Model):
    order = models.OneToOneField("commerce.Order", on_delete=models.CASCADE, related_name="shipment")
    np_warehouse = models.ForeignKey(NPWarehouse, on_delete=models.SET_NULL, null=True, blank=True)
    ttn_number = models.CharField("Номер ТТН", max_length=32, null=True, blank=True)
    shipping_status = models.CharField("Статус", max_length=20, choices=SHIPPING_STATUS_CHOICES, default="pending")
    tracking_updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Відправлення"
        verbose_name_plural = "Відправлення"

    def __str__(self) -> str:
        return f"Shipment({self.order.order_number})"
