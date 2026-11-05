from django.core.management.base import BaseCommand

from cafe.menu_data import MENU
from cafe.models import Dish


class Command(BaseCommand):
    help = "Create missing cafe menu items without overwriting staff edits."

    def handle(self, *args, **options):
        for item in MENU:
            fields = item.copy()
            slug = fields.pop("slug")
            Dish.objects.get_or_create(slug=slug, defaults=fields)
        if options["verbosity"]:
            self.stdout.write(
                self.style.SUCCESS(
                    "Меню кафе готово. Демонстрационные заказы не исполняются."
                )
            )
