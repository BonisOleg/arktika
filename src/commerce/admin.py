from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Order, OrderItem, OrderStatusLog, Payment


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    verbose_name = "Позиція"
    verbose_name_plural = "Склад"
    fields = ("product_name", "weight_option_label", "unit", "sku", "unit_price", "quantity", "line_total")
    readonly_fields = fields
    can_delete = False


class OrderStatusLogInline(TabularInline):
    model = OrderStatusLog
    extra = 0
    verbose_name = "Запис"
    verbose_name_plural = "Історія"
    fields = ("status", "note", "changed_by", "created_at")
    readonly_fields = fields
    can_delete = False


class PaymentInline(TabularInline):
    model = Payment
    extra = 0
    verbose_name = "Платіж"
    verbose_name_plural = "Оплата"
    fields = ("provider", "order_reference", "transaction_status", "signature_verified", "paid_at")
    readonly_fields = fields
    can_delete = False


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = (
        "order_number",
        "customer_name",
        "customer_phone",
        "status",
        "payment_status",
        "total_amount",
        "created_at",
    )
    list_filter = ("status", "payment_status", "created_at")
    list_editable = ()
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    search_fields = ("order_number", "customer_name", "customer_phone", "customer_email")
    readonly_fields = (
        "order_number",
        "session_key",
        "subtotal_amount",
        "vat_amount",
        "total_amount",
        "np_city_ref",
        "np_warehouse_ref",
        "created_at",
        "updated_at",
    )
    inlines = (OrderItemInline, PaymentInline, OrderStatusLogInline)
    fieldsets = (
        ("Замовлення", {"fields": ("order_number", "status", "payment_status", "created_at")}),
        ("Покупець", {"fields": ("customer_name", "customer_phone", "customer_email", "consent_gdpr", "comment")}),
        ("Доставка", {"fields": ("np_city_name", "np_warehouse_name", "np_city_ref", "np_warehouse_ref")}),
        ("Сума", {"fields": ("subtotal_amount", "vat_amount", "total_amount")}),
    )

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            OrderStatusLog.objects.create(
                order=obj,
                status=obj.status,
                changed_by=request.user,
                note="Змінено в адмінці",
            )
        super().save_model(request, obj, form, change)
