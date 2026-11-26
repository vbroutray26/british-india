"""DP-02 Segment into entries (spec §8.3).

Builds one continuous text for the source with a page map, then splits it:
  - Gazetteer chapter (place entries): a new entry starts at a paragraph whose opening matches
    "Heading.—" (e.g. "Baral.—A village in the Puri subdivision…").
  - Other chapters: a new section starts at each chapter heading and each side-note heading.

Output: data/interim/segment/<source_id>/entries.jsonl
  {entry_id, source_id, kind: gazetteer|section, chapter, heading_raw, heading, page_start, page_end,
   text, page_spans:[{page, start, end}], ocr_confidence}

entry_id is derived from source + heading + first page, so it is stable across reruns (FR-TEXT-06).

Usage: python -m pipeline.segment --source omalley-puri-1908
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path

from rapidfuzz import fuzz

from pipeline.ocr import fold
from pipeline.util import CONFIG_DIR, INTERIM_DIR, log, read_jsonl, read_yaml, sha256_text, write_jsonl

LG = log("DP-02")

# Entry heading: 1–5 capitalised words (allowing diacritics, apostrophes, brackets), then ".—" or "—".
# OCR often renders the em dash as "—", "--", "-" or "~", and may drop the full stop.
ENTRY_HEAD = re.compile(
    r"^(?P<h>(?:[A-Z][\w’'()\-]*\.?)(?:\s+(?:[A-Z(][\w’'()\-]*\.?|of|and|or|the)){0,5})\s?\.?\s?(?:—|--|–|~|-\s)\s?"
)
CHAPTER_HEAD = re.compile(r"^CHAPTER\s+(?P<num>[IVXLC1l]+)\.?", re.IGNORECASE)


@dataclass
class Para:
    text: str
    page: str | None
    leaf: int
    conf: float
    margin: list[str] = field(default_factory=list)


def load_paragraphs(pages: list[dict]) -> list[Para]:
    """Paragraphs in reading order. A page's first paragraph continues the previous page's last
    paragraph unless its first line is indented."""
    paras: list[Para] = []
    for pg in pages:
        if not pg["words"]:
            continue
        chunks = [c for c in pg["text_clean"].split("\n\n") if c.strip()]
        first_indented = bool(pg["lines"] and pg["lines"][0]["indent"])
        notes = [m["t"] for m in pg["margin"]]
        for i, c in enumerate(chunks):
            if i == 0 and paras and not first_indented and not CHAPTER_HEAD.match(c):
                prev = paras[-1]
                sep = "" if prev.text.endswith("-") else " "
                prev.text = prev.text.rstrip("-") + sep + c if prev.text.endswith("-") and c[:1].islower() else prev.text + sep + c
                prev.margin += notes if i == 0 else []
                # remember that this paragraph also spans this page
                prev.__dict__.setdefault("more_pages", []).append((pg["page"], pg["leaf"], len(prev.text) - len(c)))
                continue
            paras.append(Para(text=c, page=pg["page"], leaf=pg["leaf"], conf=pg["confidence"],
                              margin=notes if i == 0 else []))
    return paras


# A line that opens an entry: up to ~45 characters, then a dash, then the descriptor "A …"/"An …"/"The …".
# OCR noise is tolerated: "Atri.—aA village", "? maacak—A ruined temple".
ANCHOR = re.compile(r"^(?P<h>.{1,45}?)\s?[.,]?\s?(?:—|--|–|~|-)\s?(?:a|\?)?(?P<d>[A-Z][a-z]*)\b")
# Fallback when OCR lost the heading and the dash: an indented line that opens with a place descriptor.
WEAK = re.compile(r"\b(village|town|estate|hill|lake|river|temple|ghat|cave|subdivision|port|market)\b", re.IGNORECASE)


def find_anchors(lines: list[dict], expected: list[str]) -> list[tuple[int, str, float]]:
    """Align the ordered list of expected headings to anchor lines, keeping alphabetical order.

    Returns (line_index, expected_heading, score) per heading found. A heading is matched to the best
    fuzzy candidate that comes after the previous match; when OCR has garbled a heading beyond
    recognition, the single remaining candidate between two confident neighbours is taken.
    """
    cands = [(i, m.group("h")) for i, ln in enumerate(lines) if (m := ANCHOR.match(ln["t"]))]
    weak = [(i, ln["t"][:20]) for i, ln in enumerate(lines)
            if ln["indent"] and not ANCHOR.match(ln["t"]) and WEAK.search(ln["t"][:50])]
    score = lambda h, c: fuzz.ratio(fold(h), fold(re.sub(r"[^\w\s]", "", c)).strip())
    # Pass 1: confident matches in order.
    found: dict[int, tuple[int, float]] = {}
    pos = -1
    for k, h in enumerate(expected):
        # earliest strong match after the previous heading (entries are in alphabetical order)
        best = next(((ci, sc) for ci, c in cands if ci > pos and (sc := score(h, c)) >= 80), None)
        if best:
            found[k] = best
            pos = best[0]
    # Pass 2: fill gaps between confident neighbours with the best (or only) structural candidate.
    for k, h in enumerate(expected):
        if k in found:
            continue
        lo = max((found[j][0] for j in found if j < k), default=-1)
        hi = min((found[j][0] for j in found if j > k), default=len(lines))
        # Structural evidence counts when the spelling is garbled: indented line, "A/An/The" descriptor.
        def combined(ci: int, c: str, h: str = h) -> float:
            m = ANCHOR.match(lines[ci]["t"])
            return score(h, c) + (20 if lines[ci]["indent"] else 0) + (20 if m and m.group("d") in ("A", "An", "The") else 0)
        between = [(ci, combined(ci, c)) for ci, c in cands if lo < ci < hi]
        between = [b for b in between if b[1] >= 55]
        if not between:  # heading destroyed by OCR: take a descriptor line in the gap, marked low-confidence
            between = [(ci, 0.0) for ci, _ in weak if lo < ci < hi][:1]
        if between:
            ci, sc = max(between, key=lambda t: t[1])
            found[k] = (ci, round(score(h, next(c for i, c in cands if i == ci)) if any(i == ci for i, _ in cands) else 0, 1))
    return sorted(((ci, expected[k], sc) for k, (ci, sc) in found.items()), key=lambda t: t[0])


def segment_gazetteer(pages: list[dict], expected: list[str]) -> tuple[list[dict], list[str]]:
    """Split the gazetteer chapter at the anchor line of each expected heading."""
    lines = []
    for pg in pages:
        for ln in pg["lines"]:
            lines.append({**ln, "page": pg["page"], "conf": pg["confidence"]})
    anchors = find_anchors(lines, expected)
    missing = [h for h in expected if h not in {a[1] for a in anchors}]
    out = []
    for n, (li, heading, sc) in enumerate(anchors):
        end = anchors[n + 1][0] if n + 1 < len(anchors) else len(lines)
        chunk = lines[li:end]
        m = ANCHOR.match(chunk[0]["t"])
        out.append({"heading": heading, "heading_raw": m.group("h") if m else chunk[0]["t"][:20],
                    "match_score": round(sc, 1), "lines": chunk})
    return out, missing


def lines_to_text(lines: list[dict]) -> tuple[str, list[dict]]:
    """Join lines into text (paragraph breaks at indents, hyphen repair) with page spans."""
    from pipeline.ocr import join_lines
    text, spans, para = "", [], []

    def flush():
        nonlocal text
        if not para:
            return
        piece = join_lines([l["t"] for l in para], set())
        if text:
            text += "\n\n"
        start = len(text)
        text += piece
        # attribute characters to pages proportionally to their line lengths
        total = sum(len(l["t"]) + 1 for l in para) or 1
        acc = start
        for l in para:
            share = round((len(l["t"]) + 1) / total * len(piece))
            if spans and spans[-1]["page"] == l["page"]:
                spans[-1]["end"] = min(len(text), acc + share)
            else:
                spans.append({"page": l["page"], "start": acc, "end": min(len(text), acc + share)})
            acc += share
        spans[-1]["end"] = len(text)
        para.clear()

    for i, l in enumerate(lines):
        if l["indent"] and i > 0:
            flush()
        para.append(l)
    flush()
    return text, spans


def clean_heading(h: str) -> str:
    h = re.sub(r"[\s.—–~-]+$", "", h.strip())
    return re.sub(r"\s+", " ", h)


def segment(source_id: str, in_dir: Path = INTERIM_DIR / "ocr", out_dir: Path = INTERIM_DIR / "segment") -> list[dict]:
    cfg = read_yaml(CONFIG_DIR / "segment.yaml")["sources"][source_id]
    pages = read_jsonl(in_dir / source_id / "pages.jsonl")
    body = [p for p in pages if p["page"] and cfg["first_page"] <= int(p["page"]) <= cfg["last_page"]]
    gz_first, gz_last = cfg["gazetteer_pages"]
    expected = cfg.get("gazetteer_headings")
    if expected:  # headings come from the checked list; chapters before the gazetteer are split by sections
        gz_pages = [p for p in body if gz_first <= int(p["page"]) <= gz_last]
        body = [p for p in body if int(p["page"]) < gz_first]
    paras = load_paragraphs(body)

    entries: list[dict] = []
    cur: dict | None = None
    chapter = None

    def start(kind: str, heading_raw: str, para: Para) -> dict:
        return {"kind": kind, "chapter": chapter, "heading_raw": heading_raw, "heading": clean_heading(heading_raw),
                "paras": [], "confs": []}

    for para in paras:
        m_ch = CHAPTER_HEAD.match(para.text)
        if m_ch:
            chapter = m_ch.group("num").upper().replace("L", "I").replace("1", "I")
        in_gz = para.page is not None and gz_first <= int(para.page) <= gz_last
        m = ENTRY_HEAD.match(para.text) if in_gz else None
        if m and len(m.group("h")) <= 60 and not m_ch:
            cur = start("gazetteer", m.group("h"), para)
            entries.append(cur)
        elif not in_gz and (m_ch or para.margin or cur is None or cur["kind"] == "gazetteer"):
            heading = para.margin[0] if para.margin else (para.text.split(".")[0][:80] if m_ch else "(untitled)")
            cur = start("section", heading, para)
            entries.append(cur)
        elif cur is None:
            cur = start("section", "(front)", para)
            entries.append(cur)
        cur["paras"].append(para)
        cur["confs"].append(para.conf)

    rows = []
    seen: dict[str, int] = {}
    gz_rows, missing = [], []
    if expected:
        gz_chunks, missing = segment_gazetteer(gz_pages, expected)
        for c in gz_chunks:
            text, spans = lines_to_text(c["lines"])
            gz_rows.append({"kind": "gazetteer", "chapter": "XVI", "heading_raw": c["heading_raw"], "heading": c["heading"],
                            "text": text, "spans": spans, "conf": sum(l["conf"] for l in c["lines"]) / len(c["lines"]),
                            "match_score": c["match_score"]})
        if missing:
            LG.warning("headings not found: %s", ", ".join(missing))

    def make_id(heading: str, first_page: str) -> str:
        key = f"{fold(heading)}|{first_page}"
        n = seen.get(key, 0)
        seen[key] = n + 1
        return "en_" + source_id.split("-")[0] + "_" + sha256_text(source_id, key, str(n))[:10]

    for e in entries:
        text, spans = "", []
        for para in e["paras"]:
            if text:
                text += "\n\n"
            base = len(text)
            text += para.text
            pts = [(para.page, 0)] + [(pg, off) for pg, _leaf, off in para.__dict__.get("more_pages", [])]
            for k, (pg, off) in enumerate(pts):
                end = pts[k + 1][1] if k + 1 < len(pts) else len(para.text)
                if spans and spans[-1]["page"] == pg:
                    spans[-1]["end"] = base + end
                else:
                    spans.append({"page": pg, "start": base + off, "end": base + end})
        pages_in = [s["page"] for s in spans]
        entry_id = make_id(e["heading"], pages_in[0])
        rows.append({
            "entry_id": entry_id,
            "source_id": source_id,
            "kind": e["kind"],
            "chapter": e["chapter"],
            "heading_raw": e["heading_raw"],
            "heading": e["heading"],
            "page_start": pages_in[0],
            "page_end": pages_in[-1],
            "page_spans": spans,
            "text": text,
            "ocr_confidence": round(sum(e["confs"]) / len(e["confs"]), 1),
        })
    for g in gz_rows:
        pages_in = [s["page"] for s in g["spans"]]
        rows.append({
            "entry_id": make_id(g["heading"], pages_in[0]), "source_id": source_id, "kind": "gazetteer",
            "chapter": "XVI", "heading_raw": g["heading_raw"], "heading": g["heading"],
            "page_start": pages_in[0], "page_end": pages_in[-1], "page_spans": g["spans"], "text": g["text"],
            "ocr_confidence": round(g["conf"], 1), "heading_match": g["match_score"],
        })
    write_jsonl(out_dir / source_id / "entries.jsonl", rows)
    if missing:
        write_jsonl(out_dir / source_id / "missing_headings.jsonl", [{"heading": h} for h in missing])
    gz = [r for r in rows if r["kind"] == "gazetteer"]
    LG.info("%d records: %d gazetteer entries, %d sections", len(rows), len(gz), len(rows) - len(gz))
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--resume", action="store_true")
    segment(ap.parse_args(argv).source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
