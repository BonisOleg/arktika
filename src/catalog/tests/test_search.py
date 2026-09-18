from decimal import Decimal

from django.test import TestCase

from src.catalog.models import Category, Product, ProductWeightOption
from src.catalog.selectors import search_products, suggest_products


def _product(*, name: str, slug: str, sku: str, name_ru: str = "") -> Product:
    category, _ = Category.objects.get_or_create(slug="fish", defaults={"name": "Риба"})
    product = Product.objects.create(
        category=category,
        name=name,
        slug=slug,
        description=f"{name} власного виробництва",
        is_available=True,
    )
    product.name_uk = name
    product.name_ru = name_ru
    product.save()
    ProductWeightOption.objects.create(
        product=product,
        label="1 кг",
        unit="kg",
        price=Decimal("100.00"),
        sku=sku,
        is_default=True,
    )
    return product


class SearchMatchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ikra = _product(name="Ікра мойви", slug="ikra-moyvy", sku="IKRA-1")
        cls.skumbria = _product(name="Скумбрія морожена", slug="skumbria", sku="SKU-MBR")
        cls.forel = _product(name="Юкола форелі", slug="yukola-foreli", sku="FOR-1")

    def test_uk_and_ru_spelling(self):
        self.assertIn(self.ikra, search_products("ікра"))
        self.assertIn(self.ikra, search_products("икра"))
        self.assertIn(self.skumbria, search_products("скумбрія"))
        self.assertIn(self.skumbria, search_products("скумбрия"))

    def test_inflected_stem(self):
        self.assertIn(self.forel, search_products("форель"))
        self.assertIn(self.forel, search_products("форелі"))

    def test_sku(self):
        self.assertIn(self.skumbria, search_products("sku-mbr"))

    def test_suggest_uses_same_match(self):
        names = [p.name for p in suggest_products("икра")]
        self.assertIn("Ікра мойви", names)

    def test_suggest_skips_description_only(self):
        other = _product(name="Оселедець пряного посолу", slug="oseledets", sku="OS-1")
        other.description = "Подавати з ікрою"
        other.description_uk = other.description
        other.save()
        names = [p.name for p in suggest_products("икра")]
        self.assertIn("Ікра мойви", names)
        self.assertNotIn(other.name, names)

    def test_suggest_ranks_name_prefix_first(self):
        salad = _product(name="Салат ікра червона", slug="salat-ikra", sku="SAL-IK")
        ranked = [p.name for p in suggest_products("ікра")]
        self.assertLess(ranked.index(self.ikra.name), ranked.index(salad.name))

    def test_suggest_short_query_is_prefix_only(self):
        herring = _product(name="Оселедець пряного посолу", slug="oseledets", sku="OS-1")
        noise = _product(name="Снеки з лосося", slug="sneky-losos", sku="SN-1")
        names = [p.name for p in suggest_products("ос")]
        self.assertIn(herring.name, names)
        self.assertNotIn(noise.name, names)

    def test_suggest_html_has_photo_and_price(self):
        html = self.client.get("/catalog/search/suggest/", {"q": "ікра"}).content.decode()
        self.assertIn("search-suggest-photo", html)
        self.assertIn("search-suggest-price", html)
        self.assertIn("100", html)
        self.assertIn("search-suggest-item", html)
