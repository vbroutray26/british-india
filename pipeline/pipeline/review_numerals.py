"""Numeral review queue (D-36): the owner checks every OCR line whose figures are in doubt against the scan.

TS-DATA-01 sets numeral CER <= 0.5% *after review*. The queue is chosen by rules that apply to the
whole book, never by the gold pages, so GS-OCR still measures the process. A line with a figure is
queued when

  one engine only      - it was recovered from the second read (D-27, D-32, D-34), so nothing checked it;
  index                - it is on a two-column (index) page, where both engines misread page numbers alike;
  engines differ       - the second read's matching line has other figures;
  no second-read line  - the second read has no matching line;
  no second read       - the page has no second read at all;
  suspect characters   - letters or punctuation inside figures that are typical misreadings ("Ist", "5:2");
  footnote / margin note - footnotes and side-notes, which the merge does not touch.

Lines that already carry an audited correction are left out; they are reviewed in ocr_corrections.yaml.

build  writes data/interim/review/<source>/ (gitignored: crops of the scans stay out of the public repo):
       index.html with the scans' crops, one item at a time. The owner types what is printed (an empty
       field deletes OCR junk) and exports numeral_answers.json.
import turns the answers into audited corrections in data/review/<source>/ocr_corrections.yaml (by the
       reviewer, review: done; DP-01 applies them to lines, side-notes and footnotes) and logs every
       answer in data/review/<source>/numeral_review.jsonl. Rerun DP-01 afterwards.

Usage: python -m pipeline.review_numerals build --source omalley-puri-1908
       python -m pipeline.review_numerals import --source omalley-puri-1908 --answers numeral_answers.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import itertools
import json
import re
import shutil
import statistics
from pathlib import Path

from pipeline.second_read import _align, _fold, body_rows, column_rows
from pipeline.util import CONFIG_DIR, DATA_DIR, INTERIM_DIR, RAW_DIR, read_jsonl, read_yaml, write_jsonl

DIGIT = re.compile(r"\d")
FIGURES = re.compile(r"[\d½¼¾⅓⅔·]+")
# Misreadings seen on GS-OCR: I/l for 1, O/o for 0, a colon or semicolon for the raised decimal point.
SUSPECT = re.compile(r"\d[:;]\d|\b[Il]\d|\d[Il]\b|\b[Il](?:st|nd|th)\b|\d[Oo]\b|\b[Oo]\d")
PAGE_DIR = Path(__file__).parent / "review_page"
CROP_WIDTH = 1400


def _figures(t: str) -> list[str]:
    return FIGURES.findall(t)


def _id(page: str, kind: str, find: str, y) -> str:
    return hashlib.sha1(f"{page}|{kind}|{find}|{y}".encode()).hexdigest()[:12]


def _item(rec: dict, kind: str, text: str, find: str, y, reasons: list[str], col: int = 0) -> dict:
    return {"id": _id(rec["page"], kind, find, y), "page": rec["page"], "leaf": rec["leaf"], "kind": kind,
            "text": text, "find": find, "y": y, "col": col, "reasons": reasons}


def page_items(rec: dict, rows: list[str] | tuple[list[str], list[str]] | None, index: bool = False) -> list[dict]:
    """Queue items for one page. rows: the second read's lines in reading order, or (left, right) columns
    for a two-column page, or None when the page has no second read. index: the page is in the source's
    index (config/segment.yaml); a page DP-01 split into columns counts as index too."""
    lines = rec["lines"]
    index = index or any(ln.get("col") for ln in lines)
    reasons: dict[int, list[str]] = {i: [] for i, ln in enumerate(lines) if DIGIT.search(ln["t"])}
    for i, why in reasons.items():
        if lines[i].get("recovered"):
            why.append("one engine only")
        if index:
            why.append("index")
    if not index:
        if rows is None:
            for i, why in reasons.items():
                if not lines[i].get("recovered"):
                    why.append("no second read")
        else:
            assert isinstance(rows, list)
            pairs = dict(_align([_fold(ln["t"]) for ln in lines], [_fold(r) for r in rows], 60)) if rows else {}
            for i, why in reasons.items():
                if lines[i].get("recovered"):
                    continue
                if i not in pairs:
                    why.append("no second-read line")
                elif _figures(lines[i]["t"]) != _figures(rows[pairs[i]]):
                    why.append("engines differ")
    for i, why in reasons.items():
        if SUSPECT.search(lines[i]["t"]):
            why.append("suspect characters")
    items = [_item(rec, "line", lines[i]["t"], lines[i].get("first_read", lines[i]["t"]), lines[i]["y"], r,
                   lines[i].get("col", 0))
             for i, r in reasons.items() if r and not lines[i].get("corrected")]
    items += [_item(rec, "margin", m["t"], m["t"], m["y"], ["margin note"])
              for m in rec.get("margin", []) if DIGIT.search(m["t"]) and not m.get("corrected")]
    items += [_item(rec, "footnote", f, f, None, ["footnote"]) for f in rec.get("footnotes", []) if DIGIT.search(f)]
    return items


def crop_box(y, pitch: float, ocr_size: tuple[int, int], img_size: tuple[int, int]) -> tuple[int, int, int, int]:
    """Full-width band of the scan around a line (y in OCR coordinates), with a line of context above and
    below; the lower part of the page for a footnote (y None)."""
    iw, ih = img_size
    sy = ih / ocr_size[1]
    if y is None:
        return 0, int(ih * 0.6), iw, ih
    return 0, max(0, int((y - 1.2 * pitch) * sy)), iw, min(ih, int((y + 2.2 * pitch) * sy))


def _pitch(rec: dict) -> float:
    ys = sorted(ln["y"] for ln in rec["lines"] if not ln.get("col"))
    gaps = [b - a for a, b in itertools.pairwise(ys) if b > a]
    return statistics.median(gaps) if gaps else 0.02 * rec["size"][1]


def _rows(rec: dict, vision: Path):
    if not vision.exists():
        return None
    v = json.loads(vision.read_text())
    if any(ln.get("col") for ln in rec["lines"]):
        cols = column_rows(v)
        return ([r["t"] for r in cols[0]], [r["t"] for r in cols[1]]) if cols else None
    return [r["t"] for r in body_rows(v)]


def build(source_id: str) -> dict:
    from PIL import Image, ImageDraw

    pages = [r for r in read_jsonl(INTERIM_DIR / "ocr" / source_id / "pages.jsonl") if r["page"]]
    lo, hi = (read_yaml(CONFIG_DIR / "segment.yaml")["sources"].get(source_id) or {}).get("index_pages", [0, -1])
    raw = RAW_DIR / source_id
    out = INTERIM_DIR / "review" / source_id
    crops = out / "crops"
    crops.mkdir(parents=True, exist_ok=True)
    items: list[dict] = []
    for rec in pages:
        index = rec["page"].isdigit() and lo <= int(rec["page"]) <= hi
        page_items_ = page_items(rec, _rows(rec, raw / "ocr_vision" / f"leaf_{rec['leaf']:04d}.json"), index)
        if not page_items_:
            continue
        scan = raw / "pages_full" / f"leaf_{rec['leaf']:04d}.jpg"
        pitch = _pitch(rec)
        with Image.open(scan) as img:
            for it in page_items_:
                path = crops / f"{it['id']}.jpg"
                if not path.exists():
                    box = crop_box(it["y"], pitch, tuple(rec["size"]), img.size)
                    band = img.crop(box).convert("RGB")
                    if it["y"] is not None:  # a mark in the left margin at the line under review
                        sy = img.size[1] / rec["size"][1]
                        mid = (it["y"] + 0.45 * pitch) * sy - box[1]
                        h = 0.35 * pitch * sy
                        ImageDraw.Draw(band).polygon([(0, mid - h), (1.4 * h, mid), (0, mid + h)], fill=(200, 30, 30))
                    if band.width > CROP_WIDTH:
                        band = band.resize((CROP_WIDTH, round(band.height * CROP_WIDTH / band.width)))
                    band.save(path, quality=70)
                it["crop"] = f"crops/{path.name}"
        items += page_items_
    write_jsonl(out / "items.jsonl", items)
    (out / "items.js").write_text("window.REVIEW = " + json.dumps(
        {"source": source_id, "items": items}, ensure_ascii=False) + ";\n")
    for name in ("index.html", "review.js", "review.css"):
        shutil.copyfile(PAGE_DIR / name, out / name)
    counts: dict[str, int] = {}
    for it in items:
        for r in it["reasons"]:
            counts[r] = counts.get(r, 0) + 1
    return {"items": len(items), "pages": len({it["page"] for it in items}), "reasons": counts,
            "open": str(out / "index.html")}


def answers_to_corrections(items: list[dict], answers: dict[str, str], by: str, date: str) -> tuple[list[dict], list[dict]]:
    """Corrections for the answered items, and a log row per answer. A confirmed line the merge changed is
    still written as a correction, so the reviewed text is pinned against later changes to the merge."""
    corrections, log = [], []
    for it in items:
        if it["id"] not in answers:
            continue
        new = answers[it["id"]].strip()
        status = "confirmed" if new == it["text"] else "corrected"
        if new != it["find"]:
            corrections.append({"page": it["page"], "find": it["find"], "replace": new,
                                "evidence": f"page image, leaf {it['leaf']}; numeral review ({', '.join(it['reasons'])})",
                                "by": by, "date": date, "review": "done"})
        log.append({"id": it["id"], "page": it["page"], "kind": it["kind"], "status": status,
                    "reasons": it["reasons"], "by": by, "date": date})
    return corrections, log


def append_corrections(path: Path, corrections: list[dict]) -> None:
    """Append to the corrections list, keeping the file's comments (each string is a JSON-quoted scalar)."""
    text = path.read_text()
    if not text.endswith("\n"):
        text += "\n"
    for c in corrections:
        text += f"  - page: {json.dumps(c['page'])}\n"
        for k in ("find", "replace", "evidence", "by", "date", "review"):
            text += f"    {k}: {json.dumps(c[k], ensure_ascii=False)}\n"
    path.write_text(text)


def import_answers(source_id: str, answers_path: Path, by: str) -> dict:
    items = read_jsonl(INTERIM_DIR / "review" / source_id / "items.jsonl")
    answers = json.loads(answers_path.read_text())
    review = DATA_DIR / "review" / source_id
    log_path = review / "numeral_review.jsonl"
    done = {r["id"] for r in read_jsonl(log_path)} if log_path.exists() else set()
    todo = [it for it in items if it["id"] not in done]  # rerunnable: an answer is imported once
    corrections, log = answers_to_corrections(todo, answers, by, dt.date.today().isoformat())
    append_corrections(review / "ocr_corrections.yaml", corrections)
    write_jsonl(log_path, (read_jsonl(log_path) if log_path.exists() else []) + log)
    return {"answered": len(log), "corrections": len(corrections), "already_imported": len(items) - len(todo),
            "left": len(items) - len(done) - len(log)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["build", "import"])
    ap.add_argument("--source", required=True)
    ap.add_argument("--answers", type=Path)
    ap.add_argument("--by", default="owner")
    a = ap.parse_args(argv)
    if a.cmd == "build":
        res = build(a.source)
    else:
        if not a.answers:
            ap.error("import needs --answers")
        res = import_answers(a.source, a.answers, a.by)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
