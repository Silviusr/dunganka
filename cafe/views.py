import uuid
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.db import connection, DatabaseError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from .forms import CheckoutForm
from .models import Dish, Order
from .services import cart_rows, place_order


@never_cache
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})


def catalog(request):
    category = request.GET.get("category", "")
    dishes = Dish.objects.all()
    if category in Dish.Category.values:
        dishes = dishes.filter(category=category)
    else:
        category = ""
    return render(
        request,
        "cafe/catalog.html",
        {"dishes": dishes, "categories": Dish.Category.choices, "category": category},
    )


def cart(request):
    basket = request.session.get("cart", {})
    rows = cart_rows(basket)
    if len(rows) != len(basket):
        request.session["cart"] = {str(row["dish"].pk): row["quantity"] for row in rows}
        messages.warning(
            request,
            "Одно из блюд удалено из меню и убрано из корзины. Проверьте состав заявки.",
        )
    return render(
        request,
        "cafe/cart.html",
        {"rows": rows, "food_total": sum(r["subtotal"] for r in rows)},
    )


@require_POST
def cart_add(request, dish_id):
    dish = get_object_or_404(Dish, pk=dish_id, available=True)
    try:
        quantity = int(request.POST.get("quantity", "1"))
        if not 1 <= quantity <= 20:
            raise ValueError
    except (ValueError, TypeError):
        return HttpResponseBadRequest("Количество должно быть от 1 до 20.")
    basket = request.session.get("cart", {}).copy()
    if basket.get(str(dish_id), 0) + quantity > 20:
        messages.error(request, "Не более 20 порций одного блюда.")
    else:
        basket[str(dish_id)] = basket.get(str(dish_id), 0) + quantity
        request.session["cart"] = basket
        messages.success(request, f"{dish.name} — добавлено в корзину")
    return redirect("catalog")


@require_POST
def cart_update(request, dish_id):
    try:
        quantity = int(request.POST.get("quantity", ""))
        if not 0 <= quantity <= 20:
            raise ValueError
    except (ValueError, TypeError):
        return HttpResponseBadRequest("Количество должно быть от 0 до 20.")
    basket = request.session.get("cart", {}).copy()
    if str(dish_id) in basket:
        if quantity:
            basket[str(dish_id)] = quantity
        else:
            basket.pop(str(dish_id))
        request.session["cart"] = basket
    return redirect("cart")


@never_cache
def checkout(request):
    if "checkout_token" not in request.session:
        request.session["checkout_token"] = str(uuid.uuid4())
    token = request.session["checkout_token"]
    if request.method == "POST":
        submitted = request.POST.get("token", "")
        owned = request.session.get("order_ids", [])
        try:
            previous = Order.objects.filter(
                token=uuid.UUID(submitted), pk__in=owned
            ).first()
        except ValueError:
            previous = None
        if previous:
            return redirect("receipt", order_id=previous.pk)
    rows = cart_rows(request.session.get("cart", {}))
    form = CheckoutForm(
        request.POST if request.method == "POST" else None, initial={"token": token}
    )
    if request.method == "POST" and form.is_valid():
        if str(form.cleaned_data["token"]) != token:
            form.add_error(
                None,
                "Сессия оформления изменилась. Обновите страницу и попробуйте ещё раз.",
            )
        else:
            try:
                order = place_order(
                    request.session.get("cart", {}),
                    form.cleaned_data,
                    form.cleaned_data["token"],
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                request.session["order_ids"] = (
                    request.session.get("order_ids", []) + [str(order.pk)]
                )[-50:]
                request.session["cart"] = {}
                request.session["checkout_token"] = str(uuid.uuid4())
                return redirect("receipt", order_id=order.pk)
    return render(
        request,
        "cafe/checkout.html",
        {"form": form, "rows": rows, "food_total": sum(r["subtotal"] for r in rows)},
    )


@never_cache
def receipt(request, order_id):
    if str(order_id) not in request.session.get("order_ids", []):
        raise Http404
    order = get_object_or_404(Order.objects.prefetch_related("lines"), pk=order_id)
    return render(request, "cafe/receipt.html", {"order": order})
