"""Prepare a private order draft; opening it does not send a message."""

import re
from urllib.parse import urlencode
from django.conf import settings


def order_whatsapp_url(order):
    phone = re.sub(r"[\s()+-]", "", settings.WHATSAPP_ORDER_PHONE)
    if not re.fullmatch(r"[1-9][0-9]{7,14}", phone):
        return ""
    lines = [
        f"ЗАКАЗ № {order.number}",
        f"Имя: {order.name}",
        f"Телефон: {order.phone}",
        f"Instagram: {order.instagram or '—'}",
        f"Статус: {order.get_status_display()}",
        "",
        "СОСТАВ ЗАКАЗА",
    ]
    for item in order.lines.all():
        lines.append(
            f"{item.name} ({item.portion}) — {item.quantity} × {item.unit_price} ₩ = {item.subtotal} ₩"
        )
    lines.extend(
        [
            "",
            f"Стоимость еды: {order.food_total} ₩",
            f"Доставка: {str(order.delivery_fee) + ' ₩' if order.delivery_fee is not None else 'после согласования'}",
            f"Итого: {str(order.total) + ' ₩' if order.total is not None else 'после согласования доставки'}",
            f"Желаемая дата отправки: {order.dispatch_date:%d.%m.%Y}",
            f"Комментарий: {order.comment or '—'}",
            "",
            "АДРЕС ДОСТАВКИ",
            f"Индекс: {order.postcode}",
            f"Город, улица и дом: {order.address}",
            f"Квартира / 호수: {order.apartment}",
        ]
    )
    return f"https://wa.me/{phone}?" + urlencode({"text": "\n".join(lines)})
