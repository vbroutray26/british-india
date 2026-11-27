"""DP-01b Second read: an independent OCR engine to check every printed number (D-24).

The existing OCR (Tesseract, archive.org) misreads about one figure in five (GS-OCR, D-23). A second engine
with different failure modes, Apple Vision, reads each full-resolution page. DP-07 then accepts a number in
a fact only if the second read found the same figure on the same page; otherwise the fact is queued for
review with the reason. On the GS-OCR pages, figures both engines agree on are right 96% of the time,
against 79% for Tesseract alone. Neither engine reads fractions (4¼ comes out as "44"), so agreement is a
filter, not proof.

The raw Vision output is cached per leaf in the private raw repo (`ocr_vision/leaf_NNNN.json`), so the
stage reruns anywhere; only leaves without a cache need macOS (`tools/vision_ocr.swift`).

Usage: python -m pipeline.second_read --source omalley-puri-1908
"""

from __future__ import annotations

import argparse
import itertools
import json
import platform
import re
import shutil
import statistics
import subprocess
from pathlib import Path

from rapidfuzz import fuzz

from pipeline.util import INTERIM_DIR, RAW_DIR, log, read_jsonl, write_jsonl
from pipeline.verify import numbers_in

LG = log("DP-01b")
TOOL = Path(__file__).resolve().parent.parent / "tools" / "vision_ocr.swift"
BIN = Path(__file__).resolve().parent.parent / ".build" / "vision_ocr"
ENGINE = "Apple Vision VNRecognizeTextRequest (accurate, en-US, no language correction)"

# Vision has no macron model: it returns umlauts, breves or acutes for ā ī ū.
_MACRONS = str.maketrans({"ä": "ā", "ă": "ā", "â": "ā", "à": "ā", "á": "ā", "ï": "ī", "î": "ī", "í": "ī",
                          "ü": "ū", "û": "ū", "ú": "ū", "Ä": "Ā", "Ă": "Ā", "Á": "Ā", "Ï": "Ī", "Í": "Ī",
                          "Ü": "Ū", "Ú": "Ū"})
_DECIMAL = re.compile(r"(?<=\d)[:.•∙·°](?=\d)")  # the book prints decimals with a raised point


def fix_chars(t: str) -> str:
    return _DECIMAL.sub("·", t.translate(_MACRONS))


def page_numbers(text: str) -> set[str]:
    """Figures on a page in DP-07's form: commas dropped, decimal point as '.'."""
    return set(numbers_in(_DECIMAL.sub(".", text)))


def _columns(lines: list[dict], w: int) -> str:
    top = statistics.median(sorted(ln["y0"] for ln in lines)[:3])
    out = []
    for left in (True, False):
        col = [ln for ln in lines if ((ln["x0"] + ln["x1"]) / 2 < w / 2) == left]
        out += [ln["t"] for ln in sorted(col, key=lambda ln: ln["y0"])
                if ln["y0"] > top + 5 or not re.fullmatch(r"[\dA-Z .,]+", ln["t"])]
    return "\n".join(out)


def _layout(rec: dict) -> dict | None:
    """Body lines, margin-note groups and line height of a single-column page; None for a page without
    full-width lines (the index), which is read as two columns."""
    w = rec["w"]
    lines = [ln for ln in rec["lines"] if ln["t"].strip()]
    longs = [ln for ln in lines if ln["x1"] - ln["x0"] > 0.45 * w]
    if len(longs) < 5:
        return None
    bx0, bx1 = statistics.median(ln["x0"] for ln in longs), statistics.median(ln["x1"] for ln in longs)
    top, bottom = min(ln["y0"] for ln in longs), max(ln["y1"] for ln in longs)
    lh = statistics.median(ln["y1"] - ln["y0"] for ln in longs)
    body, notes = [], []
    for ln in lines:
        if ln["y1"] < top - 0.3 * lh or (ln["y0"] > bottom + 1.5 * lh and len(ln["t"]) <= 4):
            continue
        if ln["x1"] < bx0 + 0.02 * w:
            notes.append(("L", ln))
        elif ln["x0"] > bx1 - 0.02 * w:
            notes.append(("R", ln))
        else:
            body.append(ln)
    groups: list[tuple[str, list[dict]]] = []
    for side, ln in sorted(notes, key=lambda n: (n[0], n[1]["y0"])):
        if groups and groups[-1][0] == side and ln["y0"] - groups[-1][1][-1]["y1"] < 0.8 * lh:
            groups[-1][1].append(ln)
        else:
            groups.append((side, [ln]))
    # Line pitch (distance between consecutive line centres). Vision's boxes are often taller than the pitch,
    # so fragments of one printed line are grouped by the pitch, not by the box height.
    cs = sorted((ln["y0"] + ln["y1"]) / 2 for ln in longs)
    gaps = [b - a for a, b in itertools.pairwise(cs) if b - a > 0.2 * lh]
    pitch = statistics.median(gaps) if gaps else lh
    return {"body": body, "groups": groups, "lh": lh, "pitch": min(lh, pitch)}


def margin_notes(rec: dict) -> list[dict]:
    """Side-notes (O'Malley's margin headings) with their top as a fraction of the page height, for DP-02."""
    lay = _layout(rec)
    if not lay:
        return []
    out = [{"t": fix_chars(" ".join(x["t"] for x in ls)), "y_frac": round(ls[0]["y0"] / rec["h"], 4)}
           for _, ls in lay["groups"]]
    return sorted((n for n in out if len(n["t"]) >= 3), key=lambda n: n["y_frac"])


def _rows(lay: dict) -> list[dict]:
    """Body fragments joined into printed lines (same vertical centre within half a line height)."""
    rows: list[dict] = []
    for ln in sorted(lay["body"], key=lambda ln: ln["y0"] + ln["y1"]):
        c = (ln["y0"] + ln["y1"]) / 2
        if rows and abs(c - rows[-1]["c"]) < 0.4 * lay["pitch"]:
            rows[-1]["f"].append(ln)
        else:
            rows.append({"c": c, "f": [ln], "L": "", "R": ""})
    for r in rows:
        r["f"].sort(key=lambda f: f["x0"])
    return rows


def body_rows(rec: dict) -> list[dict]:
    """Printed body lines of a single-column page, margin notes left out: text, top and height as fractions of
    the page height, and whether the line is indented (a paragraph start)."""
    lay = _layout(rec)
    if not lay:
        return []
    rows = _rows(lay)
    xs = [r["f"][0]["x0"] for r in rows]
    full = [r["f"][-1]["x1"] - r["f"][0]["x0"] > 0.45 * rec["w"] for r in rows]  # table rows and short lines are not
    page_x = statistics.median([x for x, f in zip(xs, full, strict=True) if f] or xs)

    def indented(k: int) -> bool:
        # against the neighbouring full-width lines (page skew drifts the margin; a table's rows start
        # anywhere); paragraph indents measure 3-4.5% of the page width and ordinary lines stay within 2%
        near = [xs[i] for i in [*range(max(0, k - 4), k), *range(k + 1, min(len(xs), k + 5))] if full[i]]
        return xs[k] - (statistics.median(near) if near else page_x) > 0.025 * rec["w"]

    return [{"t": fix_chars(" ".join(f["t"] for f in r["f"])),
             "y_frac": round(min(f["y0"] for f in r["f"]) / rec["h"], 4),
             "h_frac": round(max(f["y1"] - f["y0"] for f in r["f"]) / rec["h"], 4),
             "indent": indented(k)} for k, r in enumerate(rows)]


def _fold(s: str) -> str:
    from pipeline.ocr import fold

    return " ".join(fold(s).split())


def _align(a: list[str], b: list[str], thr: float) -> list[tuple[int, int]]:
    """Order-preserving best match of lines a to lines b (each pair at least `thr` similar)."""
    n, m = len(a), len(b)
    sc = [[fuzz.ratio(x, y) for y in b] for x in a]
    best = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            v = max(best[i + 1][j], best[i][j + 1])
            if sc[i][j] >= thr:
                v = max(v, best[i + 1][j + 1] + sc[i][j])
            best[i][j] = v
    pairs, i, j = [], 0, 0
    while i < n and j < m:
        if sc[i][j] >= thr and best[i][j] == best[i + 1][j + 1] + sc[i][j]:
            pairs.append((i, j))
            i, j = i + 1, j + 1
        elif best[i + 1][j] >= best[i][j + 1]:
            i += 1
        else:
            j += 1
    return pairs


def geometry(first: list[str], rows: list[dict], thr: float = 60, rematch: float = 75) -> dict[int, tuple[float | None, bool]]:
    """Corrections to first-OCR line geometry from the second read: {index: (y_frac or None, indent)}.
    The hOCR's boxes are unreliable where a side-note is glued onto a line (its left edge moves out,
    faking or hiding an indent), and it stores some lines out of order; the second read separates
    side-notes by position. But its own rows sometimes merge a short line with the start of the next (the
    row's first fragment, and so its indent, is still the matched line's), so it is trusted narrowly: the
    indent of every line matched in order, and both position and indent of a line the hOCR stored out of
    order (left over by the in-order match and closely like a left-over second-read line). y_frac is None
    where the hOCR position stands."""
    a, b = [_fold(t) for t in first], [_fold(r["t"]) for r in rows]
    pairs = _align(a, b, thr)
    free = set(range(len(rows))) - {j for _, j in pairs}

    def start_row(i: int, j: int) -> int:
        # where the hOCR merged two printed lines, the indent is the one of the row its start matches
        if j - 1 in free and fuzz.ratio(a[i][:30], b[j - 1][:30]) > fuzz.ratio(a[i][:30], b[j][:30]) + 20:
            return j - 1
        return j

    out: dict[int, tuple[float | None, bool]] = {i: (None, rows[start_row(i, j)]["indent"]) for i, j in pairs}
    def like(i: int, j: int) -> float:  # whole line, or its opening (the hOCR may have merged it with the next)
        return max(fuzz.ratio(a[i], b[j]), fuzz.ratio(a[i][:40], b[j][:40]) - 15 if len(b[j]) >= 40 else 0)

    for i in sorted(set(range(len(first))) - {i for i, _ in pairs}):
        best = max(free, key=lambda j: like(i, j), default=None)
        if best is not None and like(i, best) >= rematch:
            out[i] = (rows[best]["y_frac"], rows[best]["indent"])
            free.discard(best)
    return out


def first_word_fixes(first: list[str], rows: list[dict], thr: float = 60) -> dict[int, tuple[str, bool]]:
    """First words the first OCR cut short at the left edge ("pulation" for "population"), restored from the
    second read's matching line: {index of first-OCR line: (word, second read's indent)}. Only letters, and only when the second
    read's word ends with the first OCR's (1-3 letters lost)."""
    out = {}
    for i, j in _align([_fold(t) for t in first], [_fold(r["t"]) for r in rows], thr):
        a, b = (first[i].split() or [""])[0], (rows[j]["t"].split() or [""])[0]
        ka, kb = re.sub(r"\W+$", "", a), re.sub(r"\W+$", "", b)
        if (ka.isalpha() and kb.isalpha() and ka[:1].islower() and len(ka) >= 3
                and 1 <= len(kb) - len(ka) <= 3 and _fold(kb).endswith(_fold(ka))):
            out[i] = (kb + a[len(ka):], rows[j]["indent"])
    return out


FOOTNOTE = re.compile(r"\s*[•*†‡§¶]")  # footnotes start with a reference mark


def missing_lines(first: list[str], rows: list[dict], page_text: str | None = None,
                  thr: float = 60, min_len: int = 12) -> list[tuple[int, dict]]:
    """Body lines the second read has and the first OCR dropped, as (index of the first-OCR line to insert
    after, -1 for before the first, row). Lines are aligned by text; a second-read line counts as dropped only
    where the first OCR has nothing at all between the two matched lines around it (a line it read badly is
    left alone), and only if its text is nowhere else on the first OCR's page. Footnotes (smaller type) are
    not recovered into the body."""
    if not first or not rows:
        return []
    h_med = statistics.median(r["h_frac"] for r in rows)
    rows = [r for r in rows if r["h_frac"] >= 0.8 * h_med]
    pairs = _align([_fold(t) for t in first], [_fold(r["t"]) for r in rows], thr)
    if not pairs:
        return []
    page = _fold(page_text if page_text is not None else " ".join(first))
    steps = [b["y_frac"] - a["y_frac"] for a, b in itertools.pairwise(rows)]
    step = statistics.median(steps) if steps else 1.0

    def present(t: str) -> bool:  # also with the end cut off: Vision may glue a side-note onto the line
        f = _fold(t)
        return fuzz.partial_ratio(f, page) >= 85 or fuzz.partial_ratio(f[:int(len(f) * 0.75)], page) >= 85

    out = []
    for (i0, j0), (i1, j1) in zip([(-1, -1), *pairs], [*pairs, (len(first), len(rows))]):
        if i1 != i0 + 1:
            continue
        prev = rows[j0] if j0 >= 0 else None
        for r in rows[j0 + 1:j1]:
            if prev and j1 == len(rows) and r["y_frac"] - prev["y_frac"] > 1.6 * step:
                break  # below a gap after the last matched line: footnotes
            prev = r
            if len(r["t"]) >= min_len and not FOOTNOTE.match(r["t"]) and not present(r["t"]):
                out.append((i0, r))
    return out


def assemble(rec: dict) -> str:
    """Page text from Vision's line boxes, in the reading order of the GS-OCR conventions: running head and
    signature marks dropped, fragments of one printed line joined left to right, margin notes joined and
    placed at the start (left margin) or end (right margin) of the line they begin beside; a page without
    full-width lines (the index) is read as two columns."""
    if not any(ln["t"].strip() for ln in rec["lines"]):
        return ""
    lay = _layout(rec)
    if lay is None:
        return fix_chars(_columns([ln for ln in rec["lines"] if ln["t"].strip()], rec["w"]))
    rows = _rows(lay)
    for side, ls in lay["groups"]:
        c = (ls[0]["y0"] + ls[0]["y1"]) / 2
        row = min(rows, key=lambda r: abs(r["c"] - c))
        row[side] = (row[side] + " " + " ".join(x["t"] for x in ls)).strip()
    out = []
    for r in rows:
        text = " ".join(f["t"] for f in r["f"])
        out.append(" ".join(x for x in (r["L"], text, r["R"]) if x))
    return fix_chars("\n".join(out))


def _binary() -> Path | None:
    if platform.system() != "Darwin" or not shutil.which("swiftc"):
        return None
    if not BIN.exists() or BIN.stat().st_mtime < TOOL.stat().st_mtime:
        BIN.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["swiftc", "-O", str(TOOL), "-o", str(BIN)], check=True)
    return BIN


def read_leaves(images: list[Path], cache: Path, batch: int = 40) -> int:
    """Run Vision on page images and cache one JSON per leaf. Returns the number read."""
    exe = _binary()
    if exe is None:
        LG.warning("Vision OCR needs macOS with swiftc; %d leaves left without a second read", len(images))
        return 0
    cache.mkdir(parents=True, exist_ok=True)
    done = 0
    for i in range(0, len(images), batch):
        res = subprocess.run([str(exe), *map(str, images[i:i + batch])], check=True, capture_output=True, text=True)
        for line in res.stdout.splitlines():
            rec = json.loads(line)
            if "error" in rec:
                LG.warning("%s: %s", rec["file"], rec["error"])
                continue
            rec["file"] = Path(rec["file"]).name
            (cache / rec["file"].replace(".jpg", ".json")).write_text(json.dumps(rec, ensure_ascii=False))
            done += 1
    return done


def run(source_id: str, raw_dir: Path = RAW_DIR, out_dir: Path = INTERIM_DIR / "ocr2") -> list[dict]:
    first = read_jsonl(INTERIM_DIR / "ocr" / source_id / "pages.jsonl")
    full, cache = raw_dir / source_id / "pages_full", raw_dir / source_id / "ocr_vision"
    todo = [full / f"leaf_{p['leaf']:04d}.jpg" for p in first
            if not (cache / f"leaf_{p['leaf']:04d}.json").exists() and (full / f"leaf_{p['leaf']:04d}.jpg").exists()]
    if todo:
        LG.info("reading %d leaves with Vision", read_leaves(todo, cache))
    rows, missing = [], []
    for p in first:
        f = cache / f"leaf_{p['leaf']:04d}.json"
        if not f.exists():
            missing.append(p["leaf"])
            continue
        rec = json.loads(f.read_text())
        text = assemble(rec)
        rows.append({"leaf": p["leaf"], "page": p["page"], "engine": ENGINE, "text": text,
                     "numbers": sorted(page_numbers(text)), "margin": margin_notes(rec)})
    write_jsonl(out_dir / source_id / "pages.jsonl", rows)
    if missing:
        LG.warning("%d leaves have no second read (no full-resolution image): %s", len(missing), missing[:20])
    LG.info("second read: %d leaves", len(rows))
    return rows


def load(source_id: str, out_dir: Path = INTERIM_DIR / "ocr2") -> dict[str, set[str]]:
    """Printed page -> figures the second read found there. Empty if the stage has not run."""
    path = out_dir / source_id / "pages.jsonl"
    if not path.exists():
        return {}
    return {r["page"]: set(r["numbers"]) for r in read_jsonl(path) if r["page"]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--resume", action="store_true", help="accepted for CLI uniformity; the stage is always resumable")
    run(ap.parse_args(argv).source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
