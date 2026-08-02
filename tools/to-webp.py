#!/usr/bin/env python3
"""Convert site images to WebP.

Deliberately NOT wired into src/build.py: the SSG is documented as runnable
with nothing but Jinja2 installed, and this needs Pillow. Run it by hand when
you add source art, and commit the .webp output alongside the original.

    python3 tools/to-webp.py src/assets/images/pricing/shirt.png --size 400
    python3 tools/to-webp.py 'src/assets/images/pricing/*.png' --size 400

Alpha is preserved, so the transparent rounded corners on the pricing cut-outs
survive the round trip. Palette ('P') and 'LA' sources are promoted to RGBA
first because Pillow will not write those modes straight to WebP.
"""

from __future__ import annotations  # system python3 here is 3.9

import argparse
import glob
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: python3 -m pip install --user Pillow")


def convert(src: Path, size: int | None, quality: int, lossless: bool,
            outdir: Path | None = None) -> Path:
    im = Image.open(src)
    if im.mode in ("P", "LA"):
        im = im.convert("RGBA")
    if size and max(im.size) > size:
        im = im.resize((size, size) if im.width == im.height
                       else _fit(im.size, size), Image.LANCZOS)
    out = src.with_suffix(".webp")
    if outdir is not None:
        outdir.mkdir(parents=True, exist_ok=True)
        out = outdir / out.name
    im.save(out, "WEBP", quality=quality, method=6, lossless=lossless)
    return out


def _fit(wh: tuple[int, int], size: int) -> tuple[int, int]:
    w, h = wh
    scale = size / max(w, h)
    return max(1, round(w * scale)), max(1, round(h * scale))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+", help="files or globs")
    ap.add_argument("--size", type=int, default=None,
                    help="cap the longest edge at N px (default: keep native)")
    ap.add_argument("--quality", type=int, default=82)
    ap.add_argument("--lossless", action="store_true",
                    help="for flat/vector-like art; measure before assuming it wins")
    ap.add_argument("--outdir", type=Path, default=None,
                    help="write into this directory instead of alongside the source")
    args = ap.parse_args()

    files: list[Path] = []
    for pattern in args.paths:
        files.extend(Path(p) for p in sorted(glob.glob(pattern)))
    if not files:
        sys.exit("no files matched")

    saved = 0
    for src in files:
        before = src.stat().st_size
        out = convert(src, args.size, args.quality, args.lossless, args.outdir)
        after = out.stat().st_size
        saved += before - after
        print(f"{src.name:28} {before // 1024:5} KB -> {out.name:28} {after // 1024:5} KB")
    print(f"\n{len(files)} file(s), {saved // 1024} KB saved")


if __name__ == "__main__":
    main()
