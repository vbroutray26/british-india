"""Gold-set tooling (spec §14.2).

  python -m pipeline.gold sheet --source omalley-puri-1908 --types population,coordinates --out sheet.jpg
      Contact sheet: each extracted figure beside the scan lines it came from, for labelling and review.
  python -m pipeline.gold score --source omalley-puri-1908
      TS-DATA-03: rule extraction vs GS-NUMERIC (exact-match rate per field).

Gold labels live in gold/GS-NUMERIC.jsonl. Labeller and review status are recorded per row
(D-16: drafted by Claude from the page images, reviewed by the owner).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from pipeline import REPO_ROOT
from pipeline.scan import image, leaf_for_page
from pipeline.util import INTERIM_DIR, read_jsonl

GOLD = REPO_ROOT / "gold"


def fact_crop(source_id: str, f: dict, width: int = 1500):
    from PIL import Image

    page = f["notes"].split(";")[0].removeprefix("page ").strip()
    r = leaf_for_page(source_id, page)
    nums = sorted(re.findall(r"\d[\d,]*\d", f["evidence"][0]["quote"]), key=len, reverse=True)
    pats = [re.compile(rf"(?<![\d,]){re.escape(n)}(?![\d,])") for n in nums]  # whole numbers only: "28" ≠ "287"
    idx = next((i for pat in pats for i, ln in enumerate(r["lines"]) if pat.search(ln["t"])), None)
    img = Image.open(image(source_id, r["leaf"]))
    k = img.height / r["size"][1]
    if idx is None:  # quote spans lines: fall back to a band around the first word of the quote
        word = f["evidence"][0]["quote"].split()[0]
        idx = next((i for i, ln in enumerate(r["lines"]) if word in ln["t"]), 0)
    ys = [ln["y"] * k for ln in r["lines"]]
    gap = (ys[-1] - ys[0]) / max(1, len(ys) - 1)
    top, bottom = max(0, int(ys[max(0, idx - 1)] - gap * 0.3)), min(img.height, int(ys[min(len(ys) - 1, idx + 1)] + gap * 1.2))
    c = img.crop((0, top, img.width, bottom))
    c.thumbnail((width, 10_000))
    return c, page


def sheet(source_id: str, types: list[str], out: Path, limit: int = 12) -> list[dict]:
    from PIL import Image, ImageDraw

    facts = [f for f in read_jsonl(INTERIM_DIR / "rules" / source_id / "facts.jsonl") if f["type"] in types][:limit]
    tiles, rows = [], []
    for n, f in enumerate(facts, 1):
        crop, page = fact_crop(source_id, f)
        label = f"#{n} p.{page} {f['type']} → {json.dumps(f['value'])} {f.get('as_of_year', '')}  OCR: “{f['evidence'][0]['quote'][:60]}”"
        tile = Image.new("RGB", (crop.width, crop.height + 34), "white")
        tile.paste(crop, (0, 34))
        ImageDraw.Draw(tile).text((8, 8), label, fill="black")
        tiles.append(tile)
        rows.append({"n": n, "fact_id": f["fact_id"], "page": page, "type": f["type"], "value": f["value"],
                     "year": f.get("as_of_year"), "quote": f["evidence"][0]["quote"]})
    W = max(t.width for t in tiles)
    H = sum(t.height + 8 for t in tiles)
    canvas = Image.new("RGB", (W, H), (200, 200, 200))
    y = 0
    for t in tiles:
        canvas.paste(t, (0, y))
        y += t.height + 8
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, quality=85)
    return rows


def score(source_id: str) -> dict:
    gold = [g for g in read_jsonl(GOLD / "GS-NUMERIC.jsonl") if g["source_id"] == source_id]
    facts = read_jsonl(INTERIM_DIR / "rules" / source_id / "facts.jsonl")
    res = {"labelled": len(gold), "exact": 0, "wrong": [], "missing": []}
    for g in gold:
        # Match on what was printed (page, type, year), not on fact_id: IDs change when OCR is corrected.
        cands = [f for f in facts if f["notes"].startswith(f"page {g['page']};") and f["type"] == g["type"]
                 and f.get("as_of_year") == g.get("year")]
        if any(f["value"] == g["value"] for f in cands):
            res["exact"] += 1
        elif cands:
            res["wrong"].append({"gold_id": g["gold_id"], "extracted": [f["value"] for f in cands], "gold": g["value"],
                                 "note": g.get("notes")})
        else:
            res["missing"].append(g["gold_id"])
    res["exact_rate"] = round(res["exact"] / max(1, res["labelled"]), 3)
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sheet")
    s.add_argument("--source", required=True)
    s.add_argument("--types", required=True)
    s.add_argument("--out", type=Path, required=True)
    s.add_argument("--limit", type=int, default=12)
    c = sub.add_parser("score")
    c.add_argument("--source", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "sheet":
        for r in sheet(a.source, a.types.split(","), a.out, a.limit):
            print(json.dumps(r, ensure_ascii=False))
    else:
        print(json.dumps(score(a.source), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
