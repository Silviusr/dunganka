from django.contrib import admin
from .models import Dish, Order, OrderLine


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "portion", "price", "available", "position"]
    list_editable = ["price", "available", "position"]
    list_filter = ["category", "available"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ["name"]}


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    fields = ["name", "portion", "unit_price", "quantity"]
    readonly_fields = fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "number",
        "name",
        "dispatch_date",
        "status",
        "food_total",
        "delivery_fee",
        "created_at",
    ]
    list_filter = ["status", "dispatch_date"]
    search_fields = ["id", "name", "phone", "instagram"]
    date_hierarchy = "dispatch_date"
    fields = [
        "number",
        "created_at",
        "name",
        "phone",
        "instagram",
        "postcode",
        "address",
        "apartment",
        "dispatch_date",
        "comment",
        "food_total",
        "delivery_fee",
        "total",
        "status",
    ]
    readonly_fields = [f for f in fields if f not in ["delivery_fee", "status"]]
    inlines = [OrderLineInline]

    def has_add_permission(self, request):
        return False
