"""Page images for review and gold sets, cached in the private raw repo.

  python -m pipeline.scan --source omalley-puri-1908 --page 61 [--find "49,364"] [--out FILE]

With --find, crops the page to the OCR lines containing the string (±2 lines) using hOCR line positions.
"""
from __future__ import annotations

import argparse
import json
import urllib.parse
from pathlib import Path

from pipeline.util import INTERIM_DIR, MANIFEST_DIR, RAW_DIR, http_get, log

LG = log("scan")


def leaf_for_page(source_id: str, page: str) -> dict:
    for line in (INTERIM_DIR / "ocr" / source_id / "pages.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r["page"] == page:
            return r
    raise KeyError(f"page {page} not in page map")


def _stem(source_id: str) -> tuple[str, str]:
    man = json.loads((MANIFEST_DIR / f"{source_id}.json").read_text())
    return man["identifier"], next(n for n in man["files"] if n.endswith(".pdf")).removesuffix(".pdf")


def image(source_id: str, leaf: int, full: bool = False) -> Path:
    """Page image for a scan leaf.

    Default: rendered from the local PDF (fast, offline; the PDF's images are ~580 px wide, enough to
    confirm a figure). full=True: the original scan (~3500 px, stored at 2400 px) fetched as one member of the host's JP2
    zip and cached as JPEG in the private raw repo; use it for transcription (GS-OCR) and diacritics.
    """
    if full:
        dest = RAW_DIR / source_id / "pages_full" / f"leaf_{leaf:04d}.jpg"
        if dest.exists():
            return dest
        from PIL import Image

        ident, stem = _stem(source_id)
        member = urllib.parse.quote(f"{stem}_jp2/{stem}_{leaf:04d}.jp2", safe="")
        jp2 = dest.with_suffix(".jp2")
        http_get(f"https://archive.org/download/{ident}/{stem}_jp2.zip/{member}", jp2, lg=LG)
        im = Image.open(jp2).convert("L")  # print is monochrome; greyscale halves the size
        im.thumbnail((2400, 4000), Image.LANCZOS)  # 2400 px wide keeps macrons and dots legible
        im.save(dest, quality=78)
        jp2.unlink()
        return dest
    dest = RAW_DIR / source_id / "pages" / f"leaf_{leaf:04d}.jpg"
    if dest.exists():
        return dest
    pdf = next((p for p in (RAW_DIR / source_id).glob("*.pdf") if not p.name.endswith("_text.pdf")), None)
    if pdf:
        import pypdfium2 as pdfium

        doc = pdfium.PdfDocument(str(pdf))
        if len(doc) > leaf:
            dest.parent.mkdir(parents=True, exist_ok=True)
            doc[leaf].render(scale=200 / 72).to_pil().convert("RGB").save(dest, quality=85)
            return dest
    ident, stem = _stem(source_id)
    path = f"{ident}/{stem}_jp2.zip/{stem}_jp2/{stem}_{leaf:04d}.jp2"
    url = f"https://iiif.archive.org/image/iiif/3/{urllib.parse.quote(path, safe='')}/full/max/0/default.jpg"
    http_get(url, dest, lg=LG)  # 'full/max' is reliable; scaled requests time out on the host
    return dest


def crop(source_id: str, page: str, find: str, out: Path, context: int = 2) -> Path:
    from PIL import Image  # optional dependency for review tooling

    r = leaf_for_page(source_id, page)
    img = Image.open(image(source_id, r["leaf"]))
    k = img.height / (r.get("size") or [img.width, img.height])[1]  # OCR → image scale
    ys = [ln["y"] * k for ln in r["lines"]]
    hits = [i for i, ln in enumerate(r["lines"]) if find in ln["t"]]
    if not hits:
        raise ValueError(f"'{find}' not found in OCR lines of page {page}")
    i = hits[0]
    gap = (ys[-1] - ys[0]) / max(1, len(ys) - 1)
    top = max(0, int(ys[max(0, i - context)] - gap * 0.6))
    bottom = min(img.height, int(ys[min(len(ys) - 1, i + context)] + gap * 1.4))
    c = img.crop((0, top, img.width, bottom))
    c.thumbnail((1600, 1600))
    out.parent.mkdir(parents=True, exist_ok=True)
    c.save(out, quality=88)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--page", required=True)
    ap.add_argument("--find")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    if a.find:
        print(crop(a.source, a.page, a.find, a.out or Path(f"crop_p{a.page}.jpg")))
    else:
        print(image(a.source, leaf_for_page(a.source, a.page)["leaf"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
