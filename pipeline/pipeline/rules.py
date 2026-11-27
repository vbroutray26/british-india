"""DP-04 Rule extraction, non-AI (spec §8.5).

Extracts coordinates, area, population (with year), distances, heights and administrative links.
Every extracted value keeps the exact matched string and its offsets in the passage (no quote, no fact).
Facts conform to packages/schema/schemas/fact.schema.json with method="rule".

Output: data/interim/rules/<source_id>/facts.jsonl
Usage: python -m pipeline.rules --source omalley-puri-1908
"""
from __future__ import annotations

import argparse
import re
from collections import Counter

from pipeline.util import INTERIM_DIR, log, read_jsonl, sha256_text, write_jsonl

LG = log("DP-04")

DEG = r"(\d{1,3})\s?[°º*o]\s?(\d{1,2})\s?['’′]?"
COORD = re.compile(
    DEG + r"\s?(?:N\b\.?|north(?:\s+latitude)?),?\s*(?:and|,)\s*" + DEG + r"\s?(?:E\b\.?|east(?:\s+longitude)?)", re.IGNORECASE)
NUMBER = r"(\d{1,3}(?:,\d{3})+|\d+)"
# The book prints decimals with a raised point (4·03); Tesseract reads it as "°" or ":". Before a unit it
# can only be a decimal point (degrees carry a ′ and are never followed by "acres").
DECIMAL = r"(\d{1,3}(?:,\d{3})+|\d+(?:[·°:]\d+)?)"
AREA = re.compile(r"\barea\s+of\s+(?:about\s+)?" + DECIMAL + r"\s+(square\s+miles|acres)", re.IGNORECASE)
AREA2 = re.compile(DECIMAL + r"\s+(square\s+miles)\b", re.IGNORECASE)
# Population: a number is paired with a year ONLY when they are adjacent, never across "as against",
# "from … to …" or other comparisons (the year of the second figure is often implicit). Sentence must
# mention population. (number group, year group) per pattern.
YEAR = r"(1[89]\d\d)"
POP_PAIRS = [
    (re.compile(NUMBER + r"\s+(?:persons\s+|souls\s+)?in\s+" + YEAR + r"\b"), 1, 2),               # 359,236 in 1901
    (re.compile(r"census\s+of\s+" + YEAR + r",?\s+(?:of\s+|was\s+)?" + NUMBER, re.IGNORECASE), 2, 1),       # census of 1901, of 1,017,284
    (re.compile(r"\bin\s+" + YEAR + r"\s+(?:was|numbered|amounted to)\s+" + NUMBER, re.IGNORECASE), 2, 1),  # in 1901 was 49,364
]
SENTENCE = re.compile(r"[^.;]*?\bpopulation\b[^.;]*", re.IGNORECASE)
DISTANCE = re.compile(r"\b(\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten)\s+miles?\s+"
                      r"((?:north|south|east|west)(?:-(?:north|south|east|west))?\s+of|from|distant from)\s+"
                      r"([A-Z][\w’']+(?:\s(?:town|Road|station))?)", re.IGNORECASE)
HEIGHT = re.compile(r"height\s+of\s+(?:about\s+)?" + NUMBER + r"\s+feet", re.IGNORECASE)
ADMIN = re.compile(r"\bin\s+the\s+((?:[A-Z][\w’']+|headquarters))\s+subdivision", re.IGNORECASE)
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}


class _Shift:
    """A match whose offsets are shifted into passage coordinates."""

    def __init__(self, m: re.Match, offset: int):
        self._m, self._o = m, offset

    def group(self, *a):
        return self._m.group(*a)

    def start(self):
        return self._m.start() + self._o

    def end(self):
        return self._m.end() + self._o


def num(s: str) -> int | float:
    if s.lower() in WORDS:
        return WORDS[s.lower()]
    s = re.sub(r"[·°:]", ".", s.replace(",", ""))
    return float(s) if "." in s else int(s)


def fact(place_id: str | None, ftype: str, value: dict, p: dict, m: re.Match, conf: float, year: int | None = None) -> dict:
    quote = m.group(0)
    start = p["char_start"] + m.start()
    fid = "ft_" + sha256_text(p["passage_id"], ftype, str(m.start()), quote)[:12]
    f = {
        "fact_id": fid,
        "place_id": place_id or "pl_unlinked",
        "type": ftype,
        "value": value,
        "evidence": [{"passage_id": p["passage_id"], "quote": quote, "char_start": m.start(), "char_end": m.end()}],
        "method": "rule",
        "confidence": conf,
        "review": {"status": "unreviewed"},
        "notes": f"page {p['page']}; entry offset {start}",
    }
    if year:
        f["as_of_year"] = year
    return f


def extract(p: dict, place_id: str | None) -> list[dict]:
    t, out = p["text"], []
    for m in COORD.finditer(t):
        lat = int(m.group(1)) + int(m.group(2)) / 60
        lon = int(m.group(3)) + int(m.group(4)) / 60
        if 5 <= lat <= 38 and 60 <= lon <= 100:  # sanity: inside the subcontinent
            out.append(fact(place_id, "area" if False else "admin_change", {}, p, m, 0, None) | {
                "type": "coordinates", "value": {"lat": round(lat, 4), "lon": round(lon, 4), "quality": "heading"}, "confidence": 0.95})
    for rx in (AREA, AREA2):
        for m in rx.finditer(t):
            if rx is AREA2 and any(f["type"] == "area" and f["evidence"][0]["char_start"] <= m.start() < f["evidence"][0]["char_end"] for f in out):
                continue
            unit = "sq_miles" if "square" in m.group(2).lower() else "acres"
            out.append(fact(place_id, "area", {"number": num(m.group(1)), "unit": unit}, p, m, 0.9 if rx is AREA else 0.7))
    for sm in SENTENCE.finditer(t):
        sent = sm.group(0)
        for rx, gn, gy in POP_PAIRS:
            for m in rx.finditer(sent):
                n, year = num(m.group(gn)), int(m.group(gy))
                if n >= 10 and not (1800 <= n <= 1950 and "," not in m.group(gn)):  # a bare year is not a count
                    mm = _Shift(m, sm.start())
                    out.append(fact(place_id, "population", {"number": n, "unit": "persons"}, p, mm, 0.9, year))
    for m in DISTANCE.finditer(t):
        out.append(fact(place_id, "distance", {"miles": num(m.group(1)), "relation": m.group(2).lower(), "to": m.group(3)}, p, m, 0.85))
    for m in HEIGHT.finditer(t):
        out.append(fact(place_id, "height", {"number": num(m.group(1)), "unit": "feet"}, p, m, 0.9))
    for m in ADMIN.finditer(t):
        out.append(fact(place_id, "admin_link", {"subdivision": m.group(1)}, p, m, 0.85))
    # de-duplicate identical spans (two patterns matching the same text)
    seen, uniq = set(), []
    for f in out:
        k = (f["type"], f["evidence"][0]["char_start"])
        if k not in seen:
            seen.add(k)
            uniq.append(f)
    return uniq


def consistency(facts: list[dict]) -> list[dict]:
    """Numeric consistency (spec §8.2 'Number safety'): the same place and year should not carry two
    different population figures. Returns conflicts for the review queue; nothing is overwritten."""
    by: dict[tuple, list[dict]] = {}
    for f in facts:
        if f["type"] == "population":
            scope = f["place_id"] if f["place_id"] != "pl_unlinked" else f["evidence"][0]["passage_id"]
            by.setdefault((scope, f.get("as_of_year")), []).append(f)
    return [{"place_id": k[0], "year": k[1], "values": sorted({x["value"]["number"] for x in v}),
             "fact_ids": [x["fact_id"] for x in v], "quotes": [x["evidence"][0]["quote"] for x in v]}
            for k, v in by.items() if len({x["value"]["number"] for x in v}) > 1]


def run(source_id: str) -> list[dict]:
    d = INTERIM_DIR / "classify" / source_id
    passages = read_jsonl(d / "passages.jsonl")
    by_entry = {e: p["place_id"] for p in read_jsonl(d / "places.jsonl") for e in p["entry_ids"]}
    facts = [f for p in passages for f in extract(p, by_entry.get(p["entry_id"]))]
    write_jsonl(INTERIM_DIR / "rules" / source_id / "facts.jsonl", facts)
    conflicts = consistency(facts)
    write_jsonl(INTERIM_DIR / "rules" / source_id / "conflicts.jsonl", conflicts)
    if conflicts:
        LG.warning("%d numeric conflicts sent to review", len(conflicts))
    LG.info("%d rule facts: %s", len(facts), dict(Counter(f["type"] for f in facts)))
    return facts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--resume", action="store_true")
    run(ap.parse_args(argv).source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
