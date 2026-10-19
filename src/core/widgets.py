from django_recaptcha.widgets import ReCaptchaV2Checkbox


class ReCaptchaV2CheckboxCSP(ReCaptchaV2Checkbox):
    """reCAPTCHA v2 без inline script / data-callback — сумісно з CSP nonce."""

    template_name = "core/widgets/recaptcha_v2_checkbox.html"

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        if "data-callback" not in base_attrs:
            attrs.pop("data-callback", None)
        return attrs
