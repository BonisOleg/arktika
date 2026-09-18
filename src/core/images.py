"""JPEG/PNG/GIF/WebP → WebP ≤500 Кб (ТЗ §2.4, media_library: альфа без flatten)."""
from io import BytesIO
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_IMAGE_BYTES = 500 * 1024
MAX_SIDE = 2048
MIN_SIDE = 400
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
QUALITY_STEPS = (82, 76, 70, 64, 58, 52, 46)


class OptimizeWebpImagesMixin:
    webp_image_fields: tuple[str, ...] = ("image",)

    def save(self, *args, **kwargs):
        names = self.webp_image_fields
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            names = tuple(n for n in names if n in update_fields)
        for name in names:
            apply_webp_if_new(self, name)
        super().save(*args, **kwargs)


def apply_webp_if_new(instance, field_name: str) -> None:
    field = getattr(instance, field_name, None)
    if not field or getattr(field, "_committed", True):
        return
    converted = convert_to_webp(field)
    field.save(converted.name, converted, save=False)


def convert_to_webp(django_file) -> ContentFile:
    name = getattr(django_file, "name", "") or "image"
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError("Дозволені формати: JPEG, PNG, WebP, GIF. SVG не приймається.")

    django_file.seek(0)
    try:
        image = Image.open(django_file)
        image.load()
    except UnidentifiedImageError as exc:
        raise ValidationError("Файл не є зображенням.") from exc

    image = ImageOps.exif_transpose(image)
    if _has_alpha(image):
        image = image.convert("RGBA")
    else:
        image = image.convert("RGB")

    data = _encode_under_limit(image)
    stem = Path(name).stem or "image"
    return ContentFile(data, name=f"{stem}.webp")


def _has_alpha(image: Image.Image) -> bool:
    if image.mode in {"RGBA", "LA"}:
        return True
    return image.mode == "P" and "transparency" in image.info


def _fit_side(image: Image.Image, side: int) -> Image.Image:
    if max(image.size) <= side:
        return image
    fitted = image.copy()
    fitted.thumbnail((side, side), Image.Resampling.LANCZOS)
    return fitted


def _encode_under_limit(image: Image.Image) -> bytes:
    best = b""
    side = min(MAX_SIDE, max(image.size))
    while True:
        current = _fit_side(image, side)
        for quality in QUALITY_STEPS:
            buffer = BytesIO()
            current.save(buffer, format="WEBP", quality=quality, method=4)
            data = buffer.getvalue()
            if not best or len(data) < len(best):
                best = data
            if len(data) <= MAX_IMAGE_BYTES:
                return data
        if side <= MIN_SIDE:
            break
        side = max(MIN_SIDE, int(side * 0.8))
    if not best or len(best) > MAX_IMAGE_BYTES:
        raise ValidationError("Не вдалося стиснути зображення до 500 Кб.")
    return best
