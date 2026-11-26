from pathlib import Path

import yaml

from pipeline import DATA_DIR
from pipeline.validate import main

GOOD_SOURCE = {
    "source_id": "test-source-1900",
    "title": "Test",
    "year": 1900,
    "language": "en",
    "acquired_from": "https://example.org",
    "ocr_origin": "pending",
    "licence_stated": "none stated",
    "rights_basis": "public-domain",
    "credit_line": "Test credit",
    "status": "candidate",
}
GOOD_MEDIA = {
    "media_id": "md_test-1",
    "type": "photo",
    "source_url": "https://example.org/img",
    "licence_stated": "none",
    "rights_basis": "public-domain",
    "credit_line": "Credit",
    "alt_text": {"en": "Alt", "or": "", "hi": ""},
    "caption": {"en": "Cap", "or": "", "hi": ""},
    "file": "img.jpg",
    "status": "active",
}


def _write(tmp: Path, sources: list, media: list) -> Path:
    (tmp / "sources.yaml").write_text(yaml.safe_dump({"version": 1, "sources": sources}))
    (tmp / "media.yaml").write_text(yaml.safe_dump({"version": 1, "media": media}))
    return tmp


def test_repo_registers_are_valid():
    assert main(["--data-dir", str(DATA_DIR)]) == 0


def test_valid_registers_pass(tmp_path):
    assert main(["--data-dir", str(_write(tmp_path, [GOOD_SOURCE], [GOOD_MEDIA]))]) == 0


def test_media_without_credit_fails(tmp_path):
    bad = {**GOOD_MEDIA, "credit_line": ""}
    assert main(["--data-dir", str(_write(tmp_path, [GOOD_SOURCE], [bad]))]) == 1


def test_media_without_english_alt_fails(tmp_path):
    bad = {**GOOD_MEDIA, "alt_text": {"en": "", "or": "", "hi": ""}}
    assert main(["--data-dir", str(_write(tmp_path, [GOOD_SOURCE], [bad]))]) == 1


def test_unclear_rights_requires_acceptance(tmp_path):
    bad = {**GOOD_MEDIA, "rights_basis": "unclear"}
    assert main(["--data-dir", str(_write(tmp_path, [GOOD_SOURCE], [bad]))]) == 1
    ok = {**bad, "accepted_by": "owner", "accepted_on": "2026-11-26"}
    assert main(["--data-dir", str(_write(tmp_path, [GOOD_SOURCE], [ok]))]) == 0


def test_duplicate_source_ids_fail(tmp_path):
    assert main(["--data-dir", str(_write(tmp_path, [GOOD_SOURCE, GOOD_SOURCE], []))]) == 1
