from datetime import timedelta
from uuid import uuid4
from django.test import Client, TestCase, override_settings
from django.utils import timezone


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class PublicPagesTests(TestCase):
    def test_catalog_is_available(self):
        self.assertContains(self.client.get("/"), "Знакомый вкус.")

    def test_empty_checkout_cannot_be_submitted(self):
        response = self.client.post("/checkout/", {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "корзин")

    def test_receipt_requires_own_session(self):
        self.assertEqual(self.client.get(f"/orders/{uuid4()}/").status_code, 404)

    def test_staff_records_require_login(self):
        response = self.client.get("/admin/cafe/order/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class OrderingTests(TestCase):
    def setUp(self):
        from .models import Dish

        self.dish = Dish.objects.create(
            name="Лагман",
            description="Лапша",
            portion="450 г",
            price=12000,
            category="hot",
            slug="lagman",
        )

    def add(self, quantity="2"):
        return self.client.post(f"/cart/{self.dish.pk}/", {"quantity": quantity})

    def checkout_data(self):
        self.client.get("/checkout/")
        return {
            "name": "Демо покупатель",
            "phone": "010-0000-0000",
            "postcode": "12345",
            "address": "Демонстрационный адрес",
            "apartment": "101",
            "instagram": "demo_example",
            "comment": "",
            "dispatch_date": (timezone.localdate() + timedelta(days=2)).isoformat(),
            "token": self.client.session["checkout_token"],
        }

    def test_server_prices_and_immutable_snapshot(self):
        from .models import Order

        self.add()
        response = self.client.post(
            "/checkout/", self.checkout_data() | {"total": "1", "price": "1"}
        )
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertEqual(order.food_total, 24000)
        self.assertIsNone(order.delivery_fee)
        self.dish.price, self.dish.name = 99999, "Изменено"
        self.dish.save()
        self.assertEqual(order.lines.get().unit_price, 12000)
        self.assertEqual(order.lines.get().name, "Лагман")

    def test_duplicate_submission_creates_one_order(self):
        from .models import Order

        self.add()
        data = self.checkout_data()
        first, second = (
            self.client.post("/checkout/", data),
            self.client.post("/checkout/", data),
        )
        self.assertEqual(first.status_code, 302)
        self.assertEqual(first.url, second.url)
        self.assertEqual(Order.objects.count(), 1)

    def test_receipt_is_private(self):
        self.add()
        response = self.client.post("/checkout/", self.checkout_data())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get(response.url).status_code, 200)
        self.assertEqual(Client().get(response.url).status_code, 404)

    def test_unavailable_dish_prevents_order(self):
        from .models import Order

        self.add()
        data = self.checkout_data()
        self.dish.available = False
        self.dish.save()
        response = self.client.post("/checkout/", data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Order.objects.exists())
        self.assertContains(response, "недоступ")

    def test_invalid_quantities_cannot_enter_cart(self):
        for value in ["-1", "0", "100", "1.5", "bad"]:
            with self.subTest(value=value):
                self.assertEqual(self.add(value).status_code, 400)
        self.assertEqual(self.client.session.get("cart", {}), {})

    def test_dispatch_date_bounds(self):
        from .models import Order

        self.add()
        for days in [-1, 0, 61]:
            data = self.checkout_data() | {
                "dispatch_date": (
                    timezone.localdate() + timedelta(days=days)
                ).isoformat()
            }
            self.assertEqual(self.client.post("/checkout/", data).status_code, 200)
        self.assertFalse(Order.objects.exists())

    def test_invalid_contact_preserves_form_and_cart(self):
        from .models import Order

        self.add()
        response = self.client.post(
            "/checkout/", self.checkout_data() | {"phone": "bad", "postcode": "12"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Демо покупатель")
        self.assertFalse(Order.objects.exists())
        self.assertTrue(self.client.session["cart"])

    def test_csrf_required(self):
        self.assertEqual(
            Client(enforce_csrf_checks=True)
            .post(f"/cart/{self.dish.pk}/", {"quantity": 1})
            .status_code,
            403,
        )

    def test_tampered_checkout_token_rejected(self):
        from .models import Order

        self.add()
        response = self.client.post(
            "/checkout/", self.checkout_data() | {"token": str(uuid4())}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Order.objects.exists())


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class ManagementTests(TestCase):
    setUp = OrderingTests.setUp
    add = OrderingTests.add
    checkout_data = OrderingTests.checkout_data

    def test_seed_is_idempotent(self):
        from django.core.management import call_command
        from .models import Dish

        call_command("seed_demo", verbosity=0)
        count = Dish.objects.count()
        call_command("seed_demo", verbosity=0)
        self.assertEqual(Dish.objects.count(), count)
        self.assertGreaterEqual(count, 6)

    def test_category_filter(self):
        from .models import Dish

        Dish.objects.create(
            name="Манты",
            slug="manty",
            portion="5 шт",
            price=10000,
            category="dumplings",
        )
        response = self.client.get("/?category=dumplings")
        self.assertContains(response, "Манты")
        self.assertNotContains(response, "Лагман")

    def test_update_then_remove_cart_item(self):
        self.add()
        self.client.post(f"/cart/{self.dish.pk}/update/", {"quantity": "3"})
        self.assertEqual(self.client.session["cart"][str(self.dish.pk)], 3)
        self.client.post(f"/cart/{self.dish.pk}/update/", {"quantity": "0"})
        self.assertEqual(self.client.session["cart"], {})

    def test_staff_can_manage_delivery_without_editing_snapshot(self):
        from django.contrib.auth import get_user_model
        from .models import Order

        self.add()
        self.client.post("/checkout/", self.checkout_data())
        order = Order.objects.get()
        staff = get_user_model().objects.create_superuser(
            username="owner", password="test-password-only"
        )
        self.client.force_login(staff)
        response = self.client.get(f"/admin/cafe/order/{order.pk}/change/")
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            f"/admin/cafe/order/{order.pk}/change/",
            {
                "delivery_fee": 4000,
                "status": "confirmed",
                "_save": "Save",
                "lines-TOTAL_FORMS": "1",
                "lines-INITIAL_FORMS": "1",
                "lines-MIN_NUM_FORMS": "0",
                "lines-MAX_NUM_FORMS": "1000",
                "lines-0-id": str(order.lines.get().pk),
                "lines-0-order": str(order.pk),
            },
        )
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.total, 28000)
        self.assertEqual(order.status, "confirmed")
        self.assertEqual(order.lines.get().unit_price, 12000)

    def test_deleted_dish_can_be_cleared_from_cart_and_checkout_recovers(self):
        from .models import Dish, Order

        self.add()
        self.dish.delete()
        replacement = Dish.objects.create(
            name="Второе блюдо",
            slug="replacement",
            portion="1 шт.",
            price=6000,
            category="hot",
        )
        self.client.post(f"/cart/{replacement.pk}/", {"quantity": "1"})
        response = self.client.get("/cart/")
        self.assertContains(response, "удалено из меню")
        self.assertEqual(self.client.session["cart"], {str(replacement.pk): 1})
        response = self.client.post("/checkout/", self.checkout_data())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.get().food_total, 6000)
