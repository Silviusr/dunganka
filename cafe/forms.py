import re
from datetime import timedelta
from django import forms
from django.utils import timezone


class CheckoutForm(forms.Form):
    name = forms.CharField(
        label="Ваше имя",
        max_length=100,
        widget=forms.TextInput(
            attrs={"autocomplete": "name", "placeholder": "Например, Алина"}
        ),
    )
    phone = forms.CharField(
        label="Телефон в Корее",
        max_length=30,
        widget=forms.TextInput(
            attrs={"type": "tel", "autocomplete": "tel", "placeholder": "010-0000-0000"}
        ),
    )
    instagram = forms.CharField(
        label="Instagram · необязательно",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "@ваш_аккаунт"}),
    )
    postcode = forms.RegexField(
        label="Почтовый индекс",
        regex=r"^\d{5}$",
        error_messages={"invalid": "Укажите индекс из 5 цифр."},
        widget=forms.TextInput(
            attrs={
                "inputmode": "numeric",
                "autocomplete": "postal-code",
                "placeholder": "12345",
            }
        ),
    )
    address = forms.CharField(
        label="Город, улица и дом",
        max_length=300,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "street-address",
                "placeholder": "Улица, дом, город",
            }
        ),
    )
    apartment = forms.CharField(
        label="Номер квартиры / 호수",
        max_length=120,
        error_messages={"required": "Укажите номер квартиры / 호수 для доставки."},
        widget=forms.TextInput(
            attrs={"placeholder": "Например, 101호", "autocomplete": "address-line2"}
        ),
    )
    dispatch_date = forms.DateField(
        label="Желаемая дата отправки", widget=forms.DateInput(attrs={"type": "date"})
    )
    comment = forms.CharField(
        label="Комментарий · необязательно",
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Пожелания к заказу"}),
    )
    token = forms.UUIDField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.localdate()
        self.fields["dispatch_date"].widget.attrs.update(
            min=(today + timedelta(days=1)).isoformat(),
            max=(today + timedelta(days=60)).isoformat(),
        )

    def clean_phone(self):
        value = self.cleaned_data["phone"]
        if (
            not re.fullmatch(r"[+0-9() \-]+", value)
            or not 9 <= len(re.sub(r"\D", "", value)) <= 15
        ):
            raise forms.ValidationError("Введите телефон: от 9 до 15 цифр.")
        return value

    def clean_dispatch_date(self):
        value = self.cleaned_data["dispatch_date"]
        if (
            not timezone.localdate() + timedelta(days=1)
            <= value
            <= timezone.localdate() + timedelta(days=60)
        ):
            raise forms.ValidationError(
                "Выберите дату от завтра до 60 дней вперёд по времени Кореи."
            )
        return value
