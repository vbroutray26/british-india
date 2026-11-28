"""DP-15 assemble: curated bundle for the site, and its checks (TS-DATA-05, TS-DATA-09, TS-DATA-10)."""

from __future__ import annotations

import copy

from pipeline import assemble as asm

TEXT = "Bānpur.—A village in the Khurda subdivision, 3 miles north-west of the station, an area of 575 acres."
SRC = {"source_id": "omalley-puri-1908", "title": "Bengal District Gazetteers: Puri", "author": "L. S. S. O'Malley",
       "year": 1908, "credit_line": "O'Malley (1908).", "scan_ref": "https://example.org/manifest.json",
       "rights_basis": "public-domain"}


def _inputs():
    places = [
        {"place_id": "pl_puri-district-080c", "type": "district", "status": "existing", "entry_ids": [],
         "names": [{"text": "Purī", "lang": "en", "script": "Latn", "kind": "primary", "source_id": "s"}],
         "classify": {"rule": "x", "confidence": 1.0}, "review": {"status": "unreviewed"}},
        {"place_id": "pl_khurda-subdivision-40c0", "type": "subdivision", "status": "existing", "entry_ids": ["en_k"],
         "names": [{"text": "Khurdā subdivision", "lang": "en", "script": "Latn", "kind": "primary", "source_id": "s"}],
         "classify": {"rule": "x", "confidence": 1.0}, "review": {"status": "unreviewed"}},
        {"place_id": "pl_banpur-1111", "type": "village", "status": "existing", "entry_ids": ["en_b"],
         "names": [{"text": "Bānpur", "lang": "en", "script": "Latn", "kind": "primary", "source_id": "s"}],
         "classify": {"rule": "x", "confidence": 0.95}, "review": {"status": "unreviewed"}},
    ]
    entries = [
        {"entry_id": "en_b", "kind": "gazetteer", "heading": "Bānpur", "chapter": "XVI", "page_start": "233",
         "page_end": "233", "source_id": "omalley-puri-1908", "text": TEXT, "page_spans": []},
        {"entry_id": "en_k", "kind": "gazetteer", "heading": "Khurdā subdivision", "chapter": "XVI",
         "page_start": "269", "page_end": "270", "source_id": "omalley-puri-1908", "text": "x", "page_spans": []},
    ]
    passages = [{"passage_id": "ps_b_00", "entry_id": "en_b", "char_start": 0, "char_end": len(TEXT), "text": TEXT,
                 "page": "233", "page_end": "233", "lang": "en"}]
    i = TEXT.index("area of 575 acres")
    facts = [
        {"fact_id": "ft_a", "place_id": "pl_banpur-1111", "type": "area", "value": {"number": 575, "unit": "acres"},
         "evidence": [{"passage_id": "ps_b_00", "quote": "area of 575 acres", "char_start": i, "char_end": i + 17}],
         "method": "rule", "confidence": 0.9, "review": {"status": "unreviewed"}, "notes": "page 233; entry offset 9"},
        {"fact_id": "ft_u", "place_id": "pl_unlinked", "type": "area", "value": {"number": 575, "unit": "acres"},
         "evidence": [{"passage_id": "ps_b_00", "quote": "area of 575 acres", "char_start": i, "char_end": i + 17}],
         "method": "rule", "confidence": 0.9, "review": {"status": "unreviewed"}, "notes": "page 233; entry offset 9"},
    ]
    j = TEXT.index("Khurda subdivision")
    attrs = [
        {"fact_id": "ft_c", "place_id": "pl_banpur-1111", "type": "coordinates",
         "value": {"lat": 19.9, "lon": 85.2, "quality": "heading"},
         "evidence": [{"passage_id": "ps_b_00", "quote": "x", "char_start": 0, "char_end": 1}], "notes": "page 233"},
        {"fact_id": "ft_l", "place_id": "pl_banpur-1111", "type": "admin_link", "value": {"subdivision": "Khurda"},
         "evidence": [{"passage_id": "ps_b_00", "quote": "Khurda subdivision", "char_start": j, "char_end": j + 18}],
         "notes": "page 233"},
    ]
    return places, facts, attrs, passages, entries


def _bundle():
    return asm.bundle(*_inputs(), SRC)


def test_only_facts_linked_to_a_place_are_published():
    b = _bundle()
    assert [f["fact_id"] for f in b["facts"]] == ["ft_a"]


def test_fact_carries_the_page_its_figure_is_printed_on():
    f = _bundle()["facts"][0]
    assert f["page"] == "233" and "notes" not in f


def test_interim_fields_are_dropped_from_places():
    for p in _bundle()["places"]:
        assert "entry_ids" not in p and "classify" not in p


def test_heading_coordinates_become_the_place_geometry():
    p = next(p for p in _bundle()["places"] if p["place_id"] == "pl_banpur-1111")
    assert p["geometry"] == {"kind": "point", "coordinates": [85.2, 19.9], "quality": "heading", "source": "ft_c"}


def test_admin_link_and_district_give_parents():
    places = {p["place_id"]: p for p in _bundle()["places"]}
    assert places["pl_banpur-1111"]["parent_ids"] == ["pl_khurda-subdivision-40c0"]
    assert places["pl_khurda-subdivision-40c0"]["parent_ids"] == ["pl_puri-district-080c"]
    assert places["pl_puri-district-080c"]["child_ids"] == ["pl_khurda-subdivision-40c0"]


def test_entries_name_their_place_and_source():
    e = {x["entry_id"]: x for x in _bundle()["entries"]}
    assert e["en_b"]["place_id"] == "pl_banpur-1111" and e["en_b"]["source_id"] == "omalley-puri-1908"
    assert "text" not in e["en_b"]


def test_a_valid_bundle_has_no_errors():
    assert asm.check(_bundle()) == []


def test_dangling_references_are_errors():
    b = _bundle()
    b["facts"][0]["evidence"][0]["passage_id"] = "ps_missing"
    b["passages"][0]["entry_id"] = "en_missing"
    errs = asm.check(b)
    assert any("ps_missing" in e for e in errs) and any("en_missing" in e for e in errs)


def test_quote_must_sit_at_its_offsets():
    b = _bundle()
    b["facts"][0]["evidence"][0]["char_start"] += 3
    assert any("quote" in e for e in asm.check(b))


def test_schema_errors_are_reported():
    b = copy.deepcopy(_bundle())
    b["places"][0]["type"] = "galaxy"
    assert any("places" in e and "galaxy" in e for e in asm.check(b))


def test_unclassified_places_are_held_back_until_reviewed():
    places, facts, attrs, passages, entries = _inputs()
    places[2]["type"] = "uncertain"
    b = asm.bundle(places, facts, attrs, passages, entries, SRC)
    assert "pl_banpur-1111" not in {p["place_id"] for p in b["places"]}
    assert b["facts"] == [] and next(e for e in b["entries"] if e["entry_id"] == "en_b")["place_id"] is None
    assert b["held"] == ["pl_banpur-1111"]
    assert asm.check(b) == []


def test_headquarters_subdivision_resolves_from_the_subdivisions_own_entry():
    places, facts, attrs, passages, entries = _inputs()
    places[1]["names"][0]["text"] = "Purī subdivision"
    entries[1]["text"] = "Purī Subdivision.—Headquarters subdivision of the district, lying between 19° 28′"
    attrs[1]["value"] = {"subdivision": "headquarters"}
    b = asm.bundle(places, facts, attrs, passages, entries, SRC)
    assert next(p for p in b["places"] if p["place_id"] == "pl_banpur-1111")["parent_ids"] == ["pl_khurda-subdivision-40c0"]


def test_verified_llm_facts_go_to_their_entrys_place():
    places, facts, attrs, passages, entries = _inputs()
    i = TEXT.index("3 miles north-west of the station")
    llm_fact = {"fact_id": "ft_llm1", "entry_id": "en_b", "type": "railway", "value": {"label": "station", "vocab": "new-term"},
                "evidence": [{"passage_id": "ps_b_00", "quote": "3 miles north-west of the station", "char_start": i, "char_end": i + 33}],
                "method": "llm", "model": "m", "prompt_version": "extract-v1", "run_id": "extract-v1:m", "confidence": 0.9,
                "review": {"status": "unreviewed"}, "page": "233"}
    b = asm.bundle(places, facts, attrs, passages, entries, SRC, llm_facts=[llm_fact])
    f = next(x for x in b["facts"] if x["fact_id"] == "ft_llm1")
    assert f["place_id"] == "pl_banpur-1111" and "entry_id" not in f and f["method"] == "llm"
    assert asm.check(b) == []
