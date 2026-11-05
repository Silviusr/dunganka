from urllib.parse import parse_qs, urlparse
from django.test import TestCase, override_settings
from . import tests as ordering


class WhatsAppTests(TestCase):
    setUp = ordering.OrderingTests.setUp
    add = ordering.OrderingTests.add
    checkout_data = ordering.OrderingTests.checkout_data

    def test_apartment_required(self):
        self.add()
        response = self.client.post(
            "/checkout/", self.checkout_data() | {"apartment": " "}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("apartment", response.context["form"].errors)

    @override_settings(
        WHATSAPP_ORDER_PHONE="821012345678",
        STORAGES={
            "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
            },
        },
    )
    def test_private_receipt_has_complete_message_with_address_last(self):
        self.add()
        response = self.client.post("/checkout/", self.checkout_data())
        receipt = self.client.get(response.url)
        url = receipt.context["whatsapp_url"]
        self.assertEqual(urlparse(url).netloc, "wa.me")
        self.assertEqual(urlparse(url).path, "/821012345678")
        message = parse_qs(urlparse(url).query)["text"][0]
        for value in ["Лагман", "24000", "010-0000-0000", "demo_example", "450 г"]:
            self.assertIn(value, message)
        self.assertTrue(message.endswith("Квартира / 호수: 101"))
        self.assertGreater(
            message.index("АДРЕС ДОСТАВКИ"), message.index("Комментарий:")
        )
