"""Vectorise the raster brand logo into themeable SVGs (spec §13.2 Brand).

The owner supplied only a raster (brand_logo_source.webp). This script:
  1. crops the artwork from the paper background,
  2. traces two layers with potrace: INK (dark lettering, train) and ACCENT (gold/tan detail),
  3. writes SVGs whose colours come from CSS (`currentColor` and `--logo-accent`),
     so the logo follows Then/Now and dark mode,
  4. writes web rasters (WebP) of the original artwork for places where full detail matters.

Run from the repo root:
  uv run --with pillow --with numpy python design/tools/logo.py
Requires: potrace (brew install potrace), cwebp.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "design/assets/brand/brand_logo_source.webp"
OUT = ROOT / "design/assets/brand"
WEB = ROOT / "apps/web/public/brand"

PAD = 24
UPSCALE = 2           # trace at 2x for smoother curves
INK_MAX = 95          # luminance <= this is ink
ACCENT_RANGE = (96, 205)
ACCENT_MIN_SAT = 0.10  # gold/tan detail is warmer than the paper


def load_crop() -> Image.Image:
    im = Image.open(SRC).convert("RGB")
    a = np.asarray(im).astype(float)
    ys, xs = np.where(a.mean(2) < 200)
    box = (max(xs.min() - PAD, 0), max(ys.min() - PAD, 0), min(xs.max() + PAD, im.width), min(ys.max() + PAD, im.height))
    return im.crop(box)


def masks(im: Image.Image, scale: float = UPSCALE) -> tuple[np.ndarray, np.ndarray]:
    big = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS).filter(ImageFilter.MedianFilter(3))
    a = np.asarray(big).astype(float) / 255
    lum = a.mean(2) * 255
    mx, mn = a.max(2), a.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    ink = lum <= INK_MAX
    accent = (lum >= ACCENT_RANGE[0]) & (lum <= ACCENT_RANGE[1]) & (sat >= ACCENT_MIN_SAT)
    return ink, accent


def trace(mask: np.ndarray, turdsize: int) -> tuple[str, str]:
    """Return (viewBox, path data) traced by potrace from a boolean mask."""
    with tempfile.TemporaryDirectory() as td:
        pbm, svg = Path(td) / "m.pbm", Path(td) / "m.svg"
        Image.fromarray(np.where(mask, 0, 255).astype("uint8")).convert("1").save(pbm)
        subprocess.run(
            ["potrace", str(pbm), "-s", "-o", str(svg), "--turdsize", str(turdsize),
             "--alphamax", "1.0", "--opttolerance", "0.4", "--unit", "1", "--flat"],
            check=True,
        )
        text = svg.read_text()
    transform = re.search(r'<g transform="([^"]+)"', text).group(1)
    paths = " ".join(re.findall(r' d="([^"]+)"', text))
    return transform, paths


def write_svg(name: str, w: int, h: int, layers: list[tuple[str, str, str]], title: str) -> Path:
    body = "\n".join(
        f'  <g transform="{tf}" fill="{fill}" stroke="none"><path d="{d}"/></g>' for fill, tf, d in layers
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t">\n'
        f"  <title id=\"t\">{title}</title>\n{body}\n</svg>\n"
    )
    path = OUT / name
    path.write_text(svg)
    return path


# Regions in crop coordinates (1x) for favicon candidates: (left, top, right, bottom).
FAVICON_REGIONS = {
    "t-initial": (30, 30, 240, 320),      # ornate T of TOWNS (full stem)
    "train": (35, 735, 345, 925),         # locomotive
}


def svgo(path: Path) -> None:
    subprocess.run(["pnpm", "--dir", str(ROOT / "packages/ui"), "exec", "svgo", "-q", "--multipass", "-p", "1",
                    "-i", str(path), "-o", str(path)], check=True)


def main() -> None:
    im = load_crop()
    # Lite: traced from a 520 px wide copy, ink only, aggressive speckle removal. For header/footer sizes.
    lite_scale = 520 / im.width
    ink_l, _ = masks(im, lite_scale)
    tf_l, d_l = trace(ink_l, turdsize=6)
    lite = write_svg("brand_logo_lite.svg", ink_l.shape[1], ink_l.shape[0], [("currentColor", tf_l, d_l)], "Towns of British India")
    svgo(lite)
    for name, box in FAVICON_REGIONS.items():
        region = im.crop(box)
        side = max(region.size)
        sq = Image.new("RGB", (side, side), region.getpixel((2, 2)))
        sq.paste(region, ((side - region.width) // 2, (side - region.height) // 2))
        ink_f, acc_f = masks(sq, 512 / side)
        tf_f, d_f = trace(ink_f, turdsize=40)
        fav = write_svg(f"brand_favicon_{name}.svg", 512, 512, [("currentColor", tf_f, d_f)], "Towns of British India")
        svgo(fav)
        print(f"{fav.name}: {fav.stat().st_size / 1024:.1f} KB")
    print(f"{lite.name}: {lite.stat().st_size / 1024:.1f} KB")
    ink, accent = masks(im)
    w, h = im.width * UPSCALE, im.height * UPSCALE
    tf_ink, d_ink = trace(ink, turdsize=12)
    tf_acc, d_acc = trace(accent, turdsize=30)
    title = "Towns of British India"
    mono = write_svg("brand_logo_mono.svg", w, h, [("currentColor", tf_ink, d_ink)], title)
    duo = write_svg(
        "brand_logo_duotone.svg", w, h,
        [("var(--logo-accent, currentColor)", tf_acc, d_acc), ("currentColor", tf_ink, d_ink)], title,
    )
    # Raster of the original artwork (full detail) for hero and share cards.
    WEB.mkdir(parents=True, exist_ok=True)
    for width in (480, 960, 1440):
        tmp = OUT / f"_crop_{width}.png"
        r = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        r.save(tmp)
        subprocess.run(["cwebp", "-quiet", "-q", "82", str(tmp), "-o", str(WEB / f"logo-{width}.webp")], check=True)
        tmp.unlink()
    for p in (mono, duo):
        svgo(p)
        print(f"{p.name}: {p.stat().st_size / 1024:.0f} KB")
    for p in sorted(WEB.glob("logo-*.webp")):
        print(f"{p.name}: {p.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
