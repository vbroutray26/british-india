"""DP-03 Classify entries and assign IDs (spec §8.4).

Rules read the descriptor that follows the heading ("A village in…", "Headquarters of the district…").
Low-confidence labels go to data/review/<source>/classify_queue.jsonl for a person (or, later, the
closed-label LLM classifier) to settle.

Output: data/interim/classify/<source_id>/places.jsonl and passages.jsonl
Usage: python -m pipeline.classify --source omalley-puri-1908
"""
from __future__ import annotations

import argparse
import re
import unicodedata

from pipeline.ocr import fold
from pipeline.passages import passages
from pipeline.util import DATA_DIR, INTERIM_DIR, log, read_jsonl, sha256_text, write_jsonl

LG = log("DP-03")

# (pattern on the first ~120 characters after the heading, type, confidence)
RULES: list[tuple[str, str, float]] = [
    (r"headquarters of the district", "town", 0.95),
    (r"headquarters of the subdivision", "town", 0.95),
    (r"^(?:headquarters|western|eastern|northern|southern)\s+subdivision", "subdivision", 0.95),
    (r"\bsubdivision of the district", "subdivision", 0.9),
    (r"^an?\s+(?:large\s+|small\s+)?(?:government\s+)?estate", "estate", 0.95),
    (r"^an?\s+(?:ruined\s+)?temple", "temple", 0.9),
    (r"^an?\s+(?:large\s+|small\s+)?vill[ao]ge", "village", 0.95),  # OCR: "villoge"
    (r"^an?\s+(?:small\s+)?town", "town", 0.95),
    (r"^an?\s+hill|the highest in a line of (?:low )?hills", "hill", 0.95),
    (r"^an?\s+(?:large\s+)?lake", "lake", 0.95),
    (r"^an?\s+river", "river", 0.95),
    (r"\bvillage\b", "village", 0.6),
]
HEADING_HINTS = [(r"\bsubdivision\b", "subdivision"), (r"\bhill\b", "hill"), (r"\bghat\b", "village")]


def slug(s: str) -> str:
    a = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", a.lower()).strip("-")


def place_id(heading: str, ptype: str) -> str:
    """Immutable ID: slug + short hash of (slug, type). Merges in DP-09 redirect, never reuse (§7.5)."""
    s = slug(heading)
    return f"pl_{s}-{sha256_text(s, ptype)[:4]}"


def classify_entry(e: dict) -> tuple[str, float, str]:
    after = re.sub(r"^.{0,60}?(?:—|--|–|~)\s?a?(?=[A-Z])", "", e["text"][:200], count=1)
    after = fold(after.strip())[:140]
    for pat, t, conf in RULES:
        if re.search(pat, after):
            return t, conf, pat
    for pat, t in HEADING_HINTS:
        if re.search(pat, fold(e["heading"])):
            return t, 0.6, f"heading:{pat}"
    return "uncertain", 0.0, ""


def run(source_id: str) -> list[dict]:
    entries = read_jsonl(INTERIM_DIR / "segment" / source_id / "entries.jsonl")
    places, queue, all_passages = [], [], []
    for e in entries:
        all_passages += passages(e)
        if e["kind"] != "gazetteer":
            continue
        t, conf, rule = classify_entry(e)
        low_heading = (e.get("heading_match") or 0) < 80
        pid = place_id(e["heading"], t)
        places.append({
            "place_id": pid,
            "type": t,
            "names": [{"text": e["heading"], "lang": "en", "script": "Latn", "kind": "primary", "source_id": source_id}],
            "status": "uncertain" if t == "uncertain" else "existing",
            "entry_ids": [e["entry_id"]],
            "classify": {"rule": rule, "confidence": conf},
            "review": {"status": "unreviewed"},
        })
        if conf < 0.8 or low_heading:
            queue.append({"entry_id": e["entry_id"], "place_id": pid, "heading": e["heading"], "type": t,
                          "confidence": conf, "heading_match": e.get("heading_match"),
                          "reason": "low classification confidence" if conf < 0.8 else "heading OCR garbled; anchor inferred",
                          "page": e["page_start"], "opening": e["text"][:160]})
    out = INTERIM_DIR / "classify" / source_id
    write_jsonl(out / "places.jsonl", places)
    write_jsonl(out / "passages.jsonl", all_passages)
    write_jsonl(DATA_DIR / "review" / source_id / "classify_queue.jsonl", queue)
    LG.info("%d places (%s); %d passages; %d to review", len(places),
            ", ".join(f"{t}:{sum(1 for p in places if p['type'] == t)}" for t in sorted({p["type"] for p in places})),
            len(all_passages), len(queue))
    return places


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--resume", action="store_true")
    run(ap.parse_args(argv).source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
