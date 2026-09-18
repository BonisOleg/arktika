from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]


class HttpsScaffoldTests(SimpleTestCase):
    def test_django_never_redirects_http_healthz(self):
        text = (ROOT / "config/settings/production.py").read_text(encoding="utf-8")
        self.assertIn("SECURE_SSL_REDIRECT = False", text)
        self.assertNotIn("SECURE_SSL_REDIRECT = USE_HTTPS", text)
        self.assertIn("USE_X_FORWARDED_HOST = True", text)

    def test_prod_nginx_terminates_tls_to_backend(self):
        text = (ROOT / "deploy/nginx/default.prod.conf.example").read_text(encoding="utf-8")
        self.assertIn("listen 443 ssl", text)
        self.assertIn("ssl_protocols TLSv1.2 TLSv1.3", text)
        self.assertIn("proxy_set_header X-Forwarded-Proto https", text)
        self.assertIn("http://backend:8000", text)
        self.assertIn("alias /app/staticfiles/", text)
        self.assertIn("/.well-known/acme-challenge/", text)

    def test_ssl_compose_is_optional_overlay(self):
        text = (ROOT / "docker-compose.ssl.yml").read_text(encoding="utf-8")
        self.assertIn('"443:443"', text)
        self.assertIn("/etc/letsencrypt:/etc/letsencrypt:ro", text)
        self.assertIn("default.prod.conf", text)
