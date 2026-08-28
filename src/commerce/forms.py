import re

from django import forms
from django.conf import settings
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

PHONE_RE = re.compile(r"^\+?3?8?(0\d{9})$")


class CheckoutForm(forms.Form):
    """Checkout (ТЗ §4.2-4.3): дані покупця, доставка НП, GDPR-чекбокс, reCAPTCHA."""

    customer_name = forms.CharField(
        label=_("Ім'я та прізвище"),
        max_length=255,
        widget=forms.TextInput(attrs={"autocomplete": "name", "required": True}),
    )
    customer_phone = forms.CharField(
        label=_("Телефон"),
        max_length=32,
        widget=forms.TextInput(attrs={
            "autocomplete": "tel",
            "inputmode": "tel",
            "required": True,
            "placeholder": "+380XXXXXXXXX",
        }),
    )
    customer_email = forms.EmailField(
        label=_("Email"),
        required=False,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    np_city_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(attrs={"data-np-id": "city"}),
    )
    np_city_name = forms.CharField(
        label=_("Місто (Нова Пошта)"), max_length=255,
        widget=forms.TextInput(attrs={
            "data-np-text": "city", "autocomplete": "off", "required": True,
            "hx-get": reverse_lazy("commerce:np_cities"), "hx-trigger": "keyup changed delay:300ms, focus",
            "hx-target": "next .autocomplete-options", "hx-swap": "innerHTML",
        }),
    )
    np_warehouse_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(attrs={"data-np-id": "warehouse"}),
    )
    np_warehouse_name = forms.CharField(
        label=_("Відділення / поштомат"), max_length=255,
        widget=forms.TextInput(attrs={
            "data-np-text": "warehouse", "autocomplete": "off", "required": True,
            "hx-get": reverse_lazy("commerce:np_warehouses"), "hx-trigger": "keyup changed delay:300ms, focus",
            "hx-target": "next .autocomplete-options", "hx-swap": "innerHTML",
            "hx-include": "[data-np-id='city']",
        }),
    )

    comment = forms.CharField(label=_("Коментар до замовлення"), widget=forms.Textarea, required=False)
    consent_gdpr = forms.BooleanField(
        label=_("Погоджуюсь з умовами оферти та політики конфіденційності"),
        required=True,
        widget=forms.CheckboxInput(attrs={"required": True}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if settings.RECAPTCHA_PUBLIC_KEY and settings.RECAPTCHA_PRIVATE_KEY:
            from django_recaptcha.fields import ReCaptchaField
            from django_recaptcha.widgets import ReCaptchaV2Checkbox

            self.fields["captcha"] = ReCaptchaField(widget=ReCaptchaV2Checkbox, label="")

        # Строгий вибір зі списку НП — лише коли увімкнено NP_REQUIRE_REF_SELECTION.
        if settings.NP_REQUIRE_REF_SELECTION:
            self.fields["np_city_id"].required = True
            self.fields["np_city_id"].widget.attrs["required"] = True

    def clean_customer_phone(self):
        phone = self.cleaned_data["customer_phone"].strip()
        digits = re.sub(r"[^\d+]", "", phone)
        if not PHONE_RE.match(digits):
            raise forms.ValidationError(_("Введіть коректний український номер телефону."))
        return digits

    def clean(self):
        cleaned = super().clean()
        # TODO: після NP_API_KEY увімкнути NP_REQUIRE_REF_SELECTION=True у .env
        if settings.NP_REQUIRE_REF_SELECTION:
            if not cleaned.get("np_city_id"):
                self.add_error("np_city_name", _("Оберіть місто зі списку підказок."))
            if not cleaned.get("np_warehouse_id"):
                self.add_error("np_warehouse_name", _("Оберіть відділення зі списку підказок."))
        return cleaned
