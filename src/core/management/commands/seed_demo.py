"""Ідемпотентний demo-сід: 8 категорій, товари з фасуваннями (штучні й вагові) та фото
з макету, CMS-singletons, SiteSettings. `update_or_create` — щоб повторний запуск
підправляв дані (unit/ціни/min_quantity), а не лише створював відсутні записи."""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from src.catalog.models import Category, Product, ProductImage, ProductWeightOption
from src.content.models import AboutPage, ContactsPage, DeliveryPage, OfferPage, PrivacyPage, SiteSettings

CATEGORIES = [
    ("Копчена риба", "kopchena"),
    ("В'ялена риба", "vyalena"),
    ("Пресерви", "preservy"),
    ("Солена риба", "solena"),
    ("Салати", "salaty"),
    ("Ікра", "ikra"),
    ("Морожена риба", "morozhena"),
    ("Снеки", "sneky"),
]

# Фото з mockup/assets/products → static/images/products (канон макету).
# options: (label, unit, price, sku, is_default, min_quantity, approx_unit_weight)
#   unit="kg"  → ваговий товар: price = грн/кг, покупець обирає вагу (крок 0.1 кг, мін. min_quantity кг).
#   unit=інше  → штучний товар: price = грн/1 одиницю (шт/пач/уп/ящик), кількість цілими (мін. min_quantity шт).
#   approx_unit_weight — довідкова вага 1 риби/штуки для вагових позицій (порожньо — підказка не показується).
PRODUCTS = [
    {
        "category": "kopchena",
        "name": "Скумбрія холодного копчення",
        "slug": "skumbria-holodnogo-kopchennya",
        "is_hit": True,
        "images": ["skopchena-1.jpg", "product-2.jpg", "product-3.jpg", "product-4.jpg"],
        # Штучний товар — 3 фіксовані пачки, ціна за пачку (не за кг).
        "options": [
            ("300 г", "pack", "189.00", "ARK-SK-300", False, "1", ""),
            ("500 г", "pack", "289.00", "ARK-SK-500", True, "1", ""),
            ("1 кг", "pack", "520.00", "ARK-SK-1000", False, "1", ""),
        ],
    },
    {
        "category": "kopchena",
        "name": "Рексія холодного копчення",
        "slug": "reksiya-holodnogo-kopchennya",
        "is_hit": True,
        "images": ["reksiya.jpg"],
        "options": [("500 г", "pack", "260.00", "ARK-RK-500", True, "1", "")],
    },
    {
        "category": "solena",
        "name": "Оселедець пряного посолу",
        "slug": "oseledets-pryanogo-posolu",
        "is_hit": True,
        "images": ["oseledets.jpg"],
        # Ваговий товар — ціна за 1 кг, вибір ваги з кроком 0.1 кг, мін. замовлення 0.3 кг.
        "options": [("1 кг", "kg", "296.00", "ARK-OS-KG", True, "0.3", "≈ 150–250 г/риба")],
    },
    {
        "category": "ikra",
        "name": "Ікра мойви",
        "slug": "ikra-moyvy",
        "is_new": True,
        "images": ["ikra-moyvy.jpg"],
        # Штучний товар — фіксована банка 250 г, рахуємо в штуках банок.
        "options": [("Банка 250 г", "pcs", "156.00", "ARK-IM-250", True, "1", "")],
    },
    {
        "category": "sneky",
        "name": "Снеки з лосося",
        "slug": "sneky-z-lososya",
        "is_new": True,
        "images": ["snack.jpg"],
        # Штучний товар — кілька пачок різної ваги (клієнтський приклад: 200/500/1000 г).
        "options": [
            ("100 г", "pack", "245.00", "ARK-SN-100", True, "1", ""),
            ("200 г", "pack", "460.00", "ARK-SN-200", False, "1", ""),
            ("500 г", "pack", "1050.00", "ARK-SN-500", False, "1", ""),
            ("1 кг", "pack", "1980.00", "ARK-SN-1000", False, "1", ""),
        ],
    },
    {
        "category": "salaty",
        "name": "Салат далекосхідний",
        "slug": "salat-dalekoshidnyi",
        "is_new": True,
        "images": ["seafood-salad.jpg"],
        "options": [("Контейнер 300 г", "pkg", "210.00", "ARK-SD-300", True, "1", "")],
    },
    {
        "category": "vyalena",
        "name": "Юкола форелі",
        "slug": "yukola-foreli",
        "images": ["product-2.jpg"],
        "options": [("400 г", "pack", "310.00", "ARK-YF-400", True, "1", "")],
    },
    {
        "category": "morozhena",
        "name": "Скумбрія морожена",
        "slug": "skumbria-morozhena",
        "images": ["moroz.jpg"],
        # Мікс: вагова позиція (кг, вибір ваги) + окремий штучний варіант "ящик" (10 кг, оптова ціна).
        "options": [
            ("1 кг", "kg", "165.00", "ARK-SM-KG", True, "0.5", "≈ 250–350 г/риба"),
            ("ящик 10 кг", "box", "1550.00", "ARK-SM-BOX10", False, "1", "≈ 30 риб/ящик"),
        ],
    },
    {
        "category": "preservy",
        "name": "Філе оселедця в маслі",
        "slug": "file-oseledtsya-v-masli",
        "images": ["kilka.jpg"],
        "options": [("Банка 300 г", "pkg", "175.00", "ARK-FO-300", True, "1", "")],
    },
]

DEMO_IMAGES_DIR = Path(settings.BASE_DIR) / "static" / "images" / "products"


class Command(BaseCommand):
    help = "Наповнює демо-даними: категорії, товари (штучні/вагові) з фото макету, CMS-singletons, SiteSettings."

    def _attach_images(self, product: Product, filenames: list[str]) -> None:
        """Ідемпотентно: якщо фото вже є — пропускає; інакше копіює з static/images/products."""
        if product.images.exists():
            return
        for order, filename in enumerate(filenames):
            src = DEMO_IMAGES_DIR / filename
            if not src.is_file():
                self.stderr.write(self.style.WARNING(f"Немає файлу {src}"))
                continue
            image = ProductImage(
                product=product,
                alt=product.name,
                sort_order=order,
                is_primary=(order == 0),
            )
            with src.open("rb") as fh:
                image.image.save(filename, File(fh), save=True)

    @transaction.atomic
    def handle(self, *args, **options):
        categories = {}
        for order, (name, slug) in enumerate(CATEGORIES):
            category, _ = Category.objects.update_or_create(
                slug=slug, defaults={"name": name, "sort_order": order}
            )
            categories[slug] = category

        for item in PRODUCTS:
            product, _ = Product.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "category": categories[item["category"]],
                    "name": item["name"],
                    "description": f'{item["name"]} власного виробництва Arctica.',
                    "is_available": True,
                    "is_hit": item.get("is_hit", False),
                    "is_new": item.get("is_new", False),
                },
            )
            # Спочатку прибираємо варіанти зі старими (перейменованими) лейблами —
            # інакше update_or_create по (product, label) створить дублікат і зіштовхнеться
            # з унікальним sku, який ми повторно використовуємо для нової назви.
            current_labels = [opt[0] for opt in item["options"]]
            product.weight_options.exclude(label__in=current_labels).delete()

            for label, unit, price, sku, is_default, min_quantity, approx_unit_weight in item["options"]:
                ProductWeightOption.objects.update_or_create(
                    product=product,
                    label=label,
                    defaults={
                        "unit": unit,
                        "price": price,
                        "sku": sku,
                        "is_default": is_default,
                        "min_quantity": min_quantity,
                        "approx_unit_weight": approx_unit_weight,
                    },
                )
            self._attach_images(product, item.get("images", []))

        SiteSettings.load()
        AboutPage.load()
        DeliveryPage.load()
        OfferPage.load()
        PrivacyPage.load()
        ContactsPage.load()

        img_count = ProductImage.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Готово: {len(categories)} категорій, {len(PRODUCTS)} товарів, {img_count} фото."
            )
        )
