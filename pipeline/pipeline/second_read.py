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
import json
import platform
import re
import shutil
import statistics
import subprocess
from pathlib import Path

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
    return {"body": body, "groups": groups, "lh": lh}


def margin_notes(rec: dict) -> list[dict]:
    """Side-notes (O'Malley's margin headings) with their top as a fraction of the page height, for DP-02."""
    lay = _layout(rec)
    if not lay:
        return []
    out = [{"t": fix_chars(" ".join(x["t"] for x in ls)), "y_frac": round(ls[0]["y0"] / rec["h"], 4)}
           for _, ls in lay["groups"]]
    return sorted((n for n in out if len(n["t"]) >= 3), key=lambda n: n["y_frac"])


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
    lh = lay["lh"]
    rows: list[dict] = []
    for ln in sorted(lay["body"], key=lambda ln: ln["y0"] + ln["y1"]):
        c = (ln["y0"] + ln["y1"]) / 2
        if rows and abs(c - rows[-1]["c"]) < 0.5 * lh:
            rows[-1]["f"].append(ln)
        else:
            rows.append({"c": c, "f": [ln], "L": "", "R": ""})
    for side, ls in lay["groups"]:
        c = (ls[0]["y0"] + ls[0]["y1"]) / 2
        row = min(rows, key=lambda r: abs(r["c"] - c))
        row[side] = (row[side] + " " + " ".join(x["t"] for x in ls)).strip()
    out = []
    for r in rows:
        text = " ".join(f["t"] for f in sorted(r["f"], key=lambda f: f["x0"]))
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
