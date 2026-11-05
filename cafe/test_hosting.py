"""Deployment contracts: fail closed and use the configured persistent database."""

import json
import os
import subprocess
import sys
from pathlib import Path
from django.test import SimpleTestCase, TestCase

ROOT = Path(__file__).resolve().parent.parent


class HostingSettingsTests(SimpleTestCase):
    def load_settings(self, **values):
        env = {
            key: value
            for key, value in os.environ.items()
            if key
            not in [
                "RENDER",
                "RENDER_EXTERNAL_HOSTNAME",
                "DATABASE_URL",
                "DJANGO_DEBUG",
                "DJANGO_SECRET_KEY",
                "DJANGO_TRUST_PROXY",
            ]
        }
        env.update(values)
        script = "import json; from config import settings as s; print(json.dumps({'debug':s.DEBUG,'database':s.DATABASES['default'],'hosts':s.ALLOWED_HOSTS,'origins':s.CSRF_TRUSTED_ORIGINS,'proxy':getattr(s,'SECURE_PROXY_SSL_HEADER',None)}))"
        return subprocess.run(
            [sys.executable, "-c", script],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )

    def test_database_url_selects_postgres_with_tls(self):
        result = self.load_settings(
            DJANGO_DEBUG="0",
            DJANGO_SECRET_KEY="synthetic-test-only-secret",
            DATABASE_URL="postgresql://demo:fictional@db.example.test:5432/dunganka",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        database = json.loads(result.stdout)["database"]
        self.assertEqual(database["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(database["NAME"], "dunganka")
        self.assertEqual(database["OPTIONS"]["sslmode"], "require")

    def test_render_uses_production_settings_and_real_hostname(self):
        result = self.load_settings(
            RENDER="true",
            RENDER_EXTERNAL_HOSTNAME="dunganka-test.onrender.com",
            DJANGO_SECRET_KEY="synthetic-test-only-secret",
            DATABASE_URL="postgresql://demo:fictional@db.example.test:5432/dunganka",
            DJANGO_TRUST_PROXY="1",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        settings = json.loads(result.stdout)
        self.assertFalse(settings["debug"])
        self.assertIn("dunganka-test.onrender.com", settings["hosts"])
        self.assertIn("https://dunganka-test.onrender.com", settings["origins"])
        self.assertEqual(settings["proxy"], ["HTTP_X_FORWARDED_PROTO", "https"])

    def test_render_cannot_silently_use_ephemeral_sqlite(self):
        result = self.load_settings(
            RENDER="true", DJANGO_SECRET_KEY="synthetic-test-only-secret"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DATABASE_URL", result.stderr)

    def test_local_sqlite_and_proxy_defaults_are_preserved(self):
        result = self.load_settings()
        self.assertEqual(result.returncode, 0, result.stderr)
        settings = json.loads(result.stdout)
        self.assertEqual(settings["database"]["ENGINE"], "django.db.backends.sqlite3")
        self.assertIsNone(settings["proxy"])


class HealthTests(TestCase):
    def test_health_endpoint_checks_database(self):
        response = self.client.get("/healthz/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertIn("no-store", response.headers["Cache-Control"])


class StaffBootstrapTests(TestCase):
    def test_bootstrap_creates_staff_once_without_resetting_password(self):
        from django.contrib.auth import get_user_model
        from django.core.management import call_command
        from unittest.mock import patch

        with patch.dict(
            os.environ,
            {
                "DJANGO_SUPERUSER_USERNAME": "owner",
                "DJANGO_SUPERUSER_PASSWORD": "Example-test-only-83$long",
            },
        ):
            call_command("bootstrap_admin", verbosity=0)
        user = get_user_model().objects.get(username="owner")
        self.assertTrue(user.is_staff and user.is_superuser)
        self.assertTrue(user.check_password("Example-test-only-83$long"))
        with patch.dict(
            os.environ,
            {
                "DJANGO_SUPERUSER_USERNAME": "owner",
                "DJANGO_SUPERUSER_PASSWORD": "A-different-test-password-99!",
            },
        ):
            call_command("bootstrap_admin", verbosity=0)
        user.refresh_from_db()
        self.assertTrue(user.check_password("Example-test-only-83$long"))

    def test_bootstrap_missing_credentials_does_not_create_user(self):
        from django.contrib.auth import get_user_model
        from django.core.management import call_command
        from unittest.mock import patch

        with patch.dict(
            os.environ,
            {"DJANGO_SUPERUSER_USERNAME": "", "DJANGO_SUPERUSER_PASSWORD": ""},
        ):
            call_command("bootstrap_admin", verbosity=0)
        self.assertFalse(get_user_model().objects.exists())

    def test_bootstrap_rejects_weak_password(self):
        from django.contrib.auth import get_user_model
        from django.core.management import call_command, CommandError
        from unittest.mock import patch

        with patch.dict(
            os.environ,
            {"DJANGO_SUPERUSER_USERNAME": "owner", "DJANGO_SUPERUSER_PASSWORD": "123"},
        ):
            with self.assertRaises(CommandError):
                call_command("bootstrap_admin", verbosity=0)
        self.assertFalse(get_user_model().objects.exists())


class ProductionCatalogTests(TestCase):
    def test_catalog_renders_with_collected_manifest_assets(self):
        from tempfile import TemporaryDirectory
        from django.core.management import call_command
        from django.contrib.staticfiles.storage import staticfiles_storage
        from django.test import override_settings

        call_command("seed_demo", verbosity=0)
        with (
            TemporaryDirectory() as directory,
            override_settings(DEBUG=False, STATIC_ROOT=directory),
        ):
            call_command("collectstatic", interactive=False, verbosity=0)
            response = self.client.get("/")
            self.assertEqual(response.status_code, 200)
            for image in ["1071", "1698", "1716"]:
                self.assertContains(
                    response, staticfiles_storage.url(f"cafe/dishes/img-{image}.jpg")
                )
