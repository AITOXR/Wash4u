#!/usr/bin/env python3
"""Compose the social share image and the favicon set from owned brand assets.

Run by hand and commit the output; deliberately not wired into src/build.py,
which is documented as runnable with nothing but Jinja2 installed.

    python3 tools/make-share-assets.py

WHY THESE EXIST
  og:image was images/proof/sneaker-nike-after.webp — a tight crop of one
  shoe, carrying a third-party swoosh, with no logo, no context and the wrong
  aspect ratio, used for every share of every page on the site.

  The favicons were the wide WASH4YOU wordmark letterboxed into a square. At
  32px that degrades to an illegible blue/green smear. A favicon has to be a
  MARK, so this crops the drum roundel out of the logo — the one element of
  the lockup that is square by construction and still readable at 16px.
"""

from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMG = ROOT / "src/assets/images"

NAVY = (13, 35, 80)
NAVY_MID = (20, 51, 107)
GREEN = (33, 177, 75)


def _paste_fit(canvas: Image.Image, art: Image.Image, box_w: int, xy: tuple[int, int]) -> None:
    """Scale `art` to box_w and paste it centred on its own alpha."""
    scale = box_w / art.width
    art = art.resize((box_w, max(1, round(art.height * scale))), Image.LANCZOS)
    canvas.paste(art, xy, art)


def share_image() -> None:
    """1200x630 — the size Facebook, WhatsApp, LinkedIn and X all read."""
    W, H = 1200, 630
    c = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(c)

    # brand gradient ground, painted by row so it needs no external art
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(
            round(NAVY_MID[0] + (NAVY[0] - NAVY_MID[0]) * t),
            round(NAVY_MID[1] + (NAVY[1] - NAVY_MID[1]) * t),
            round(NAVY_MID[2] + (NAVY[2] - NAVY_MID[2]) * t)))

    # a row of real garment cut-outs along the base: this is what we clean,
    # and it is the same artwork the site's hero and price rail use
    tiles = ["men-suit-3pcs", "lehenga", "sneakers", "shirt", "curtain", "double-blanket"]
    size, gap = 186, 24
    row_w = len(tiles) * size + (len(tiles) - 1) * gap
    x = (W - row_w) // 2
    for slug in tiles:
        f = IMG / "pricing" / f"{slug}.webp"
        if not f.exists():
            continue
        plate = Image.open(f).convert("RGBA").resize((size, size), Image.LANCZOS)
        # 4% inset crop deletes the baked rounded corners and the transparent
        # pixels behind them — the same trick the service hero uses
        k = round(size * 0.04)
        plate = plate.crop((k, k, size - k, size - k))
        card = Image.new("RGBA", plate.size, (239, 239, 239, 255))
        card.paste(plate, (0, 0), plate)
        rounded = Image.new("L", card.size, 0)
        ImageDraw.Draw(rounded).rounded_rectangle([0, 0, card.size[0] - 1, card.size[1] - 1], 14, fill=255)
        card.putalpha(rounded)
        c.paste(card, (x, H - card.size[1] - 92), card)
        x += card.size[0] + gap

    # logo, top left, at a size that survives a WhatsApp thumbnail
    logo = Image.open(IMG / "logo-white.png").convert("RGBA")
    lw = 460
    _paste_fit(c, logo, lw, ((W - lw) // 2, 96))

    # the green rule the whole site closes its dark bands with
    d.rectangle([0, H - 10, W, H], fill=GREEN)

    out = IMG / "og-share.jpg"
    c.save(out, "JPEG", quality=86, optimize=True)
    print(f"  {out.relative_to(ROOT)}  {W}x{H}  {out.stat().st_size // 1024} KB")


def favicons() -> None:
    """Rebuild the icon set from the drum roundel, not the wordmark.

    The roundel is the washing-drum glyph inside the O of YOU. It is the only
    part of the lockup that is square by construction, so it is the only part
    that survives 32px — the wordmark at that size is an illegible smear.

    Bounds were measured, not guessed: the green swirl's bbox in
    logo-header.png is x 610-659, y 26-76, and the crop is that box padded
    32% to take in the blue ring around it.
    """
    logo = Image.open(IMG / "logo-header.png").convert("RGBA")
    w, h = logo.size
    box = (round(w * 0.7695), round(h * 0.1250), round(w * 0.8540), round(h * 0.5833))
    roundel = logo.crop(box)

    # BRAND BLUE, not navy: the crop carries the logo's own blue ring, so a
    # navy tile would show a visible disc edge. Green on this blue is the
    # highest-contrast pairing the mark offers at icon size.
    BLUE = (32, 96, 160)
    for size in (32, 180, 192, 512):
        pad = round(size * 0.10)
        tile = Image.new("RGBA", (size, size), BLUE + (255,))
        art = roundel.resize((size - pad * 2, size - pad * 2), Image.LANCZOS)
        tile.paste(art, (pad, pad), art)
        # opaque, so Apple touch icons render correctly and no OS picks an
        # arbitrary ground behind a transparent PNG
        out = IMG / f"favicon-{size}.png"
        tile.convert("RGB").save(out, "PNG", optimize=True)
        print(f"  {out.relative_to(ROOT)}  {size}x{size}  {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    print("share image:")
    share_image()
    print("favicons:")
    favicons()
