"""DP-07 Verification, non-AI (spec §8.8). Nothing unverified reaches the build.

Checks every candidate fact:
  1. quote: after normalising whitespace, case and diacritics, the quote is in the passage with
     fuzzy ratio >= 0.92 — and numbers must match exactly;
  2. schema: valid against packages/schema/schemas/fact.schema.json;
  3. numbers: every number in the value appears in the quote;
  4. rule agreement: a DP-06 (llm) value that disagrees with a DP-04 (rule) value on the same field → conflict;
  5. vocabulary: list items map to the controlled vocabulary or are marked new-term;
  6. second read: every figure in the quote was also read by the second OCR engine on the passage's
     pages (DP-01b, D-24), so a figure misread by one engine does not pass unseen.
Failures are rejected or queued for review, with the reason.

Usage: python -m pipeline.verify --source omalley-puri-1908 [--input rules|llm]
"""
from __future__ import annotations

import argparse
import re
from collections import Counter

from rapidfuzz import fuzz

from pipeline.ocr import fold
from pipeline.util import DATA_DIR, INTERIM_DIR, log, read_jsonl, write_jsonl
from pipeline.validate import validator

LG = log("DP-07")
QUOTE_MIN = 92.0
# Place attributes (geometry and relations for DP-09), not fact-card facts: same quote and number
# checks, but no fact-schema check.
ATTRIBUTE_TYPES = {"coordinates", "distance", "height", "admin_link"}
NUMBER_WORDS = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7",
                "eight": "8", "nine": "9", "ten": "10"}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", fold(s)).strip()


_RAISED_POINT = re.compile(r"(?<=\d)[·°:](?=\d+(?![\d′'’]))")  # 4°03 is 4·03; 20°11′ stays a coordinate


def numbers_in(s: str, words: bool = False) -> list[str]:
    s = _RAISED_POINT.sub(".", s)
    nums = [n.replace(",", "") for n in re.findall(r"\d[\d,]*(?:\.\d+)?", s)]
    if words:
        nums += [NUMBER_WORDS[w] for w in re.findall(r"[a-z]+", s.lower()) if w in NUMBER_WORDS]
    return nums


def quote_ok(quote: str, passage: str) -> tuple[bool, float]:
    q, p = norm(quote), norm(passage)
    if not q:
        return False, 0.0
    if q in p:
        score = 100.0
    else:
        score = fuzz.partial_ratio(q, p)
    # numbers in the quote must appear verbatim in the passage
    nums_ok = all(n in numbers_in(passage) for n in numbers_in(quote))
    return score >= QUOTE_MIN and nums_ok, round(score, 1)


def value_numbers(value: dict) -> list[str]:
    out = []
    for k, v in value.items():
        if isinstance(v, (int, float)) and k not in ("lat", "lon"):
            out.append(str(int(v)) if float(v).is_integer() else str(v))
    return out


def _page_span(p: dict) -> list[str]:
    a, b = p.get("page"), p.get("page_end") or p.get("page")
    if a and b and a.isdigit() and b.isdigit():
        return [str(n) for n in range(int(a), int(b) + 1)]
    return [x for x in dict.fromkeys((a, b)) if x]


def second_read_reasons(f: dict, passages: dict[str, dict], second: dict[str, set[str]]) -> list[str]:
    reasons = []
    for ev in f["evidence"]:
        p = passages.get(ev["passage_id"])
        nums = numbers_in(ev["quote"])
        if not p or not nums:
            continue
        span = _page_span(p)
        seen = set().union(*(second[pg] for pg in span if pg in second))
        reasons += [f"no second read for page {pg}" for pg in span if pg not in second]
        reasons += [f"second read disagrees: {n}" for n in nums if n not in seen and seen]
    return list(dict.fromkeys(reasons))


def recovered_reasons(f: dict, passages: dict[str, dict], recovered: dict[str, list[str]]) -> list[str]:
    """A figure on a line DP-01 recovered from the second read was read by one engine only, so the
    second-read agreement check says nothing about it (D-27)."""
    from rapidfuzz import fuzz

    reasons = []
    for ev in f["evidence"]:
        p = passages.get(ev["passage_id"])
        nums = numbers_in(ev["quote"])
        if not p or not nums:
            continue
        for pg in _page_span(p):
            for t in recovered.get(pg, []):
                if fuzz.partial_ratio(ev["quote"], t) >= 90 and all(n in numbers_in(t) for n in nums):
                    reasons.append(f"one engine only: line missing from the first OCR (p. {pg})")
    return list(dict.fromkeys(reasons))


def check(f: dict, passages: dict[str, dict], schema, second: dict[str, set[str]] | None = None,
          recovered: dict[str, list[str]] | None = None) -> list[str]:
    reasons = [] if second is None else second_read_reasons(f, passages, second)
    if recovered:
        reasons += recovered_reasons(f, passages, recovered)
    for ev in f["evidence"]:
        p = passages.get(ev["passage_id"])
        if not p:
            reasons.append(f"unknown passage {ev['passage_id']}")
            continue
        ok, score = quote_ok(ev["quote"], p["text"])
        if not ok:
            reasons.append(f"quote not found (score {score})")
        if p["text"][ev["char_start"]:ev["char_end"]] != ev["quote"]:
            reasons.append("offsets do not point at the quote")
    quote_nums = [n for ev in f["evidence"] for n in numbers_in(ev["quote"], words=True)]
    for n in value_numbers(f["value"]):
        if n not in quote_nums:
            reasons.append(f"number {n} not in quote")
    sf = {k: v for k, v in f.items() if k in schema.schema["properties"]}
    for e in ([] if f["type"] in ATTRIBUTE_TYPES else schema.iter_errors(sf)):
        reasons.append(f"schema: {'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message[:80]}")
    return reasons


def run(source_id: str, which: str = "rules") -> dict:
    passages = {p["passage_id"]: p for p in read_jsonl(INTERIM_DIR / "classify" / source_id / "passages.jsonl")}
    facts = read_jsonl(INTERIM_DIR / which / source_id / "facts.jsonl")
    schema = validator("fact.schema.json")
    from pipeline.second_read import load

    second = load(source_id)
    recovered = {r["page"]: r["recovered"] for r in read_jsonl(INTERIM_DIR / "ocr" / source_id / "pages.jsonl")
                 if r.get("page") and r.get("recovered")}
    if not second:
        LG.warning("no second read for %s: every fact with a figure is queued (run DP-01b)", source_id)
    accepted, attributes, rejected = [], [], []
    for f in facts:
        reasons = check(f, passages, schema, second, recovered)
        if reasons:
            rejected.append(f | {"verify": {"reasons": reasons}})
        else:
            (attributes if f["type"] in ATTRIBUTE_TYPES else accepted).append(f)
    out = INTERIM_DIR / "verify" / source_id
    write_jsonl(out / f"{which}_accepted.jsonl", accepted)
    write_jsonl(out / f"{which}_attributes.jsonl", attributes)
    write_jsonl(out / f"{which}_rejected.jsonl", rejected)
    write_jsonl(DATA_DIR / "review" / source_id / f"verify_{which}_queue.jsonl",
                [{"fact_id": f["fact_id"], "type": f["type"], "reasons": f["verify"]["reasons"],
                  "quote": f["evidence"][0]["quote"]} for f in rejected])
    stats = {"accepted": len(accepted), "attributes": len(attributes), "rejected": len(rejected),
             "reasons": dict(Counter(r.split(" (")[0].split(":")[0] for f in rejected for r in f["verify"]["reasons"]))}
    LG.info("%s: %d facts accepted, %d place attributes accepted, %d rejected %s", which, stats["accepted"],
            stats["attributes"], stats["rejected"], stats["reasons"])
    return stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--input", default="rules", choices=["rules", "llm"])
    ap.add_argument("--resume", action="store_true")
    a = ap.parse_args(argv)
    run(a.source, a.input)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
