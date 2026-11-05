"""Prices and portions transcribed independently from the supplied cafe menu."""

from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings

from .models import Dish


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class CafeMenuTests(TestCase):
    def test_menu_prices_portions_and_only_identified_photos(self):
        call_command("seed_demo", verbosity=0)
        expected = {
            ("Гуйру лагман", "Порция"): 15000,
            ("Босо Цо Мян", "Порция"): 15000,
            ("Джусай лагман", "Порция"): 15000,
            ("Суйру лагман", "Порция"): 15000,
            ("Суйру лагман", "0,7 порции"): 13000,
            ("Ашлянфу", "Порция"): 15000,
            ("Мала лагман", "Порция"): 15000,
            ("Джусай ганфан", "Порция"): 15000,
            ("Гуйру ганфан", "Порция"): 15000,
            ("Фри с мясом", "Порция"): 15000,
            ("Жидкий лагман по-дунгански", "Порция"): 15000,
            ("Жидкий лагман по-дунгански", "0,7 порции"): 13000,
            ("Да Пан Джи", "На 3–4 человека"): 40000,
            ("Да Пан Ню Жу", "На 3–4 человека"): 55000,
            ("Говядина по-дунгански", "Порция"): 18000,
            ("Картофель фри", "Порция"): 5000,
            ("Салат Ачичук", "Порция"): 8000,
            ("Салат Свежий", "Порция"): 8000,
            ("Лепешка", "Целая"): 5000,
            ("Лепешка", "Половина"): 2500,
            ("Пампушка", "1 шт."): 2500,
            ("Рис", "1 порция"): 4000,
        }
        self.assertEqual(
            {(d.name, d.portion): d.price for d in Dish.objects.all()}, expected
        )
        photos = {d.image for d in Dish.objects.all()}
        self.assertEqual(len(photos), 19)
        approved_ids = {
            "1071",
            "1134",
            "1140",
            "1176",
            "1235",
            "1258",
            "1378",
            "1405",
            "1458",
            "1543",
            "1616",
            "1698",
            "1716",
            "1841",
            "1893",
            "1987",
            "2038",
            "2172",
            "2192",
        }
        self.assertEqual({Path(p).stem.split("-")[-1] for p in photos}, approved_ids)
        for photo in photos:
            self.assertTrue(
                (settings.BASE_DIR / "cafe/static" / photo).is_file(), photo
            )
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        for photo in photos:
            self.assertContains(response, "/static/" + photo)
        self.assertNotContains(response, "Все порции и цены — демонстрационные")

    def test_seed_preserves_staff_edits(self):
        call_command("seed_demo", verbosity=0)
        dish = Dish.objects.get(slug="ashlyanfu")
        dish.price = 16000
        dish.save()
        call_command("seed_demo", verbosity=0)
        dish.refresh_from_db()
        self.assertEqual(dish.price, 16000)
