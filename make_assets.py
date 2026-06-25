"""Generate site icons and the Open Graph share image.

Build-time tool (needs Pillow, not a runtime dependency). Re-run after changing
the name/tagline or brand colors:

    .venv\\Scripts\\python.exe make_assets.py

Outputs (committed to the repo):
    static/icons/favicon.svg        scalable favicon (modern browsers)
    static/icons/favicon-32.png     32x32 fallback
    static/icons/apple-touch-icon.png  180x180 (iOS home screen)
    static/favicon.ico              multi-size .ico (legacy / implicit request)
    static/og-image.png             1200x630 link-preview image
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Brand palette (matches static/css/style.css).
ACCENT1 = (110, 168, 254)   # #6ea8fe
ACCENT2 = (167, 139, 250)   # #a78bfa
DARK = (11, 14, 20)         # #0b0e14
WHITE = (230, 233, 239)     # #e6e9ef
DIM = (154, 163, 178)       # #9aa3b2

NAME = "Praise Tony-Shokare"
TAGLINE = "Software developer building web apps and games."
DOMAIN = "ot-404.github.io"
MONOGRAM = "PT"

STATIC = Path("static")
ICONS = STATIC / "icons"


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    candidates = (
        [r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf"]
        if bold
        else [r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf"]
    )
    for c in candidates:
        if Path(c).exists():
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


def fit_font(text: str, max_width: int, start: int, minimum: int = 12) -> ImageFont.FreeTypeFont:
    """Largest bold font (<= start) whose text width fits max_width."""
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    size = start
    while size > minimum:
        f = font(size, bold=True)
        if probe.textlength(text, font=f) <= max_width:
            return f
        size -= 2
    return font(minimum, bold=True)


def diagonal_gradient(size: int, c1: tuple, c2: tuple) -> Image.Image:
    """Top-left -> bottom-right linear gradient (RGB)."""
    base = Image.new("RGB", (size, size), c1)
    top = Image.new("RGB", (size, size), c2)
    mask = Image.new("L", (size, size))
    px = mask.load()
    denom = (size - 1) * 2 or 1
    for y in range(size):
        for x in range(size):
            px[x, y] = int(255 * (x + y) / denom)
    base.paste(top, (0, 0), mask)
    return base


def monogram(size: int, rounded: bool = True) -> Image.Image:
    """Gradient square (optionally rounded) with the centered monogram."""
    tile = diagonal_gradient(size, ACCENT1, ACCENT2).convert("RGBA")
    if rounded:
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            [0, 0, size - 1, size - 1], radius=int(size * 0.22), fill=255
        )
        out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        out.paste(tile, (0, 0), mask)
    else:
        out = tile
    d = ImageDraw.Draw(out)
    f = font(int(size * 0.5), bold=True)
    box = d.textbbox((0, 0), MONOGRAM, font=f)
    tw, th = box[2] - box[0], box[3] - box[1]
    d.text(((size - tw) / 2 - box[0], (size - th) / 2 - box[1]), MONOGRAM, font=f, fill=DARK)
    return out


def build_favicons() -> None:
    ICONS.mkdir(parents=True, exist_ok=True)

    # Scalable SVG favicon.
    (ICONS / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">\n'
        '  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">\n'
        f'    <stop offset="0" stop-color="rgb{ACCENT1}"/>'
        f'<stop offset="1" stop-color="rgb{ACCENT2}"/>\n'
        '  </linearGradient></defs>\n'
        '  <rect width="64" height="64" rx="14" fill="url(#g)"/>\n'
        f'  <text x="32" y="45" font-family="Segoe UI, Arial, sans-serif" '
        f'font-size="32" font-weight="700" text-anchor="middle" '
        f'fill="rgb{DARK}">{MONOGRAM}</text>\n'
        "</svg>\n",
        encoding="utf-8",
    )

    monogram(32).save(ICONS / "favicon-32.png")
    monogram(180, rounded=False).convert("RGB").save(ICONS / "apple-touch-icon.png")

    ico = monogram(64)
    ico.save(STATIC / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    print("  icons -> static/icons/ + static/favicon.ico")


def build_og_image() -> None:
    W, H = 1200, 630
    margin = 90
    img = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(img)

    # Accent bar along the bottom.
    bar = diagonal_gradient(W, ACCENT1, ACCENT2).resize((W, 10))
    img.paste(bar, (0, H - 10))

    # Monogram top-left.
    mark = monogram(120)
    img.paste(mark, (margin, margin), mark)

    # Name.
    max_text_width = W - margin * 2
    name_font = fit_font(NAME, max_text_width, start=86)
    d.text((margin, 250), NAME, font=name_font, fill=WHITE)

    # Tagline.
    tag_font = fit_font(TAGLINE, max_text_width, start=40)
    d.text((margin, 250 + name_font.size + 24), TAGLINE, font=tag_font, fill=DIM)

    # Domain.
    dom_font = font(30, bold=True)
    d.text((margin, H - 80), DOMAIN, font=dom_font, fill=ACCENT1)

    img.save(STATIC / "og-image.png")
    print("  og image -> static/og-image.png (1200x630)")


if __name__ == "__main__":
    build_favicons()
    build_og_image()
    print("Done.")
