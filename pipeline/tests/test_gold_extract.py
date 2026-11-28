"""GS-EXTRACT: label checks and the TS-DATA-04 scorer."""

from __future__ import annotations

from pipeline import gold_extract as ge
from pipeline.util import read_jsonl


def _row(**facts_over):
    fact = {"type": "festival", "value": {"label": "Makar Sankrānti"}, "year": None, "page": "233",
            "quote": "Oriyā pilgrims gather here on the Makar Sankrānti day in January"}
    fact.update(facts_over)
    return {"gold_id": "gse-x-001", "source_id": "x", "heading": "Atri", "entry_type": "village",
            "pages": ["233"], "facts": [fact], "labeller": "claude", "method": "page image",
            "labelled_on": "2026-11-27", "review": {"reviewer": "owner", "status": "pending"}}


def test_valid_row_passes():
    assert ge.check_row(_row()) == []


def test_unknown_type_is_rejected():
    # area and population are rule facts (DP-04, GS-NUMERIC), not DP-06 types
    assert any("type" in e for e in ge.check_row(_row(type="area")))


def test_empty_quote_is_rejected():
    assert any("quote" in e for e in ge.check_row(_row(quote=" ")))


def test_year_must_be_printed_in_quote():
    # "Do not infer years": a labelled year must appear in its quote
    assert any("year" in e for e in ge.check_row(_row(type="admin_change", year=1886,
                                                      quote="In 1885 it was decided that Government should retain")))
    assert ge.check_row(_row(type="admin_change", year=1885, value={"label": "Government control"},
                             quote="In 1885 it was decided that Government should retain")) == []


def test_number_in_value_must_be_in_quote():
    assert any("number" in e for e in ge.check_row(_row(value={"label": "fair of 300 stalls"})))


def test_page_must_be_one_of_the_entry_pages():
    assert any("page" in e for e in ge.check_row(_row(page="240")))


def test_match_same_type_overlapping_quote():
    g = [{"type": "temple", "year": None, "quote": "It contains a temple dedicated to Bhagavatī, the presiding deity"}]
    c = [{"type": "temple", "year": None, "quote": "a temple dedicated to Bhagavati"}]
    assert ge.match_facts(g, c) == [(0, 0)]


def test_match_needs_same_type_and_year():
    g = [{"type": "temple", "year": None, "quote": "a temple dedicated to Bhagavatī"}]
    assert ge.match_facts(g, [{"type": "festival", "year": None, "quote": "a temple dedicated to Bhagavatī"}]) == []
    g = [{"type": "admin_change", "year": 1885, "quote": "In 1885 it was decided that Government should retain"}]
    c = [{"type": "admin_change", "year": 1876, "quote": "In 1885 it was decided that Government should retain"}]
    assert ge.match_facts(g, c) == []


def test_match_is_one_to_one():
    g = [{"type": "road", "year": None, "quote": "situated on the Trunk Road"}]
    c = [{"type": "road", "year": None, "quote": "situated on the Trunk Road"}] * 2
    assert ge.match_facts(g, c) == [(0, 0)]


def test_score_facts_per_type_and_unsupported():
    text = "It contains a temple dedicated to Bhagavatī. It lies on the Trunk Road."
    gold = [{"type": "temple", "year": None, "quote": "a temple dedicated to Bhagavatī"},
            {"type": "road", "year": None, "quote": "on the Trunk Road"}]
    cands = [{"type": "temple", "year": None, "quote": "a temple dedicated to Bhagavati"},
             {"type": "temple", "year": None, "quote": "a second temple to Siva by the tank"}]
    s = ge.score_facts([(gold, cands, text)])
    assert s["by_type"]["temple"] == {"tp": 1, "fp": 1, "fn": 0, "precision": 0.5, "recall": 1.0}
    assert s["by_type"]["road"]["recall"] == 0.0
    assert s["unsupported"] == 1 and s["unsupported_rate"] == 0.5


def test_gold_file_rows_pass_checks():
    rows = read_jsonl(ge.GOLD)
    assert rows, "GS-EXTRACT has no rows"
    assert len({r["gold_id"] for r in rows}) == len(rows)
    for r in rows:
        assert ge.check_row(r) == [], r["gold_id"]


def test_the_prompts_worked_examples_are_left_out_of_scoring(tmp_path):
    import json

    cands = tmp_path / "c.jsonl"
    cands.write_text("")
    res = ge.score("omalley-puri-1908", cands, prompt_version="extract-v1")
    assert res["held_out_examples"] == ["gse-omalley-001", "gse-omalley-005", "gse-omalley-009"]
    assert res["labelled_entries"] == len([r for r in read_jsonl(ge.GOLD) if r["source_id"] == "omalley-puri-1908"]) - 3
    assert json.dumps(res)  # serialisable
