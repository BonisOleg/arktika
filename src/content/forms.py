from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class ContactForm(forms.Form):
    """Форма `/contacts/` (ТЗ §3) — ім'я/телефон або email, повідомлення, GDPR-чекбокс."""

    name = forms.CharField(label=_("Ім'я"), max_length=255)
    phone = forms.CharField(label=_("Телефон"), max_length=32, required=False)
    email = forms.EmailField(label=_("Email"), required=False)
    message = forms.CharField(label=_("Повідомлення"), widget=forms.Textarea)
    consent_gdpr = forms.BooleanField(label=_("Погоджуюсь на обробку персональних даних"), required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if settings.RECAPTCHA_PUBLIC_KEY and settings.RECAPTCHA_PRIVATE_KEY:
            from django_recaptcha.fields import ReCaptchaField
            from django_recaptcha.widgets import ReCaptchaV2Checkbox

            self.fields["captcha"] = ReCaptchaField(widget=ReCaptchaV2Checkbox, label="")

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("phone") and not cleaned.get("email"):
            raise forms.ValidationError(_("Вкажіть телефон або email для зв'язку."))
        return cleaned
