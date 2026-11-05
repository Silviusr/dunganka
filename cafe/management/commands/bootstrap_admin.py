import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Create the initial staff account from environment, never reset an existing account."

    @transaction.atomic
    def handle(self, *args, **options):
        username = os.getenv("DJANGO_SUPERUSER_USERNAME", "")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "")
        if not username or not password:
            return
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            return
        try:
            validate_password(password, user=User(username=username))
        except ValidationError as exc:
            raise CommandError(" ".join(exc.messages)) from exc
        User.objects.create_superuser(username=username, password=password)
        if options["verbosity"]:
            self.stdout.write(self.style.SUCCESS("Initial staff account created."))
