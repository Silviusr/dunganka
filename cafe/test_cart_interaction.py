from django.test import TestCase, override_settings

from . import tests as ordering_tests


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class CartInteractionTests(TestCase):
    setUp = ordering_tests.OrderingTests.setUp
    add = ordering_tests.OrderingTests.add
    checkout_data = ordering_tests.OrderingTests.checkout_data

    def test_add_returns_json_without_navigation_or_queued_notice(self):
        response = self.client.post(
            f"/cart/{self.dish.pk}/", {"quantity": 2}, HTTP_ACCEPT="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "ok": True,
                "cart_count": 2,
                "message": "Лагман — добавлено в корзину",
            },
        )
        self.assertEqual(self.client.session["cart"][str(self.dish.pk)], 2)
        self.assertNotContains(self.client.get("/"), "Лагман — добавлено в корзину")

    def test_json_limit_error_keeps_cart_unchanged(self):
        self.add("20")
        response = self.client.post(
            f"/cart/{self.dish.pk}/", {"quantity": 1}, HTTP_ACCEPT="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["cart_count"], 20)
        self.assertFalse(response.json()["ok"])
        self.assertEqual(self.client.session["cart"][str(self.dish.pk)], 20)

    def test_no_javascript_fallback_returns_to_same_category_and_card(self):
        response = self.client.post(f"/cart/{self.dish.pk}/", {"category": "hot"})
        self.assertEqual(response.url, f"/?category=hot#dish-{self.dish.pk}")

    def test_pages_use_order_wording_throughout_checkout(self):
        self.add("1")
        pages = [self.client.get(p) for p in ["/", "/cart/", "/checkout/"]]
        data = self.checkout_data() | {
            "name": "Алина Тестовая",
            "address": "Тестовый адрес",
            "instagram": "test",
        }
        data.pop("demo_consent", None)
        response = self.client.post("/checkout/", data)
        self.assertEqual(response.status_code, 302)
        pages.append(self.client.get(response.url))
        for page in pages:
            text = page.content.decode().lower()
            for word in ["демо", "демонстрац", "учебный проект"]:
                self.assertNotIn(word, text)
