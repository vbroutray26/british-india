"""DP-01 OCR and normalise (spec §8.2).

Reads the host's existing OCR (Tesseract hOCR from the Internet Archive), keeps per-word confidence,
maps scan leaves to printed page numbers, separates running heads, and writes one record per page:

  data/interim/ocr/<source_id>/pages.jsonl
    {source_id, leaf, page, running_head, lines:[{t, y, indent}], margin:[{t, y}], footnotes:[t],
     text_raw, text_clean, recovered, confidence, low_conf_words, words, flags}
  A line may also carry: recovered (from the second read, D-27), first_word / first_read (the hOCR's
  reading before a fix or merge from the second read, D-29, D-31), corrected (an audited correction was
  applied), col (1 = right column of a two-column page such as the index), table (a row of an inset
  table, read from the second read's cells; also recovered, D-32).

Layout (O'Malley district gazetteers): one text column; section headings printed as side-notes in the
outer margin; new paragraphs indented; footnotes in smaller type at the foot. Lines are re-sorted by
vertical position because the OCR emits them in block order.

Normalisation keeps the original spelling and diacritics; a folded form is computed later for search.
Re-OCR with ocrmypdf (spec §8.2 step 2) is only run when the measured CER on GS-OCR exceeds 3%.

Usage: python -m pipeline.ocr --source omalley-puri-1908
"""
from __future__ import annotations

import argparse
import html
import itertools
import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

from pipeline.util import DATA_DIR, INTERIM_DIR, RAW_DIR, log, read_yaml, write_json, write_jsonl

LG = log("DP-01")
LOW_CONF = 60          # word confidence below this is "low"
PAGE_REVIEW_CONF = 80  # pages whose mean word confidence is below this go to the review queue


@dataclass
class Line:
    words: list[tuple[str, int]] = field(default_factory=list)  # (text, confidence)
    bbox: tuple[int, int, int, int] = (0, 0, 0, 0)
    fsize: float = 0.0
    xs: list[tuple[int, int]] = field(default_factory=list)  # each word's left and right edge
    ys: list[tuple[int, int]] = field(default_factory=list)  # each word's top and bottom

    @property
    def text(self) -> str:
        return " ".join(w for w, _ in self.words)


@dataclass
class Page:
    index: int
    width: int = 0
    height: int = 0
    lines: list[Line] = field(default_factory=list)


def _title(attrs: dict) -> dict:
    out = {}
    for part in (attrs.get("title") or "").split(";"):
        part = part.strip()
        if part:
            k, _, v = part.partition(" ")
            out[k] = v
    return out


class HocrParser(HTMLParser):
    """Minimal streaming hOCR parser (stdlib only): pages → lines → words with confidence."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.pages: list[Page] = []
        self._line: Line | None = None
        self._word_conf: int | None = None
        self._word_fsize: float = 0.0
        self._word_x: tuple[int, int] = (0, 0)
        self._word_y: tuple[int, int] = (0, 0)
        self._buf: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "")
        t = _title(a)
        if cls == "ocr_page":
            box = [int(x) for x in t.get("bbox", "0 0 0 0").split()]
            self.pages.append(Page(index=len(self.pages), width=box[2], height=box[3]))
        elif cls == "ocr_line":
            box = tuple(int(x) for x in t.get("bbox", "0 0 0 0").split())
            self._line = Line(bbox=box)  # type: ignore[arg-type]
            self.pages[-1].lines.append(self._line)
        elif cls == "ocrx_word":
            self._word_conf = int(t.get("x_wconf", "0"))
            wb = [int(x) for x in t.get("bbox", "0 0 0 0").split()]
            self._word_x = (wb[0], wb[2])
            self._word_y = (wb[1], wb[3])
            self._word_fsize = float(t.get("x_fsize", "0") or 0)
            self._buf = []

    def handle_data(self, data):
        if self._word_conf is not None:
            self._buf.append(data)

    def handle_endtag(self, tag):
        if tag == "span" and self._word_conf is not None and self._line is not None:
            w = html.unescape("".join(self._buf)).strip()
            if w:
                self._line.words.append((w, self._word_conf))
                self._line.xs.append(self._word_x)
                self._line.ys.append(self._word_y)
                self._line.fsize = max(self._line.fsize, self._word_fsize)
            self._word_conf = None


# ---------------------------------------------------------------- normalisation

LIGATURES = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl", "ſ": "s", "æ": "ae", "Æ": "Ae"}
QUOTES = {"“": '"', "”": '"', "„": '"', "‘": "'", "’": "'", "‚": "'", "`": "'"}
DASHES = {"—": "—", "–": "–", "‒": "–", "―": "—"}  # keep em/en dashes (date ranges, headings)


def normalise_chars(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    for a, b in {**LIGATURES, **QUOTES, **DASHES}.items():
        s = s.replace(a, b)
    return re.sub(r"[ \t]+", " ", s)


def fold(s: str) -> str:
    """Search form: strip diacritics, lowercase (Jagannáth → jagannath). Display text keeps diacritics."""
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()


def join_lines(lines: list[str], hyphen_words: set[str]) -> str:
    """Join lines into paragraphs text, repairing end-of-line hyphenation.

    'disap-' + 'peared' → 'disappeared', unless the hyphenated form is attested elsewhere in the source
    ('sub-division' stays hyphenated when 'sub-division' appears mid-line somewhere in the book).
    """
    out = ""
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        if out.endswith("-") and not out.endswith("--"):
            m_prev = re.search(r"(\w+)-$", out)
            m_next = re.match(r"(\w+)", ln)
            if m_prev and m_next and m_next.group(1)[:1].islower():
                joined_hyphen = f"{m_prev.group(1)}-{m_next.group(1)}".lower()
                out = out[:-1] + ("-" if joined_hyphen in hyphen_words else "") + ln
                continue
        out = f"{out} {ln}" if out else ln
    return out


# ---------------------------------------------------------------- running heads and page numbers

def load_page_map(folder: Path) -> dict[int, str]:
    """leafNum (1-based, as in the host's page_numbers.json) → printed page number."""
    p = next(folder.glob("*_page_numbers.json"), None)
    if not p:
        return {}
    return {int(x["leafNum"]): x["pageNumber"] for x in json.loads(p.read_text())["pages"] if x.get("pageNumber")}


def detect_leaf_offset(pages: list[Page], page_map: dict[int, str]) -> int:
    """Find how hOCR page indices align with leafNum by checking where printed numbers appear in headers."""
    best, best_hits = 1, -1
    for offset in (0, 1, 2):
        hits = 0
        for p in pages:
            num = page_map.get(p.index + offset)
            if num and p.lines and any(re.search(rf"\b{re.escape(num)}\b", ln.text) for ln in p.lines[:2] + p.lines[-1:]):
                hits += 1
        if hits > best_hits:
            best, best_hits = offset, hits
    LG.info("leaf offset %d (%d pages confirm their printed number in the header/footer)", best, best_hits)
    return best


# e.g. "234 PURI." / "PHYSICAL ASPECTS. 3" — the page number is often misread ("o", "li"), so allow any short token.
RUNNING_HEAD = re.compile(r"^\s*(\S{1,3}\s+)?[A-Z][A-Za-z .,'’&-]{2,60}?[.,]?(\s+\S{1,3})?\s*$")


def split_running_head(p: Page, printed: str | None) -> tuple[str | None, list[Line]]:
    """The first line is a running head when it is short, mostly capitals, and/or carries the page number."""
    if not p.lines:
        return None, []
    first = p.lines[0].text
    near_top = p.lines[0].bbox[1] < p.height * 0.12 if p.height else True
    has_num = bool(printed and re.search(rf"\b{re.escape(printed)}\b", first))
    letters = [c for c in re.sub(r"\s+\S{1,3}$", "", first) if c.isalpha()]  # ignore a trailing misread number
    caps = sum(c.isupper() for c in letters) / max(1, len(letters))
    if near_top and len(first) <= 70 and (has_num or (caps > 0.7 and RUNNING_HEAD.match(first))):
        return first, p.lines[1:]
    # A head the OCR garbled ("D4 Punt, ;"), sometimes under a speck read as text: short lines at the top of
    # the page set off from the text below by a wider gap than the line spacing.
    k = 0
    while k < 2 and _set_off(p, k):
        k += 1
    if k:
        return " ".join(ln.text for ln in p.lines[:k]), p.lines[k:]
    return None, p.lines


def _set_off(p: Page, i: int) -> bool:
    if len(p.lines) < i + 3 or not p.height:
        return False
    a, b, c = (ln.bbox[1] for ln in p.lines[i:i + 3])
    t = p.lines[i].text.strip()
    return (a < p.height * 0.12 and len(t) <= 35 and not t.upper().startswith("CHAPTER")
            and c > b and b - a >= 1.4 * (c - b))


# ---------------------------------------------------------------- numeric safety

NUM = re.compile(r"\b\d{1,3}(?:,\d{3})+\b|\b\d+(?:\.\d+)?\b")


def numeric_flags(lines: list[Line]) -> list[str]:
    """Flag numerals that OCR read with low confidence, and digit/letter confusions (spec §8.2 'Number safety')."""
    flags = []
    for ln in lines:
        for w, c in ln.words:
            if any(ch.isdigit() for ch in w):
                if c < LOW_CONF:
                    flags.append(f"low-conf-number:{w}")
                if re.search(r"\d[OlIS]|[OlIS]\d", w):
                    flags.append(f"digit-letter-mix:{w}")
    return flags


# ---------------------------------------------------------------- layout

INDENT_MIN = 85  # px at scan resolution; paragraph indents measure ~120 px, skew drift up to ~60 px


def layout(lines: list[Line], page_w: int, page_h: int) -> dict:
    """Split lines into body / margin notes / footnotes and mark paragraph starts."""
    lines = [ln for ln in lines if ln.text.strip()]
    sizes_all = sorted(ln.fsize for ln in lines if ln.fsize)
    med_all = sizes_all[len(sizes_all) // 2] if sizes_all else 0
    # Specks: very short strings in tiny type are scan noise, not text.
    lines = [ln for ln in lines if not (len(ln.text.strip()) <= 2 and ln.fsize < med_all * 0.6)]
    lines = [piece for ln in lines for piece in split_jumps(ln, page_w)]
    if not lines:
        return {"body": [], "margin": [], "footnotes": []}
    cols = split_columns(lines, page_w)
    if cols:  # the index: the OCR runs each printed line across both columns
        return {"body": cols[0] + cols[1], "margin": [], "footnotes": [], "x0": None, "right": cols[1]}
    wide = [ln for ln in lines if (ln.bbox[2] - ln.bbox[0]) > page_w * 0.45]
    if not wide:  # plate, table or title page: keep everything as body, in reading order
        return {"body": sorted(lines, key=lambda l: (l.bbox[1], l.bbox[0])), "margin": [], "footnotes": [],
                "x0": None}
    xs0 = sorted(ln.bbox[0] for ln in wide)
    xs1 = sorted(ln.bbox[2] for ln in wide)
    col_x0, col_x1 = xs0[len(xs0) // 4], xs1[len(xs1) * 3 // 4]  # robust column edges
    body, margin = [], []
    for ln in lines:
        x0, _, x1, _ = ln.bbox
        if x1 < col_x0 - 20 or x0 > col_x1 + 20:
            margin.append(ln)
        else:
            body.append(ln)
    body.sort(key=lambda l: (l.bbox[1], l.bbox[0]))
    margin.sort(key=lambda l: l.bbox[1])
    # Footnotes: trailing lines in clearly smaller type in the bottom third, below a gap.
    sizes = sorted(ln.fsize for ln in body if ln.fsize)
    med = sizes[len(sizes) // 2] if sizes else 0
    foot: list[Line] = []
    while body and med and 0 < body[-1].fsize < med * 0.78 and body[-1].bbox[1] > page_h * 0.66:
        foot.insert(0, body.pop())
    return {"body": body, "margin": margin, "footnotes": foot, "x0": col_x0}


def split_jumps(ln: Line, page_w: int) -> list[Line]:
    """Split a line the OCR gathered from several printed lines (D-32): where a word jumps back left by more
    than a fifth of the page and down or up by more than half a word's height, a new line starts. Each piece
    gets the box of its own words, so it sorts into its printed place."""
    if len(ln.ys) != len(ln.words) or len(ln.xs) != len(ln.words) or len(ln.words) < 2:
        return [ln]
    hs = sorted(b - a for a, b in ln.ys)
    h = hs[len(hs) // 2]
    cuts = [k for k in range(1, len(ln.words)) if ln.xs[k][0] < ln.xs[k - 1][0] - 0.2 * page_w
            and abs(ln.ys[k][0] - ln.ys[k - 1][0]) > 0.5 * h]
    if not cuts:
        return [ln]
    out = []
    for a, b in itertools.pairwise([0, *cuts, len(ln.words)]):
        xs, ys = ln.xs[a:b], ln.ys[a:b]
        y0 = sorted(y for y, _ in ys)[len(ys) // 2]  # the median top: a stray mark does not move the line
        out.append(Line(words=ln.words[a:b], bbox=(min(x for x, _ in xs), y0, max(x for _, x in xs), y0 + h),
                        fsize=ln.fsize, xs=xs, ys=ys))
    return out


def cut_inset(lines: list[Line], insets: list[dict], page_w: int, page_h: int) -> list[Line]:
    """Body lines with the words of inset tables cut out (D-32): beside a table the OCR runs its cells into the
    wrapped text. Only the words right of the table (the text) are kept; the table is read from the second
    read's cells. Lines left empty are dropped."""
    out = []
    for ln in lines:
        c = (ln.bbox[1] + ln.bbox[3]) / 2 / page_h
        reg = next((r for r in insets if r["y0_frac"] <= c <= r["y1_frac"]), None)
        if reg is None or len(ln.xs) != len(ln.words):
            out.append(ln)
            continue
        keep = [k for k, (a, _) in enumerate(ln.xs) if a >= (reg["x_frac"] - 0.01) * page_w]
        if keep:
            xs = [ln.xs[k] for k in keep]
            out.append(Line(words=[ln.words[k] for k in keep], bbox=(xs[0][0], ln.bbox[1], xs[-1][1], ln.bbox[3]),
                            fsize=ln.fsize, xs=xs))
    return out


def shift_insets(insets: list[dict], body: list[Line], rows: list[dict], page_h: int) -> list[dict]:
    """Inset-table regions moved from the second read's page coordinates into the first OCR's: the two reads
    crop and scale the page differently, so a line sits a little higher or lower in one than in the other.
    The shift is the median, over the lines both read alike, of the difference in their tops."""
    from pipeline.second_read import _align, _fold

    pairs = _align([_fold(ln.text) for ln in body], [_fold(r["t"]) for r in rows], 80) if rows else []
    if not pairs:
        return insets
    d = sorted(body[i].bbox[1] / page_h - rows[j]["y_frac"] for i, j in pairs)[len(pairs) // 2]
    keys = ("y0_frac", "y1_frac", "first_frac")
    return [t | {k: t[k] + d for k in keys} for t in insets]


def inset_indent(x_left: int | None, inset: dict, page_w: int) -> bool:
    """Whether a line of the text wrapped beside an inset table is indented (a paragraph start): measured
    from the wrapped text's left edge. A line only the second read has (no hOCR box) is not."""
    return x_left is not None and x_left - inset["x_frac"] * page_w > INDENT_MIN


def _gutter(ln: Line, page_w: int) -> tuple[int, float] | None:
    """The widest gap between words of a line, as (index of the first word after it, gap centre), when wide
    enough to be a column gutter and near the middle of the page."""
    if len(ln.xs) != len(ln.words) or len(ln.xs) < 2:
        return None
    k = max(range(1, len(ln.xs)), key=lambda i: ln.xs[i][0] - ln.xs[i - 1][1])
    gap, mid = ln.xs[k][0] - ln.xs[k - 1][1], (ln.xs[k][0] + ln.xs[k - 1][1]) / 2
    return (k, mid) if gap >= 0.04 * page_w and 0.35 * page_w < mid < 0.65 * page_w else None


def _across(ln: Line, centre: float, page_w: int) -> int | None:
    """Index of the first word right of the gutter, for a line with a narrower gap where the gutter is."""
    if len(ln.xs) != len(ln.words):
        return None
    for k in range(1, len(ln.xs)):
        lo, hi = ln.xs[k - 1][1], ln.xs[k][0]
        if hi - lo >= 0.015 * page_w and lo - 0.01 * page_w <= centre <= hi + 0.01 * page_w:
            return k
    return None


def split_columns(lines: list[Line], page_w: int) -> tuple[list[Line], list[Line]] | None:
    """A two-column page (the index) whose lines the OCR joined across the gutter: (left column, right
    column), each in y order. None unless most lines show a gap at the same place near the middle of the page."""
    gut = {id(ln): g for ln in lines if (g := _gutter(ln, page_w))}
    many = [ln for ln in lines if len(ln.words) >= 2]
    if len(gut) < 5 or len(gut) < 0.4 * len(many):
        return None
    mids = sorted(m for _, m in gut.values())
    centre = mids[len(mids) // 2]
    if sum(abs(m - centre) <= 0.04 * page_w for m in mids) < 0.7 * len(mids):
        return None
    left: list[Line] = []
    right: list[Line] = []
    for ln in lines:
        g = gut.get(id(ln))
        k = g[0] if g and abs(g[1] - centre) <= 0.04 * page_w else _across(ln, centre, page_w)
        if k:
            for side, ws, xs in ((left, ln.words[:k], ln.xs[:k]), (right, ln.words[k:], ln.xs[k:])):
                side.append(Line(words=ws, bbox=(xs[0][0], ln.bbox[1], xs[-1][1], ln.bbox[3]), fsize=ln.fsize, xs=xs))
        else:
            (left if ln.bbox[0] < centre else right).append(ln)
    return sorted(left, key=lambda l: l.bbox[1]), sorted(right, key=lambda l: l.bbox[1])


def merge_margin(notes: list[Line]) -> list[dict]:
    """Join stacked side-note lines into one note each (lines less than ~1.6 line-heights apart)."""
    out: list[dict] = []
    for ln in notes:
        t = normalise_chars(ln.text).strip()
        if not t or len(t) < 2:
            continue
        if out and ln.bbox[1] - out[-1]["_y1"] < (ln.bbox[3] - ln.bbox[1]) * 1.6:
            out[-1]["t"] = join_lines([out[-1]["t"], t], set())
            out[-1]["_y1"] = ln.bbox[3]
        else:
            out.append({"t": t, "y": ln.bbox[1], "_y1": ln.bbox[3]})
    return [{"t": o["t"].rstrip(" ,.;:"), "y": o["y"]} for o in out]


def paragraphs(lines: list[dict], hyphen_words: set[str]) -> str:
    """Join lines into text with a blank line before each indented (paragraph-start) line."""
    paras: list[list[str]] = []
    for ln in lines:
        if ln["indent"] or not paras:
            paras.append([])
        paras[-1].append(ln["t"])
    return "\n\n".join(join_lines(p, hyphen_words) for p in paras)


def recover_lines(line_recs: list[dict], vision: Path, height: int, other: list[str]) -> list[str]:
    """Repair `line_recs` in place from the cached second read (DP-01b): restore first words the archive.org
    OCR cut short at the left edge (D-29), and insert body lines it dropped (D-27), in place of any fragments it
    kept of them. Returns the recovered texts. `other` is the page's text outside the body
    (footnotes, side-notes, running head), which is never recovered into it."""
    if not line_recs or not vision.exists():
        return []
    from pipeline.second_read import body_rows, first_word_fixes, geometry, missing_lines

    first, orig = [ln["t"] for ln in line_recs], list(line_recs)
    rows = body_rows(json.loads(vision.read_text()))
    for i, (w, _indent) in first_word_fixes(first, rows).items():
        line_recs[i]["t"] = w + line_recs[i]["t"][len(first[i].split()[0]):]
        line_recs[i]["first_word"] = first[i].split()[0]  # as the first OCR read it
    # Position and indent from the second read (D-30): lost letters or a glued side-note move the hOCR's left
    # edge, which fakes or hides a paragraph start, and the hOCR stores some lines out of order.
    for i, (y_frac, indent) in geometry(first, rows).items():
        line_recs[i]["indent"] = indent
        if y_frac is not None:
            line_recs[i]["y"] = int(y_frac * height)
    found = missing_lines(first, rows, " ".join(first + other))
    for i, r in reversed(found):
        line_recs.insert(i + 1, {"t": r["t"], "y": int(r["y_frac"] * height), "indent": r["indent"], "recovered": True})
    # Fragments the first OCR kept of the lines it dropped give way to the recovered lines (text_raw keeps them).
    gone = {id(orig[i]) for _, r in found for i in r.get("replaces", [])}
    line_recs[:] = [ln for ln in line_recs if id(ln) not in gone]
    line_recs.sort(key=lambda ln: (ln.get("col", 0), ln["y"]))  # stable: lines without a match keep their place among equals
    return [r["t"] for _, r in found]


def merge_reads(rows: list[dict], vision_dir: Path, hyphen_words: set[str]) -> int:
    """Merge the second read into each page's lines (D-31), judged by the words both engines agree on across
    the whole book. Figures are never taken from the second read. Lines recovered from it, lines with an
    audited correction and two-column pages are left alone. A merged line keeps the first OCR's reading in
    "first_read"; text_raw is unchanged. Returns the number of lines changed."""
    from pipeline.second_read import _align, _fold, agreed_words, body_rows, merge_line

    work = []
    for r in rows:
        f = vision_dir / f"leaf_{r['leaf']:04d}.json"
        if not r["lines"] or not f.exists() or any("col" in ln for ln in r["lines"]):
            continue
        vrows = body_rows(json.loads(f.read_text()))
        pairs = _align([_fold(ln["t"]) for ln in r["lines"]], [_fold(v["t"]) for v in vrows], 60) if vrows else []
        work.append((r, [(r["lines"][i], vrows[j]["t"]) for i, j in pairs]))
    vocab = agreed_words([(ln["t"], v) for _, pairs in work for ln, v in pairs])
    total = 0
    for r, pairs in work:
        n = 0
        for ln, v in pairs:
            if ln.get("recovered") or ln.get("corrected"):
                continue
            new = merge_line(ln["t"], v, vocab)
            if new != ln["t"]:
                ln["first_read"], ln["t"] = ln["t"], new
                n += 1
        if n:
            r["flags"].append(f"merged-lines:{n}")
            r["text_clean"] = paragraphs(r["lines"], hyphen_words)
            total += n
    LG.info("second read merged into %d lines (vocabulary of %d agreed words)", total, len(vocab))
    return total


# ---------------------------------------------------------------- stage

def run(source_id: str, raw_dir: Path = RAW_DIR, out_dir: Path = INTERIM_DIR / "ocr") -> list[dict]:
    from pipeline.second_read import body_rows, inset_tables

    folder = raw_dir / source_id
    hocr = next(folder.glob("*_hocr.html"))
    parser = HocrParser()
    parser.feed(hocr.read_text(encoding="utf-8"))
    pages = parser.pages
    page_map = load_page_map(folder)
    offset = detect_leaf_offset(pages, page_map)

    # Hyphenated forms attested mid-line anywhere in the book (used to decide line-end hyphen repair).
    hyphen_words: set[str] = set()
    for p in pages:
        for ln in p.lines:
            for w, _ in ln.words[:-1]:
                if re.fullmatch(r"[A-Za-z]+-[A-Za-z]+", w):
                    hyphen_words.add(w.lower())

    corrections = (read_yaml(DATA_DIR / "review" / source_id / "ocr_corrections.yaml") or {}).get("corrections", [])
    rows = []
    for p in pages:
        leaf = p.index + offset
        printed = page_map.get(leaf)
        lay = layout(p.lines, p.width, p.height)
        sorted_page = Page(index=p.index, width=p.width, height=p.height, lines=lay["body"])
        head, body = split_running_head(sorted_page, printed)
        text_raw = "\n".join(ln.text for ln in body)
        vision = folder / "ocr_vision" / f"leaf_{leaf:04d}.json"
        insets = [] if "right" in lay or not vision.exists() else inset_tables(json.loads(vision.read_text()))
        if insets:
            insets = shift_insets(insets, body, body_rows(json.loads(vision.read_text())), p.height)
            body = cut_inset(body, insets, p.width, p.height)
        x0 = lay.get("x0")
        # Indent is measured against neighbouring lines, so page skew does not look like an indent.
        line_recs, lefts = [], {}
        for i, ln in enumerate(body):
            near = [b.bbox[0] for b in body[max(0, i - 2):i + 3] if b is not ln] or [x0 or ln.bbox[0]]
            line_recs.append({"t": normalise_chars(ln.text), "y": ln.bbox[1],
                              "indent": bool(x0 is not None and ln.bbox[0] - min(near) > INDENT_MIN)})
            lefts[id(line_recs[-1])] = ln.bbox[0]
            if any(ln is r for r in lay.get("right", [])):
                line_recs[-1]["col"] = 1  # right column of a two-column page: read after the left
        recovered = [] if "right" in lay else recover_lines(line_recs, vision, p.height,
                                  [normalise_chars(ln.text) for ln in lay["footnotes"] + lay["margin"]] + [head or ""])
        for t in insets:  # D-32: the table's rows, read before the text wrapped beside it
            beside = [ln for ln in line_recs if (t["first_frac"] - 0.006) * p.height <= ln["y"] <= t["y1_frac"] * p.height]
            for ln in beside:  # measured from the wrapped text's own edge, not the column's
                ln["indent"] = inset_indent(lefts.get(id(ln)), t, p.width)
            # before the first wrapped line (the two reads place lines a few pixels apart)
            top = min([int(t["first_frac"] * p.height)] + [ln["y"] for ln in beside]) - len(t["rows"])
            line_recs += [{"t": r, "y": top + k, "indent": False, "recovered": True, "table": True}
                          for k, r in enumerate(t["rows"])]
            recovered += t["rows"]
        line_recs.sort(key=lambda ln: (ln.get("col", 0), ln["y"]))
        words = [c for ln in body for _, c in ln.words]
        conf = round(sum(words) / len(words), 1) if words else 0.0
        low = sum(1 for c in words if c < LOW_CONF)
        flags = numeric_flags(body)
        if words and conf < PAGE_REVIEW_CONF:
            flags.insert(0, "page-low-confidence")
        if not words:
            flags.insert(0, "blank-or-plate")
        applied = []
        for c in corrections:
            if str(c["page"]) == str(printed):
                for ln in line_recs:
                    if c["find"] in ln["t"]:
                        ln["t"] = ln["t"].replace(c["find"], c["replace"])
                        ln["corrected"] = True  # checked against the scan: the merge below leaves it alone
                        applied.append(c["find"])
        missed = [c["find"] for c in corrections if str(c["page"]) == str(printed) and c["find"] not in applied]
        if missed:
            flags.append("correction-not-applied:" + "|".join(missed))
        if applied:
            flags.append(f"ocr-corrected:{len(applied)}")
        if recovered:
            flags.append(f"recovered-lines:{len(recovered)}")
        rows.append({
            "source_id": source_id,
            "leaf": leaf,
            "page": printed or None,
            "running_head": normalise_chars(head) if head else None,
            "size": [p.width, p.height],  # OCR coordinate space, for cropping page images
            "lines": line_recs,
            "margin": merge_margin(lay["margin"]),
            "footnotes": [normalise_chars(ln.text) for ln in lay["footnotes"]],
            "text_raw": text_raw,
            "text_clean": paragraphs(line_recs, hyphen_words),
            "recovered": recovered,  # lines only the second read has (D-27); not in text_raw
            "confidence": conf,
            "words": len(words),
            "low_conf_words": low,
            "flags": flags,
        })
    merge_reads(rows, folder / "ocr_vision", hyphen_words)
    out = out_dir / source_id
    write_jsonl(out / "pages.jsonl", rows)
    stats = summary(rows)
    write_json(out / "stats.json", stats)
    LG.info("%d pages; mean conf %.1f; %d pages to review; %d numeric flags",
            stats["pages"], stats["mean_confidence"], stats["pages_to_review"], stats["numeric_flags"])
    return rows


def summary(rows: list[dict]) -> dict:
    text_pages = [r for r in rows if r["words"]]
    return {
        "pages": len(rows),
        "text_pages": len(text_pages),
        "mapped_pages": sum(1 for r in rows if r["page"]),
        "mean_confidence": round(sum(r["confidence"] for r in text_pages) / max(1, len(text_pages)), 1),
        "pages_to_review": sum(1 for r in rows if "page-low-confidence" in r["flags"]),
        "numeric_flags": sum(1 for r in rows for f in r["flags"] if f.startswith(("low-conf-number", "digit-letter"))),
        "flag_counts": dict(Counter(f.split(":")[0] for r in rows for f in r["flags"])),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--resume", action="store_true", help="stage is idempotent; reruns rewrite identical output")
    run(ap.parse_args(argv).source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
