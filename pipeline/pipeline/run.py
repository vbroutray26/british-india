"""Run pipeline stages in order for one source.

  python -m pipeline.run --source omalley-puri-1908               # DP-01..DP-07 (no network)
  python -m pipeline.run --source omalley-puri-1908 --acquire     # also DP-00 first
"""
from __future__ import annotations

import argparse

from pipeline import acquire, classify, ocr, rules, segment, verify, vocab

STAGES = [("DP-01 ocr", ocr.run), ("DP-02 segment", segment.segment), ("DP-03 classify", classify.run),
          ("DP-04 rules", rules.run), ("DP-05 vocab", vocab.run), ("DP-07 verify", verify.run)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--acquire", action="store_true")
    a = ap.parse_args(argv)
    if a.acquire:
        acquire.acquire(a.source)
    for _name, fn in STAGES:
        fn(a.source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
