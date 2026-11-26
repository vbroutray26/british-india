"""DP-05 Vocabulary tagging (spec §8.6).

Tags passages with controlled-vocabulary terms (crops, trade items, industries, calamities, monuments,
festivals). Matching is on folded text (diacritics stripped, lowercase) with word boundaries, and
tolerates OCR italic garbling of a final letter ("pujd" for "pujā"). Tags are low-confidence candidates
for DP-06 to confirm; they are not facts.

Output: data/interim/vocab/<source_id>/tags.jsonl  {passage_id, entry_id, category, term, surface, start, end}
Usage: python -m pipeline.vocab --source omalley-puri-1908
"""
from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

from pipeline.ocr import fold
from pipeline.util import INTERIM_DIR, REPO_ROOT, log, read_jsonl, read_yaml, write_jsonl

LG = log("DP-05")
VOCAB = REPO_ROOT / "pipeline" / "vocab" / "vocab.yaml"


def compile_vocab(path: Path = VOCAB) -> list[tuple[str, str, re.Pattern]]:
    out = []
    for cat, terms in read_yaml(path).items():
        for term, spellings in terms.items():
            alts = sorted({fold(s) for s in spellings}, key=len, reverse=True)
            rx = re.compile(r"(?<![\w-])(?:" + "|".join(re.escape(a) for a in alts) + r")(?![\w-])")
            out.append((cat, term, rx))
    return out


def tag(passage: dict, vocab: list[tuple[str, str, re.Pattern]]) -> list[dict]:
    t = fold(passage["text"])  # NFKD folding can change length only for combining marks; recompute spans below
    same_len = len(t) == len(passage["text"])
    tags = []
    for cat, term, rx in vocab:
        for m in rx.finditer(t):
            tags.append({"passage_id": passage["passage_id"], "entry_id": passage["entry_id"], "category": cat,
                         "term": term, "surface": passage["text"][m.start():m.end()] if same_len else m.group(0),
                         "start": m.start() if same_len else None, "end": m.end() if same_len else None})
    return tags


def run(source_id: str) -> list[dict]:
    vocab = compile_vocab()
    passages = read_jsonl(INTERIM_DIR / "classify" / source_id / "passages.jsonl")
    tags = [t for p in passages for t in tag(p, vocab)]
    write_jsonl(INTERIM_DIR / "vocab" / source_id / "tags.jsonl", tags)
    LG.info("%d tags in %d passages: %s", len(tags), len({t["passage_id"] for t in tags}),
            dict(Counter(t["category"] for t in tags)))
    return tags


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--resume", action="store_true")
    run(ap.parse_args(argv).source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
