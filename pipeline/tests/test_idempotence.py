"""TS-DATA-11: rerunning stages on unchanged input produces byte-identical output.
Runs only where the private raw data is checked out (not in public CI)."""
import hashlib

import pytest

from pipeline import classify, ocr, rules, segment, vocab
from pipeline.util import INTERIM_DIR, RAW_DIR

SRC = "omalley-puri-1908"
pytestmark = pytest.mark.skipif(not (RAW_DIR / SRC).exists(), reason="private raw data not present")


def digest():
    return {p.relative_to(INTERIM_DIR).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(INTERIM_DIR.rglob("*.jsonl")) if SRC in p.as_posix()}


def run_all():
    ocr.run(SRC); segment.segment(SRC); classify.run(SRC); rules.run(SRC); vocab.run(SRC)


def test_rerun_is_byte_identical():
    run_all()
    first = digest()
    run_all()
    assert digest() == first and first
