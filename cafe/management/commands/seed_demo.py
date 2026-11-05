from django.core.management.base import BaseCommand
from cafe.models import Dish

DEMO_MENU = [
    (
        "lagman",
        "Домашний лагман",
        "Тянутая лапша, говядина, сладкий перец и ароматная подлива.",
        "450 г",
        12000,
        "hot",
    ),
    (
        "manty",
        "Манты на пару",
        "Тонкое тесто ручной лепки, сочная начинка из говядины и лука.",
        "5 шт.",
        10000,
        "dumplings",
    ),
    (
        "ashlyanfu",
        "Ашлянфу",
        "Холодная лапша с овощами, крахмалом и пряной заправкой.",
        "400 г",
        9000,
        "hot",
    ),
    (
        "samsa",
        "Домашняя самса",
        "Румяное тесто и сочная начинка. Хороша к чаю и общему столу.",
        "2 шт.",
        6000,
        "dumplings",
    ),
    (
        "carrot",
        "Морковь по-дунгански",
        "Хрустящая морковь, чеснок и пряности в домашней заправке.",
        "250 г",
        5000,
        "salads",
    ),
    (
        "cucumber",
        "Острые огурцы",
        "Свежие огурцы, зелень, чеснок и лёгкая острая заправка.",
        "250 г",
        5000,
        "salads",
    ),
]


class Command(BaseCommand):
    help = "Create missing demonstration menu items without overwriting staff edits."

    def handle(self, *args, **options):
        for i, (slug, name, description, portion, price, category) in enumerate(
            DEMO_MENU
        ):
            Dish.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "description": description,
                    "portion": portion,
                    "price": price,
                    "category": category,
                    "position": i,
                },
            )
        if options["verbosity"]:
            self.stdout.write(
                self.style.SUCCESS(
                    "Демонстрационное меню готово. Реальные заказы не принимаются."
                )
            )
