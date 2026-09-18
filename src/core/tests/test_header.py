from django.test import TestCase
from django.urls import reverse


class HeaderSearchLayoutTests(TestCase):
    def test_search_in_header_lang_cart_in_drawer(self):
        html = self.client.get(reverse("core:home")).content.decode()
        self.assertIn("header-toolbar", html)
        self.assertIn('class="header-search"', html)
        self.assertIn("header-search-input", html)
        self.assertIn("header-actions-desktop", html)
        self.assertIn("mobile-nav-tools", html)
        self.assertIn("cart-count-nav", html)
        self.assertNotIn("mobile-search", html)
        self.assertLess(html.find("header-search"), html.find("header-actions"))
        self.assertGreater(html.find("mobile-nav-tools"), html.find("data-mobile-nav"))
        self.assertLess(html.find("mobile-nav-tools"), html.find("mobile-nav-categories"))

    def test_hreflang_has_uk_and_ru_without_double_prefix(self):
        html = self.client.get(reverse("core:home")).content.decode()
        self.assertIn('hreflang="uk"', html)
        self.assertIn('hreflang="ru"', html)
        self.assertIn('hreflang="x-default"', html)
        self.assertNotIn("/ru/ru", html)
        ru = self.client.get("/ru/")
        self.assertEqual(ru.status_code, 200)
        ru_html = ru.content.decode()
        self.assertIn("/ru/", ru_html)
        self.assertNotIn("/ru/ru", ru_html)
