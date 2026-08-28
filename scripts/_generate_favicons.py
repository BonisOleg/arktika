"""Генерує фавікони з оптового favicon (rk-arctica.com.ua) або локальної копії.

Джерело: static/favicon/_source-wholesale.ico
(скопійовано з https://rk-arctica.com.ua/favicon.ico).

Риба широка (≈175×70) — у квадрат вписуємо з малим відступом;
для 16/32 трохи збільшуємо (легкий crop по боках), щоб у табі була читабельнішою.
apple-touch-icon — на navy (iOS ігнорує альфу).
"""
from pathlib import Path
import shutil

from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
OUT = BASE_DIR / "static" / "favicon"
SRC = OUT / "_source-wholesale.ico"
FALLBACK = BASE_DIR / "static" / "images" / "logo-fish.png"
OUT.mkdir(parents=True, exist_ok=True)

TRANSPARENT = (0, 0, 0, 0)
APPLE_BG = (16, 40, 72, 255)  # --color-navy #102848


def scale_to_fit(src: Image.Image, box: tuple[int, int]) -> Image.Image:
    bw, bh = box
    ratio = min(bw / src.width, bh / src.height)
    nw = max(1, int(round(src.width * ratio)))
    nh = max(1, int(round(src.height * ratio)))
    return src.resize((nw, nh), Image.Resampling.LANCZOS)


def fit_contain(src: Image.Image, size: int, bg, margin_ratio: float = 0.06) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), bg)
    margin = max(1, int(size * margin_ratio))
    inner = size - margin * 2
    fish = scale_to_fit(src, (inner, inner))
    x = (size - fish.width) // 2
    y = (size - fish.height) // 2
    canvas.paste(fish, (x, y), fish)
    return canvas


def fit_cover_wide(src: Image.Image, size: int, bg, width_ratio: float = 1.15) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), bg)
    target_w = max(size, int(size * width_ratio))
    ratio = target_w / src.width
    fish = src.resize(
        (target_w, max(1, int(round(src.height * ratio)))),
        Image.Resampling.LANCZOS,
    )
    x = (size - fish.width) // 2
    y = (size - fish.height) // 2
    canvas.paste(fish, (x, y), fish)
    return canvas


def main() -> None:
    src_path = SRC if SRC.exists() else FALLBACK
    source = Image.open(src_path).convert("RGBA")
    bbox = source.getbbox()
    if bbox:
        source = source.crop(bbox)

    for name, size, kind in [
        ("favicon-16x16.png", 16, "cover"),
        ("favicon-32x32.png", 32, "cover"),
        ("android-chrome-192x192.png", 192, "contain"),
        ("android-chrome-512x512.png", 512, "contain"),
    ]:
        img = (
            fit_cover_wide(source, size, TRANSPARENT)
            if kind == "cover"
            else fit_contain(source, size, TRANSPARENT, margin_ratio=0.06)
        )
        img.save(OUT / name, optimize=True)
        print("saved", name, img.size)

    apple = fit_contain(source, 180, APPLE_BG, margin_ratio=0.08)
    apple.convert("RGB").save(OUT / "apple-touch-icon.png", optimize=True)
    print("saved apple-touch-icon.png 180 navy")

    if SRC.exists():
        shutil.copyfile(SRC, OUT / "favicon.ico")
        print("copied wholesale favicon.ico")
    else:
        ico_sizes = [16, 32, 48]
        ico_images = [fit_contain(source, s, TRANSPARENT, margin_ratio=0.04) for s in ico_sizes]
        ico_images[0].save(
            OUT / "favicon.ico",
            format="ICO",
            sizes=[(s, s) for s in ico_sizes],
            append_images=ico_images[1:],
        )
        print("saved favicon.ico", ico_sizes)


if __name__ == "__main__":
    main()
