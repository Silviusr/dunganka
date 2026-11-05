import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Dish(models.Model):
    class Category(models.TextChoices):
        HOT = "hot", "Горячее"
        DUMPLINGS = "dumplings", "Хлеб и гарниры"
        SALADS = "salads", "Салаты"

    name = models.CharField("Название", max_length=120)
    slug = models.SlugField(unique=True)
    description = models.CharField("Описание", max_length=350)
    portion = models.CharField("Порция", max_length=60)
    price = models.PositiveIntegerField("Цена, ₩", validators=[MinValueValidator(1)])
    category = models.CharField("Категория", max_length=20, choices=Category.choices)
    image = models.CharField("Фото в static", max_length=200, blank=True)
    available = models.BooleanField("В наличии", default=True)
    position = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["position", "pk"]
        verbose_name = "блюдо"
        verbose_name_plural = "меню"

    def __str__(self):
        return self.name


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новый"
        CONFIRMED = "confirmed", "Подтверждён"
        COOKING = "cooking", "Готовится"
        SHIPPED = "shipped", "Отправлен"
        CANCELLED = "cancelled", "Отменён"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.UUIDField(unique=True, editable=False)
    name = models.CharField("Имя", max_length=100)
    phone = models.CharField("Телефон", max_length=30)
    instagram = models.CharField("Instagram", max_length=100, blank=True)
    postcode = models.CharField("Индекс", max_length=5)
    address = models.CharField("Адрес", max_length=300)
    apartment = models.CharField("Квартира / детали", max_length=120, blank=True)
    dispatch_date = models.DateField("Дата отправки")
    comment = models.TextField("Комментарий", max_length=1000, blank=True)
    food_total = models.PositiveIntegerField("Еда, ₩")
    delivery_fee = models.PositiveIntegerField("Доставка, ₩", null=True, blank=True)
    status = models.CharField(
        "Статус", max_length=20, choices=Status.choices, default=Status.NEW
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "заявка"
        verbose_name_plural = "заявки"

    @property
    def number(self):
        return str(self.id).split("-")[0].upper()

    @property
    def total(self):
        return (
            None if self.delivery_fee is None else self.food_total + self.delivery_fee
        )

    def __str__(self):
        return f"Заявка {self.number} · {self.name}"


class OrderLine(models.Model):
    order = models.ForeignKey(Order, related_name="lines", on_delete=models.CASCADE)
    dish = models.ForeignKey(Dish, null=True, on_delete=models.SET_NULL)
    name = models.CharField("Блюдо", max_length=120)
    portion = models.CharField("Порция", max_length=60)
    unit_price = models.PositiveIntegerField("Цена, ₩")
    quantity = models.PositiveSmallIntegerField(
        "Количество", validators=[MinValueValidator(1), MaxValueValidator(20)]
    )

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    class Meta:
        verbose_name = "позиция"
        verbose_name_plural = "состав заказа"
