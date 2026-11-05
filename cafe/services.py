from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Dish, Order, OrderLine


def cart_rows(cart):
    rows = []
    dishes = {str(d.pk): d for d in Dish.objects.filter(pk__in=cart)}
    for key, quantity in cart.items():
        dish = dishes.get(key)
        if dish:
            rows.append(
                {"dish": dish, "quantity": quantity, "subtotal": dish.price * quantity}
            )
    return rows


@transaction.atomic
def place_order(cart, cleaned_data, token):
    existing = Order.objects.filter(token=token).first()
    if existing:
        return existing
    if not cart:
        raise ValidationError("Ваша корзина пуста.")
    rows = cart_rows(cart)
    if len(rows) != len(cart) or any(not r["dish"].available for r in rows):
        raise ValidationError(
            "Одно из блюд теперь недоступно. Вернитесь в корзину и удалите его."
        )
    if any(
        type(r["quantity"]) is not int or not 1 <= r["quantity"] <= 20 for r in rows
    ):
        raise ValidationError("Количество должно быть от 1 до 20.")
    fields = {
        key: cleaned_data[key]
        for key in [
            "name",
            "phone",
            "instagram",
            "postcode",
            "address",
            "apartment",
            "dispatch_date",
            "comment",
        ]
    }
    order, created = Order.objects.get_or_create(
        token=token, defaults={**fields, "food_total": sum(r["subtotal"] for r in rows)}
    )
    if created:
        OrderLine.objects.bulk_create(
            [
                OrderLine(
                    order=order,
                    dish=r["dish"],
                    name=r["dish"].name,
                    portion=r["dish"].portion,
                    unit_price=r["dish"].price,
                    quantity=r["quantity"],
                )
                for r in rows
            ]
        )
    return order
