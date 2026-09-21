from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from src.catalog.models import Category, Product, ProductWeightOption
from src.content.models import AboutPage


class AdminEditorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_superuser("admin", "admin@example.com", "pass")
        cls.category = Category.objects.create(name="Копчена", slug="kopchena")
        cls.product = Product.objects.create(
            category=cls.category,
            name="Скумбрія",
            slug="skumbria",
            description="<p>Перший</p><p>Другий</p>",
        )
        ProductWeightOption.objects.create(
            product=cls.product,
            label="1 кг",
            unit="kg",
            price=Decimal("100.00"),
            sku="SKU-ADM-1",
            is_default=True,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_product_form_has_language_tabs_and_tinymce(self):
        url = reverse("admin:catalog_product_change", args=[self.product.pk])
        html = self.client.get(url).content.decode()
        self.assertIn("Українська", html)
        self.assertIn("Русский", html)
        self.assertIn("tab-wrapper", html)
        self.assertIn("tinymce", html.lower())
        self.assertNotIn("tabbed_translation_fields.js", html)

    def test_about_form_has_language_tabs_and_tinymce(self):
        page = AboutPage.load()
        url = reverse("admin:content_aboutpage_change", args=[page.pk])
        html = self.client.get(url).content.decode()
        self.assertIn("Українська", html)
        self.assertIn("Русский", html)
        self.assertIn("tab-wrapper", html)
        self.assertIn("tinymce", html.lower())

    def test_pdp_renders_html_in_div_and_strips_script(self):
        self.product.description = '<p>Смак</p><script>alert(1)</script>'
        self.product.description_uk = self.product.description
        self.product.save()
        html = self.client.get(self.product.get_absolute_url()).content.decode()
        self.assertIn('class="pdp-desc cms-html"', html)
        self.assertIn("<p>Смак</p>", html)
        self.assertNotIn("<script>", html)
        self.assertNotIn("<p class=\"pdp-desc\">", html)
