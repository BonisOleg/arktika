from django.test import TestCase
from django.urls import reverse


class HeaderSearchLayoutTests(TestCase):
    def test_search_in_header_lang_cart_in_drawer(self):
        html = self.client.get(reverse("core:home")).content.decode()
        self.assertIn('class="header-search"', html)
        self.assertIn("header-search-input", html)
        self.assertIn("header-actions-desktop", html)
        self.assertIn("mobile-nav-tools", html)
        self.assertIn("cart-count-nav", html)
        self.assertNotIn("mobile-search", html)
        self.assertLess(html.find("header-search"), html.find("header-actions"))
        self.assertGreater(html.find("mobile-nav-tools"), html.find("data-mobile-nav"))
