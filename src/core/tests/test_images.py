from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from src.catalog.models import Category
from src.core.images import MAX_IMAGE_BYTES, convert_to_webp


def _jpeg_bytes(*, size=(80, 50), color=(12, 90, 40)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size, color).save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def _png_alpha_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGBA", (48, 48), (20, 180, 80, 110)).save(buffer, format="PNG")
    return buffer.getvalue()


def _noisy_jpeg_bytes() -> bytes:
    width, height = 2200, 1600
    image = Image.frombytes("RGB", (width, height), bytes((i * 37 + j * 13) % 256 for i in range(height) for j in range(width) for _ in range(3)))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()


class ConvertToWebpTests(TestCase):
    def test_jpeg_becomes_webp(self):
        result = convert_to_webp(SimpleUploadedFile("photo.jpg", _jpeg_bytes()))
        self.assertTrue(result.name.endswith(".webp"))
        self.assertLessEqual(result.size, MAX_IMAGE_BYTES)
        opened = Image.open(result)
        self.assertEqual(opened.format, "WEBP")
        self.assertEqual(opened.mode, "RGB")

    def test_png_keeps_alpha(self):
        result = convert_to_webp(SimpleUploadedFile("logo.png", _png_alpha_bytes()))
        opened = Image.open(result)
        self.assertEqual(opened.mode, "RGBA")
        extrema = opened.getextrema()
        self.assertLess(extrema[3][0], 255)

    def test_rejects_svg(self):
        with self.assertRaises(ValidationError):
            convert_to_webp(SimpleUploadedFile("icon.svg", b"<svg xmlns='http://www.w3.org/2000/svg'></svg>"))

    def test_large_photo_fits_limit(self):
        raw = _noisy_jpeg_bytes()
        self.assertGreater(len(raw), MAX_IMAGE_BYTES)
        result = convert_to_webp(SimpleUploadedFile("huge.jpg", raw))
        self.assertLessEqual(result.size, MAX_IMAGE_BYTES)
        self.assertTrue(result.name.endswith(".webp"))


class CategoryImageSaveTests(TestCase):
    def test_upload_converts_on_save(self):
        category = Category(name="Риба", slug="ryba-webp")
        category.image = SimpleUploadedFile("cat.jpg", _jpeg_bytes(), content_type="image/jpeg")
        category.save()
        category.refresh_from_db()
        self.assertTrue(category.image.name.endswith(".webp"))
        self.assertLessEqual(category.image.size, MAX_IMAGE_BYTES)
