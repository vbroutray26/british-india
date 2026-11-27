"""GS-EXTRACT: gold labels for DP-06 extraction and the TS-DATA-04 scorer.

One row per gazetteer entry, labelled from the full-resolution scan (never from pipeline output). An
entry row lists every DP-06 fact the entry supports, each with the exact quote as printed, the page it
is printed on and a year only where the quote prints it. An entry with no facts is still a row: it
counts against facts an extractor invents. Rows carry labeller, method and review status (D-16).

TS-DATA-04 (before human review): precision >= 0.92 and recall >= 0.85 per fact type, unsupported-fact
rate <= 1%. A candidate matches a gold fact of the same type (and year, where both give one) whose
quote overlaps its own (fuzzy, diacritics folded); matching is one to one. A candidate is unsupported
when its quote is not in the entry text (the DP-07 quote check, ratio >= 92).

DP-06 is built in M3. The scorer reads `interim/extract/<source>/candidate_facts.jsonl` (rows with
entry_id, type, quote, year) and says so when it is not there yet.

Usage: python -m pipeline.gold_extract check --source omalley-puri-1908
       python -m pipeline.gold_extract score --source omalley-puri-1908
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from rapidfuzz import fuzz

from pipeline.ocr import fold
from pipeline.util import INTERIM_DIR, REPO_ROOT, read_jsonl

GOLD = REPO_ROOT / "gold" / "GS-EXTRACT.jsonl"

# Appendix B: the fact types DP-06 extracts. Areas, populations and coordinates are rule facts (DP-04).
DP06_TYPES = (
    "crop", "industry", "trade_item", "market_or_fair", "port", "railway", "canal", "road", "flood",
    "famine", "cyclone", "epidemic", "temple", "monument", "festival", "school", "hospital",
    "admin_change", "notable_person", "language",
)
MATCH = 85.0      # quote overlap for a candidate to match a gold fact
SUPPORTED = 92.0  # DP-07 quote check
ROW_KEYS = ("gold_id", "source_id", "heading", "entry_type", "pages", "facts", "labeller", "method",
            "labelled_on", "review")


def _norm(s: str) -> str:
    return " ".join(fold(s).split())


def check_row(row: dict) -> list[str]:
    """Errors in one gold row; an empty list means it is well formed."""
    errs = [f"missing {k}" for k in ROW_KEYS if k not in row]
    if errs:
        return errs
    for i, f in enumerate(row["facts"]):
        at = f"fact {i}"
        if f.get("type") not in DP06_TYPES:
            errs.append(f"{at}: type {f.get('type')!r} is not a DP-06 type")
        quote = (f.get("quote") or "").strip()
        if not quote:
            errs.append(f"{at}: empty quote")
        label = (f.get("value") or {}).get("label")
        if not isinstance(label, str) or not label.strip():
            errs.append(f"{at}: value.label missing")
        year = f.get("year")
        if year is not None and (not isinstance(year, int) or str(year) not in quote):
            errs.append(f"{at}: year {year!r} is not printed in the quote")
        digits = set(re.findall(r"\d+", quote.replace(",", "")))
        for n in re.findall(r"\d+", (label or "").replace(",", "")):
            if n not in digits:
                errs.append(f"{at}: number {n} in value is not in the quote")
        if f.get("page") not in row["pages"]:
            errs.append(f"{at}: page {f.get('page')!r} is not one of the entry's pages")
    return errs


def _overlap(a: str, b: str) -> float:
    a, b = _norm(a), _norm(b)
    return fuzz.partial_ratio(a, b) if a and b else 0.0


def match_facts(gold: list[dict], cands: list[dict]) -> list[tuple[int, int]]:
    """One-to-one (gold index, candidate index) pairs, best quote overlap first."""
    scored = []
    for gi, g in enumerate(gold):
        for ci, c in enumerate(cands):
            if g["type"] != c.get("type"):
                continue
            if g.get("year") is not None and c.get("year") is not None and g["year"] != c["year"]:
                continue
            s = _overlap(g["quote"], c.get("quote") or "")
            if s >= MATCH:
                scored.append((-s, gi, ci))
    used_g, used_c, pairs = set(), set(), []
    for _, gi, ci in sorted(scored):
        if gi not in used_g and ci not in used_c:
            used_g.add(gi)
            used_c.add(ci)
            pairs.append((gi, ci))
    return sorted(pairs)


def score_facts(entries: list[tuple[list[dict], list[dict], str]]) -> dict:
    """entries: (gold facts, candidate facts, entry text) per labelled entry."""
    counts: dict = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    n_cands = unsupported = 0
    for gold, cands, text in entries:
        pairs = match_facts(gold, cands)
        mg, mc = {g for g, _ in pairs}, {c for _, c in pairs}
        for gi, g in enumerate(gold):
            counts[g["type"]]["tp" if gi in mg else "fn"] += 1
        for ci, c in enumerate(cands):
            if ci not in mc:
                counts[c.get("type")]["fp"] += 1
        body = _norm(text)
        for c in cands:
            n_cands += 1
            if fuzz.partial_ratio(_norm(c.get("quote") or ""), body) < SUPPORTED:
                unsupported += 1
    by_type = {}
    for t, c in sorted(counts.items(), key=lambda kv: str(kv[0])):
        p = c["tp"] / (c["tp"] + c["fp"]) if c["tp"] + c["fp"] else 1.0
        r = c["tp"] / (c["tp"] + c["fn"]) if c["tp"] + c["fn"] else 1.0
        by_type[t] = {**c, "precision": round(p, 3), "recall": round(r, 3)}
    return {"by_type": by_type, "candidates": n_cands, "unsupported": unsupported,
            "unsupported_rate": round(unsupported / n_cands, 3) if n_cands else 0.0}


def _entries(source_id: str) -> dict[str, dict]:
    recs = read_jsonl(INTERIM_DIR / "segment" / source_id / "entries.jsonl")
    return {_norm(r["heading"]): r for r in recs if r["kind"] == "gazetteer"}


def check(source_id: str) -> dict:
    """Row errors, plus warnings where a quote is not found in DP-02's OCR text of its entry
    (often OCR noise, since labels come from the scan; each warning is worth a look)."""
    rows = [r for r in read_jsonl(GOLD) if r["source_id"] == source_id]
    recs = _entries(source_id)
    out: dict = {"entries": len(rows), "facts": sum(len(r["facts"]) for r in rows), "errors": [], "warnings": []}
    for r in rows:
        out["errors"] += [f"{r['gold_id']}: {e}" for e in check_row(r)]
        rec = recs.get(_norm(r["heading"]))
        if rec is None:
            out["warnings"].append(f"{r['gold_id']}: no DP-02 entry headed {r['heading']!r}")
            continue
        for f in r["facts"]:
            s = fuzz.partial_ratio(_norm(f["quote"]), _norm(rec["text"]))
            if s < 80:
                out["warnings"].append(f"{r['gold_id']}: quote not in OCR text ({s:.0f}): {f['quote'][:60]}")
    return out


def score(source_id: str, candidates: Path | None = None) -> dict:
    rows = [r for r in read_jsonl(GOLD) if r["source_id"] == source_id]
    path = candidates or INTERIM_DIR / "extract" / source_id / "candidate_facts.jsonl"
    head = {"labelled_entries": len(rows), "labelled_facts": sum(len(r["facts"]) for r in rows)}
    if not path.exists():
        return {**head, "note": f"no DP-06 output at {path.relative_to(REPO_ROOT)} (DP-06 is built in M3)"}
    recs = _entries(source_id)
    by_entry: dict = defaultdict(list)
    for c in read_jsonl(path):
        by_entry[c["entry_id"]].append(c)
    entries = []
    for r in rows:
        rec = recs.get(_norm(r["heading"]))
        if rec is not None:
            entries.append((r["facts"], by_entry.get(rec["entry_id"], []), rec["text"]))
    return {**head, **score_facts(entries)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["check", "score"])
    ap.add_argument("--source", required=True)
    ap.add_argument("--candidates", type=Path)
    a = ap.parse_args(argv)
    res = check(a.source) if a.cmd == "check" else score(a.source, a.candidates)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 1 if res.get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
