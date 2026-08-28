from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import NPCity, NPWarehouse, Shipment


@admin.register(NPCity)
class NPCityAdmin(ModelAdmin):
    list_display = ("name", "area", "is_active", "synced_at")
    search_fields = ("name", "area")
    list_filter = ("is_active",)
    ordering = ("name",)


@admin.register(NPWarehouse)
class NPWarehouseAdmin(ModelAdmin):
    list_display = ("city", "number", "description", "is_active", "synced_at")
    search_fields = ("number", "description", "city__name")
    list_filter = ("is_active", "city")
    autocomplete_fields = ("city",)
    ordering = ("city__name", "number")


@admin.register(Shipment)
class ShipmentAdmin(ModelAdmin):
    list_display = ("order", "np_warehouse", "shipping_status", "ttn_number", "tracking_updated_at")
    list_filter = ("shipping_status",)
    search_fields = ("order__order_number", "ttn_number")
    autocomplete_fields = ("np_warehouse", "order")
    readonly_fields = ("tracking_updated_at",)
