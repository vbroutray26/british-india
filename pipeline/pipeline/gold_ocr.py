"""GS-OCR: corrected page transcriptions and the OCR character error rate (spec §14.2, TS-DATA-01).

  python -m pipeline.gold_ocr sample --source omalley-puri-1908 [--n 50]   # choose pages, write the manifest
  python -m pipeline.gold_ocr seed   --source omalley-puri-1908            # OCR text as a draft to correct
  python -m pipeline.gold_ocr view   --source omalley-puri-1908 --page 61  # full-resolution crops for reading
  python -m pipeline.gold_ocr score  --source omalley-puri-1908            # CER, raw OCR and after review

Transcriptions live in gold/GS-OCR/<source>/p<page>.txt; the manifest gold/GS-OCR.jsonl records labeller,
method and review status per page (D-16). Conventions are in gold/README.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import re
import unicodedata
from pathlib import Path

from rapidfuzz.distance import Levenshtein

from pipeline import REPO_ROOT
from pipeline.util import INTERIM_DIR, read_jsonl, write_jsonl

GOLD = REPO_ROOT / "gold"
MANIFEST = GOLD / "GS-OCR.jsonl"
SECTIONS = ("body", "footnotes")

# Typographic variants that carry no textual difference. Letters and diacritics are never folded here.
TYPO = str.maketrans({"“": '"', "”": '"', "„": '"', "‘": "'", "’": "'", "′": "'", "″": '"',
                      "—": "-", "–": "-", "‐": "-", "‑": "-", " ": " "})


def normalise(text: str, fold_diacritics: bool = False) -> str:
    s = unicodedata.normalize("NFC", text).translate(TYPO).replace("{", "").replace("}", "")
    if fold_diacritics:
        s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip()


def cer(gold: str, ocr: str, fold_diacritics: bool = False) -> dict:
    g, o = normalise(gold, fold_diacritics), normalise(ocr, fold_diacritics)
    ops = Levenshtein.editops(g, o)
    digit_edits = sum(
        1 for op in ops
        if (op.tag in ("replace", "delete") and g[op.src_pos].isdigit())
        or (op.tag in ("replace", "insert") and o[op.dest_pos].isdigit())
    )
    return {"chars": len(g), "edits": len(ops), "digits": sum(c.isdigit() for c in g), "digit_edits": digit_edits}


def parse_gold(text: str) -> dict:
    out, cur = {s: [] for s in SECTIONS}, None
    for line in text.splitlines():
        if line.startswith("%"):
            continue
        if line.startswith("@@ "):
            cur = line[3:].strip()
            if cur not in out:
                raise ValueError(f"unknown section {cur!r}")
            continue
        if cur:
            out[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def _strata(pages: list[dict]) -> list[list[dict]]:
    pool = sorted((p for p in pages if p.get("page") and "blank-or-plate" not in p.get("flags", [])),
                  key=lambda p: (p["confidence"], p["leaf"]))
    k = len(pool) // 4
    return [pool[i * k:(i + 1) * k] if i < 3 else pool[3 * k:] for i in range(4)]


def sample_pages(pages: list[dict], n: int, seed: int = 1908) -> list[str]:
    """Stratified by OCR confidence quartile so hard pages are represented; stable for a given seed."""
    rng, picked, strata = random.Random(seed), [], _strata(pages)
    for i, st in enumerate(strata):
        picked += rng.sample(st, n // 4 + (1 if i < n % 4 else 0))
    return [p["page"] for p in sorted(picked, key=lambda p: p["leaf"])]


def replacement_page(pages: list[dict], page: str, taken: list[str], seed: int = 1908) -> str:
    """A stand-in for a sampled page found to hold no running text (e.g. a map the flags missed):
    drawn from the same confidence stratum, never a page already taken, stable for a given seed."""
    stratum = next(st for st in _strata(pages) if any(p["page"] == page for p in st))
    free = sorted((p["page"] for p in stratum if p["page"] not in taken), key=lambda x: int(x) if x.isdigit() else 0)
    return random.Random(f"{seed}-{page}").choice(free)


def ocr_text(rec: dict, reviewed: bool) -> str:
    """The OCR's page text in its own reading order: lines and margin notes by y, then footnotes.

    reviewed=False uses the text as first read (text_raw, without lines recovered from the second read);
    True uses lines after audited corrections and recovery (D-27)."""
    lines = rec["lines"] if reviewed else [ln for ln in rec["lines"] if not ln.get("recovered")]
    raw = rec["text_raw"].split("\n")
    texts = [ln["t"] for ln in lines] if reviewed or len(raw) != len(lines) else raw
    items = [(ln["y"], t) for ln, t in zip(lines, texts, strict=True)]
    items += [(m["y"], m["t"]) for m in rec.get("margin", [])]
    return "\n".join([t for _, t in sorted(items, key=lambda x: x[0])] + list(rec.get("footnotes", [])))


def _pages(source_id: str) -> dict[str, dict]:
    return {r["page"]: r for r in read_jsonl(INTERIM_DIR / "ocr" / source_id / "pages.jsonl") if r["page"]}


def _path(source_id: str, page: str) -> Path:
    return GOLD / "GS-OCR" / source_id / f"p{page.zfill(3)}.txt"


def sample(source_id: str, n: int) -> list[dict]:
    pages = _pages(source_id)
    rows = [r for r in read_jsonl(MANIFEST) if r["source_id"] != source_id] if MANIFEST.exists() else []
    keep = {r["page"]: r for r in read_jsonl(MANIFEST) if r["source_id"] == source_id} if MANIFEST.exists() else {}
    slug = source_id.split("-")[0]
    for p in sample_pages(list(pages.values()), n):
        rows.append(keep.get(p) or {
            "gold_id": f"gso-{slug}-p{p.zfill(3)}", "source_id": source_id, "page": p, "leaf": pages[p]["leaf"],
            "file": str(_path(source_id, p).relative_to(REPO_ROOT)), "status": "seeded", "labeller": "claude",
            "method": "OCR seed corrected line by line against the full-resolution scan (archive.org JP2)",
            "labelled_on": None, "review": {"reviewer": "owner", "status": "pending"},
        })
    rows += [r for r in keep.values() if r.get("replaces")]  # replacements survive a re-sample
    write_jsonl(MANIFEST, sorted(rows, key=lambda r: (r["source_id"], r["leaf"])))
    return rows


def seed(source_id: str) -> int:
    pages, made = _pages(source_id), 0
    for r in read_jsonl(MANIFEST):
        path = REPO_ROOT / r["file"]
        if r["source_id"] != source_id or r["status"] == "excluded" or path.exists():
            continue  # never overwrite a transcription
        rec = pages[r["page"]]
        items = [(ln["y"], ln["t"]) for ln in rec["lines"]] + [(m["y"], "{" + m["t"] + "}") for m in rec["margin"]]
        body = "\n".join(t for _, t in sorted(items, key=lambda x: x[0]))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"% GS-OCR {source_id} page {r['page']} (leaf {r['leaf']}). Conventions: gold/README.md\n"
                        f"@@ body\n{body}\n@@ footnotes\n" + "\n".join(rec["footnotes"]) + "\n")
        made += 1
    return made


def view(source_id: str, page: str, out_dir: Path, parts: int = 2) -> list[Path]:
    from PIL import Image

    from pipeline.scan import image

    rec = _pages(source_id)[page]
    img = Image.open(image(source_id, rec["leaf"], full=True))
    w, h = img.size
    dark = img.point(lambda v: 255 if v < 110 else 0).crop((int(w * 0.03), int(h * 0.02), int(w * 0.97), int(h * 0.98)))
    x0, y0, x1, y1 = dark.getbbox() or (0, 0, w, h)
    x0, x1, y0, y1 = x0 + int(w * 0.03) - 20, x1 + int(w * 0.03) + 20, y0 + int(h * 0.02) - 20, y1 + int(h * 0.02) + 20
    step, out = (y1 - y0) / parts, []
    out_dir.mkdir(parents=True, exist_ok=True)
    for i in range(parts):
        top, bottom = int(y0 + i * step - (40 if i else 0)), int(y0 + (i + 1) * step + 40)
        p = out_dir / f"p{page.zfill(3)}_{i + 1}.jpg"
        img.crop((max(0, x0), max(0, top), min(w, x1), min(h, bottom))).save(p, quality=88)
        out.append(p)
    return out


def score(source_id: str, engine: str = "tesseract") -> dict:
    """CER against the gold pages. engine="vision" scores the second read (DP-01b) in place of DP-01;
    it has no separate reviewed text, so both columns are the same."""
    pages = _pages(source_id)
    if engine == "vision":
        second = {r["page"]: r["text"] for r in read_jsonl(INTERIM_DIR / "ocr2" / source_id / "pages.jsonl")}
    rows = [r for r in read_jsonl(MANIFEST) if r["source_id"] == source_id and r["status"] == "transcribed"]
    res: dict = {"pages": len(rows), "per_page": []}
    totals = {k: {"chars": 0, "edits": 0, "digits": 0, "digit_edits": 0, "edits_folded": 0} for k in ("raw", "reviewed")}
    for r in rows:
        g = parse_gold((REPO_ROOT / r["file"]).read_text())
        gold = g["body"] + "\n" + g["footnotes"]
        line = {"page": r["page"]}
        for k, tot in totals.items():
            o = second[r["page"]] if engine == "vision" else ocr_text(pages[r["page"]], reviewed=k == "reviewed")
            c, f = cer(gold, o), cer(gold, o, fold_diacritics=True)
            for m in ("chars", "edits", "digits", "digit_edits"):
                tot[m] += c[m]
            tot["edits_folded"] += f["edits"]
            line[k] = round(c["edits"] / max(1, c["chars"]), 4)
        res["per_page"].append(line)
    for k, t in totals.items():
        res[k] = {"cer": round(t["edits"] / max(1, t["chars"]), 4),
                  "cer_diacritics_folded": round(t["edits_folded"] / max(1, t["chars"]), 4),
                  "numeral_cer": round(t["digit_edits"] / max(1, t["digits"]), 4), **t}
    res["per_page"].sort(key=lambda x: -x["raw"])
    return res


def mark_transcribed(source_id: str, pages: list[str]) -> None:
    rows = read_jsonl(MANIFEST)
    for r in rows:
        if r["source_id"] == source_id and r["page"] in pages:
            r["status"], r["labelled_on"] = "transcribed", dt.date.today().isoformat()
    write_jsonl(MANIFEST, rows)


def exclude(source_id: str, page: str, reason: str) -> str:
    """Mark a sampled page excluded (kept in the manifest with its reason) and add a replacement."""
    pages, rows = _pages(source_id), read_jsonl(MANIFEST)
    taken = [r["page"] for r in rows if r["source_id"] == source_id]
    new = replacement_page(list(pages.values()), page, taken)
    slug = source_id.split("-")[0]
    for r in rows:
        if r["source_id"] == source_id and r["page"] == page:
            r["status"], r["excluded_reason"] = "excluded", reason
            proto = r
    rows.append({**{k: v for k, v in proto.items() if k != "excluded_reason"},
                 "gold_id": f"gso-{slug}-p{new.zfill(3)}", "page": new, "leaf": pages[new]["leaf"],
                 "file": str(_path(source_id, new).relative_to(REPO_ROOT)), "status": "seeded", "labelled_on": None,
                 "replaces": page, "review": {"reviewer": "owner", "status": "pending"}})
    write_jsonl(MANIFEST, sorted(rows, key=lambda r: (r["source_id"], r["leaf"])))
    return new


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["sample", "seed", "view", "score", "done", "exclude"])
    ap.add_argument("--source", required=True)
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--page", action="append", default=[])
    ap.add_argument("--out", type=Path, default=Path("gso_view"))
    ap.add_argument("--reason", default="")
    ap.add_argument("--engine", default="tesseract", choices=["tesseract", "vision"])
    a = ap.parse_args(argv)
    if a.cmd == "sample":
        print("\n".join(r["page"] for r in sample(a.source, a.n) if r["source_id"] == a.source))
    elif a.cmd == "seed":
        print(f"seeded {seed(a.source)} pages")
    elif a.cmd == "view":
        for p in a.page:
            print("\n".join(str(x) for x in view(a.source, p, a.out)))
    elif a.cmd == "exclude":
        for p in a.page:
            print(f"p{p} excluded; replacement p{exclude(a.source, p, a.reason)}")
    elif a.cmd == "done":
        mark_transcribed(a.source, a.page)
    else:
        print(json.dumps(score(a.source, a.engine), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
