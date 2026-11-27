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

from pipeline.passages import page_at
from pipeline.util import INTERIM_DIR, log, read_jsonl, sha256_text, write_jsonl

LG = log("DP-04")

DEG = r"(\d{1,3})\s?[°º*o]\s?(\d{1,2})\s?['’′]?"
COORD = re.compile(
    DEG + r"\s?(?:N\b\.?|north(?:\s+latitude)?),?\s*(?:and|,)\s*" + DEG + r"\s?(?:E\b\.?|east(?:\s+longitude)?)", re.IGNORECASE)
NUMBER = r"(\d{1,3}(?:,\d{3})+|\d+)"
# The book prints decimals with a raised point (4·03); Tesseract reads it as "°" or ":". Before a unit it
# can only be a decimal point (degrees carry a ′ and are never followed by "acres").
DECIMAL = r"(\d{1,3}(?:,\d{3})+|\d+(?:[·°:]\d+)?)"
SQ = r"sq[a-z]{3,4}\s+miles"  # "square", and OCR's "squsre", "sqnare"
AREA = re.compile(r"\barea\s+of\s+(?:about\s+)?" + DECIMAL + r"\s+(" + SQ + r"|acres)", re.IGNORECASE)
AREA2 = re.compile(DECIMAL + r"\s+(" + SQ + r")\b", re.IGNORECASE)
# Acres are also crop and holding sizes; only a land unit's extent is an area: "has an area, according to
# the latest survey, of 618,154 acres", "extending over 68,000 acres", "villages containing 540,376 acres".
AREA_ACRES = re.compile(r"(?:\barea\b[^.;\d]{0,80}?\b(?:of|is|was)|\bextending\s+over|\bcontaining|\bcover(?:s|ing)|"
                        r"\bcomprising)\s+(?:about\s+)?" + DECIMAL + r"\s+(acres)\b", re.IGNORECASE)
# Population: a number is paired with a year ONLY when they are adjacent, never across "as against",
# "from … to …" or other comparisons (the year of the second figure is often implicit). Sentence must
# mention population. (number group, year group) per pattern.
YEAR = r"(1[89]\d\d)"
POPN = NUMBER + r"(?![\d,]*\s+(?:per\b|million|lakhs?|crores?))"  # "60 per cent.", "24 million" are not counts
POP_PAIRS = [
    (re.compile(POPN + r"\s+(?:persons\s+|souls\s+)?in\s+" + YEAR + r"\b"), 1, 2),               # 359,236 in 1901
    (re.compile(r"census\s+of\s+" + YEAR + r",?\s+(?:of\s+|was\s+)?" + POPN, re.IGNORECASE), 2, 1),       # census of 1901, of 1,017,284
    (re.compile(r"\bin\s+" + YEAR + r"\s+(?:was\s+returned\s+at|was|numbered|amounted\s+to|at)\s+" + POPN,
                re.IGNORECASE), 2, 1),                                                   # in 1891 was returned at 944,998
]
# A count with no year beside it: "the population had risen to 1,017,284", "its population 10,000 souls",
# "contained 3,000 souls". It takes the clause's census year only when the clause names one year and
# mentions the census; otherwise it carries no year (never a guess).
POP_COUNTS = [
    re.compile(r"\bpopulation(?:\s+(?:is|was|of|had\s+risen\s+to|rose\s+to|amounted\s+to|numbered))?\s+" + POPN
               + r"(?!\s+(?:persons\s+)?(?:to|per)\s+(?:the\s+)?square)", re.IGNORECASE),
    re.compile(r"\b(?:contain\W{0,3}ing|contained|with)\s+" + POPN + r"\s+souls\b", re.IGNORECASE),
]
# A census summary table row: name, area (sq. miles), towns, villages, population, persons per sq. mile
# ("Puri ... ... 1,528 1 1,889 658,048 431"). Accepted only when population / area agrees with the printed
# density within 2%, so a misread figure drops the row instead of entering wrong data. The year is the last
# "census of YEAR" before the table in the entry.
TABLE_ROW = re.compile(r"\b([A-Z][A-Za-z]+(?:\s+[a-z]+)?)(?:\s+\.{2,})*\s+" + NUMBER + r"\s+(\d+|\.{2,})\s+" + NUMBER
                       + r"\s+" + NUMBER + r"\s+(\d{1,4})\b")
CENSUS_YEAR = re.compile(r"census\s+of\s+" + YEAR, re.IGNORECASE)
# Clauses end at ";" or at a full stop before a capital ("15·4 per cent., being" does not end one).
CLAUSE = re.compile(r"(?:[^.;]|\.(?!\s+[A-Z\"'(]|\s*$))+")
POP_WORDS = re.compile(r"\b(?:population|souls|inhabitants|c[eo]nsus)\b", re.IGNORECASE)  # OCR: "consus"
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


def fact(place_id: str | None, ftype: str, value: dict, p: dict, m: re.Match, conf: float, year: int | None = None,
         spans: list[dict] | None = None) -> dict:
    quote = m.group(0)
    start = p["char_start"] + m.start()
    # the page the figure is printed on, which differs from the passage's first page when it runs over a page
    page = (page_at(spans, start) if spans else None) or p["page"]
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
        "notes": f"page {page}; entry offset {start}",
    }
    if year:
        f["as_of_year"] = year
    return f


def extract(p: dict, place_id: str | None, spans: list[dict] | None = None, before: str = "") -> list[dict]:
    """Rule facts in a passage. `spans` is the entry's page map (DP-02), for the page of each figure;
    `before` is the entry's text before the passage (a table's census year is stated above it)."""
    t, out = p["text"], []

    def mk(*a, **k):
        return fact(*a, **k, spans=spans)

    for m in COORD.finditer(t):
        lat = int(m.group(1)) + int(m.group(2)) / 60
        lon = int(m.group(3)) + int(m.group(4)) / 60
        if 5 <= lat <= 38 and 60 <= lon <= 100:  # sanity: inside the subcontinent
            out.append(mk(place_id, "coordinates", {"lat": round(lat, 4), "lon": round(lon, 4), "quality": "heading"},
                          p, m, 0.95))
    taken: set[int] = set()  # start offsets of figures already used, so two patterns never give one figure twice
    for rx, conf in ((AREA, 0.9), (AREA_ACRES, 0.8), (AREA2, 0.7)):
        for m in rx.finditer(t):
            if m.start(1) in taken:
                continue
            taken.add(m.start(1))
            unit = "sq_miles" if m.group(2).lower().startswith("sq") else "acres"
            out.append(mk(place_id, "area", {"number": num(m.group(1)), "unit": unit}, p, m, conf))
    taken = set()
    for cm in CLAUSE.finditer(t):
        clause = cm.group(0)
        if not POP_WORDS.search(clause):
            continue
        for rx, gn, gy in POP_PAIRS:
            for m in rx.finditer(clause):
                n, year = num(m.group(gn)), int(m.group(gy))
                if n >= 10 and not (1800 <= n <= 1950 and "," not in m.group(gn)) and m.start(gn) not in taken:
                    taken.add(m.start(gn))
                    out.append(mk(place_id, "population", {"number": n, "unit": "persons"}, p, _Shift(m, cm.start()), 0.9, year))
        years = set(re.findall(r"\b" + YEAR + r"\b", clause))
        census_year = int(years.pop()) if len(years) == 1 and re.search(r"\bc[eo]nsus\b", clause, re.IGNORECASE) else None
        for rx in POP_COUNTS:
            for m in rx.finditer(clause):
                n = num(m.group(1))
                if n < 10 or (1800 <= n <= 1950 and "," not in m.group(1)) or m.start(1) in taken:
                    continue
                taken.add(m.start(1))
                out.append(mk(place_id, "population", {"number": n, "unit": "persons"}, p, _Shift(m, cm.start()),
                              0.85 if census_year else 0.8, census_year))
    for m in TABLE_ROW.finditer(t):
        area, pop, dens = num(m.group(2)), num(m.group(5)), int(m.group(6))
        years = CENSUS_YEAR.findall(before + " " + t[:m.start()])
        if not years or not area or pop < 1000 or abs(pop / area - dens) > 0.02 * dens:
            continue
        for ftype, value, year in (("area", {"number": area, "unit": "sq_miles"}, None),
                                   ("population", {"number": pop, "unit": "persons"}, int(years[-1]))):
            f = mk(place_id, ftype, value, p, m, 0.8, year)
            f["notes"] += f"; table row: {m.group(1)}"
            out.append(f)
    for m in DISTANCE.finditer(t):
        out.append(mk(place_id, "distance", {"miles": num(m.group(1)), "relation": m.group(2).lower(), "to": m.group(3)}, p, m, 0.85))
    for m in HEIGHT.finditer(t):
        out.append(mk(place_id, "height", {"number": num(m.group(1)), "unit": "feet"}, p, m, 0.9))
    for m in ADMIN.finditer(t):
        out.append(mk(place_id, "admin_link", {"subdivision": m.group(1)}, p, m, 0.85))
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
        if f["type"] == "population" and f.get("as_of_year"):  # yearless counts describe different tracts
            scope = f["place_id"] if f["place_id"] != "pl_unlinked" else f["evidence"][0]["passage_id"]
            scope += f["notes"].partition("table row: ")[2]  # each row of a table is its own place
            by.setdefault((scope, f.get("as_of_year")), []).append(f)
    return [{"place_id": k[0], "year": k[1], "values": sorted({x["value"]["number"] for x in v}),
             "fact_ids": [x["fact_id"] for x in v], "quotes": [x["evidence"][0]["quote"] for x in v]}
            for k, v in by.items() if len({x["value"]["number"] for x in v}) > 1]


def lookback_scope(entries: list[dict]) -> dict[str, object]:
    """What the text before a passage runs back through: a table's census year is stated above it, sometimes
    in the section before (a side-note heading can fall between), so for a section it is the whole chapter;
    for a gazetteer entry it is the entry alone."""
    return {e["entry_id"]: ("chapter", e.get("chapter")) if e["kind"] == "section" else e["entry_id"] for e in entries}


def run(source_id: str) -> list[dict]:
    d = INTERIM_DIR / "classify" / source_id
    passages = read_jsonl(d / "passages.jsonl")
    by_entry = {e: p["place_id"] for p in read_jsonl(d / "places.jsonl") for e in p["entry_ids"]}
    entries = read_jsonl(INTERIM_DIR / "segment" / source_id / "entries.jsonl")
    spans = {e["entry_id"]: e["page_spans"] for e in entries}
    scope = lookback_scope(entries)
    facts, before = [], {}
    for p in passages:
        e = p["entry_id"]
        k = scope.get(e, e)
        facts += extract(p, by_entry.get(e), spans.get(e), before.get(k, "")[-2000:])
        before[k] = before.get(k, "") + "\n\n" + p["text"]
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
