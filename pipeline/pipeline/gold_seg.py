"""GS-SEG: entry and section boundary gold set and scorer (TS-DATA-02, target >= 98%).

Each gold row is a boundary read from the full-resolution scan: the kind of record that should start
there (gazetteer entry or chapter section), the printed page, the heading as printed and the opening
words. A boundary is

  found   - DP-02 starts a record of that kind on that page whose first 200 characters contain the
            opening words (fuzzy, diacritics folded: OCR noise is not a segmentation error);
  merged  - the opening words are inside some other record of that kind (the boundary was not split);
  missed  - neither.

Usage: python -m pipeline.gold_seg score --source omalley-puri-1908
"""

from __future__ import annotations

import argparse
import json

from rapidfuzz import fuzz

from pipeline.ocr import fold
from pipeline.util import INTERIM_DIR, REPO_ROOT, read_jsonl

GOLD = REPO_ROOT / "gold" / "GS-SEG.jsonl"
MIN_SCORE = 85.0
HEAD = 200


def _norm(s: str) -> str:
    return " ".join(fold(s).split())


def match(g: dict, records: list[dict]) -> str:
    words = _norm(g["first_words"])
    # An entry's printed heading is often garbled by OCR; the words after the dash place the boundary too.
    rest = _norm(g["first_words"].split("—", 1)[1]) if "—" in g["first_words"] else words
    same_kind = [r for r in records if r["kind"] == g["kind"]]
    if any(r["page_start"] == g["page"]
           and max(fuzz.partial_ratio(words, _norm(r["text"][:HEAD])), fuzz.partial_ratio(rest, _norm(r["text"][:HEAD])))
           >= MIN_SCORE for r in same_kind):
        return "found"
    if any(fuzz.partial_ratio(words, _norm(r["text"])) >= MIN_SCORE for r in same_kind):
        return "merged"
    return "missed"


def score(source_id: str) -> dict:
    gold = [g for g in read_jsonl(GOLD) if g["source_id"] == source_id]
    records = read_jsonl(INTERIM_DIR / "segment" / source_id / "entries.jsonl")
    res: dict = {"labelled": len(gold), "found": 0, "merged": [], "missed": []}
    for g in gold:
        m = match(g, records)
        if m == "found":
            res["found"] += 1
        else:
            res[m].append({"gold_id": g["gold_id"], "kind": g["kind"], "page": g["page"], "heading": g["heading"]})
    res["accuracy"] = round(res["found"] / max(1, res["labelled"]), 3)
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["score"])
    ap.add_argument("--source", required=True)
    a = ap.parse_args(argv)
    print(json.dumps(score(a.source), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
