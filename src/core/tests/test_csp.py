import re

from django.test import TestCase, override_settings
from django.urls import reverse

from src.content.forms import ContactForm

GTM_SCRIPT_DOMAINS = (
    "https://www.googletagmanager.com",
    "https://*.googletagmanager.com",
    "https://*.google-analytics.com",
    "https://*.googleadservices.com",
    "https://*.doubleclick.net",
    "https://*.google.com",
    "https://www.gstatic.com",
)

IMG_CONNECT_DOMAINS = (
    "https://www.googletagmanager.com",
    "https://*.googletagmanager.com",
    "https://www.google-analytics.com",
    "https://*.google-analytics.com",
    "https://*.analytics.google.com",
    "https://*.googleadservices.com",
    "https://*.doubleclick.net",
    "https://*.google.com",
)

FRAME_DOMAINS = (
    "https://www.google.com",
    "https://www.googletagmanager.com",
    "https://*.doubleclick.net",
)

RECAPTCHA_TEST_PUBLIC = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
RECAPTCHA_TEST_PRIVATE = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"


def _directive(csp: str, name: str) -> str:
    match = re.search(rf"(?:^|;)\s*{re.escape(name)}\s+([^;]+)", csp)
    assert match, f"CSP missing directive {name}: {csp}"
    return match.group(1)


class CSPAndGTMTests(TestCase):
    def _homepage(self):
        return self.client.get(reverse("core:home"), follow=True)

    def test_homepage_csp_header_and_gtm(self):
        response = self._homepage()
        self.assertEqual(response.status_code, 200)

        csp = response.headers.get("Content-Security-Policy", "")
        self.assertTrue(csp)

        script_src = _directive(csp, "script-src")
        self.assertRegex(script_src, r"'nonce-[^']+'")
        for domain in GTM_SCRIPT_DOMAINS:
            self.assertIn(domain, script_src)
        self.assertNotIn("'unsafe-inline'", script_src)
        self.assertNotIn("'unsafe-eval'", script_src)

        img_src = _directive(csp, "img-src")
        self.assertIn("data:", img_src)
        for domain in IMG_CONNECT_DOMAINS:
            self.assertIn(domain, img_src)

        connect_src = _directive(csp, "connect-src")
        for domain in IMG_CONNECT_DOMAINS:
            self.assertIn(domain, connect_src)

        frame_src = _directive(csp, "frame-src")
        for domain in FRAME_DOMAINS:
            self.assertIn(domain, frame_src)

        html = response.content.decode()
        self.assertIn("GTM-K62J62KG", html)
        self.assertIn("googletagmanager.com/ns.html", html)

        header_nonce = re.search(r"'nonce-([^']+)'", script_src).group(1)
        script_nonce = re.search(
            r'<script[^>]*\snonce=["\']([^"\']+)["\'][^>]*>[\s\S]*?googletagmanager\.com/gtm\.js',
            html,
        )
        self.assertIsNotNone(script_nonce)
        self.assertEqual(script_nonce.group(1), header_nonce)

    @override_settings(GTM_ID="")
    def test_gtm_disabled_when_empty_id(self):
        html = self._homepage().content.decode()
        self.assertNotIn("googletagmanager.com/gtm.js", html)
        self.assertNotIn("googletagmanager.com/ns.html", html)

    @override_settings(
        RECAPTCHA_PUBLIC_KEY=RECAPTCHA_TEST_PUBLIC,
        RECAPTCHA_PRIVATE_KEY=RECAPTCHA_TEST_PRIVATE,
    )
    def test_recaptcha_widget_has_no_inline_script(self):
        html = str(ContactForm()["captcha"])
        self.assertIn("recaptcha/api.js", html)
        self.assertIn("g-recaptcha", html)
        self.assertNotIn("data-callback", html)
        for match in re.finditer(r"<script\b([^>]*)>", html, flags=re.I):
            attrs = match.group(1)
            self.assertIn("src=", attrs)
