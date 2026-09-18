from django.test import SimpleTestCase

from src.core.admin_url import ADMIN_URL_FALLBACK, resolve_admin_url


class AdminUrlTests(SimpleTestCase):
    def test_fallback_is_not_admin_or_manage(self):
        self.assertNotEqual(ADMIN_URL_FALLBACK.lower(), "admin")
        self.assertNotEqual(ADMIN_URL_FALLBACK.lower(), "manage")

    def test_rejects_default_admin_prefix(self):
        self.assertEqual(resolve_admin_url("admin/"), f"{ADMIN_URL_FALLBACK}/")
        self.assertEqual(resolve_admin_url("admin"), f"{ADMIN_URL_FALLBACK}/")
        self.assertEqual(resolve_admin_url(""), f"{ADMIN_URL_FALLBACK}/")

    def test_keeps_custom_path(self):
        self.assertEqual(resolve_admin_url("kryha-desk/"), "kryha-desk/")
        self.assertEqual(resolve_admin_url("custom-panel"), "custom-panel/")
