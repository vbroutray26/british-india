"""Numeral review queue (D-36): what is queued, crops, and turning answers into audited corrections."""

from __future__ import annotations

import yaml

from pipeline import review_numerals as rn


def _vis(*rows):
    """The second read's lines for the page, already in reading order."""
    return list(rows)


def _rec(lines, **kw):
    rec = {"page": "42", "leaf": 60, "size": [1000, 1600], "lines": lines, "margin": [], "footnotes": []}
    rec.update(kw)
    return rec


def _reasons(items):
    return {it["text"]: it["reasons"] for it in items}


def test_lines_without_figures_are_not_queued():
    rec = _rec([{"t": "The temple stands on the edge of a deep pool", "y": 100}])
    assert rn.page_items(rec, _vis("The temple stands on the edge of a deep pool")) == []


def test_figures_both_engines_agree_on_are_not_queued():
    t = "the rent-roll is Rs. 8,000 per annum, and the area"
    assert rn.page_items(_rec([{"t": t, "y": 100}]), _vis(t)) == []


def test_engines_differ_on_a_figure():
    rec = _rec([{"t": "Statistics of rainfall, 20; vital, 195-127;", "y": 100}])
    items = rn.page_items(rec, _vis("Statistics of rainfall, 20; vital, 125-127;"))
    assert _reasons(items) == {"Statistics of rainfall, 20; vital, 195-127;": ["engines differ"]}


def test_second_read_missing_the_line():
    rec = _rec([{"t": "a plot of land, measuring 548 acres, was acquired", "y": 100},
                {"t": "at a cost of Rs. 2,120, in addition to 29 acres", "y": 130}])
    items = rn.page_items(rec, _vis("a plot of land, measuring 548 acres, was acquired"))
    assert _reasons(items) == {"at a cost of Rs. 2,120, in addition to 29 acres": ["no second-read line"]}


def test_recovered_lines_are_one_engine_reads():
    rec = _rec([{"t": "Savings Bank transactions, 197.", "y": 100, "recovered": True}])
    items = rn.page_items(rec, _vis("Savings Bank transactions, 197."))
    assert items[0]["reasons"] == ["one engine only"]


def test_suspect_characters_beside_figures():
    # both engines read it, but "Ist" and "5:2" are typical misreadings of 1st and 5·2
    for t in ("came into force from the Ist July 1906.", "not more than 5:2 inches fell in September,"):
        items = rn.page_items(_rec([{"t": t, "y": 100}]), _vis(t))
        assert items and items[0]["reasons"] == ["suspect characters"], t


def test_every_index_line_with_figures_is_queued():
    rec = _rec([{"t": "Seko, 196.", "y": 100}, {"t": "Tangri, 157.", "y": 100, "col": 1}])
    items = rn.page_items(rec, None)
    assert {it["text"]: it["reasons"][0] for it in items} == {"Seko, 196.": "index", "Tangri, 157.": "index"}


def test_pages_in_the_index_range_are_index_even_unsplit():
    # DP-01 splits only some index pages into columns; the rest still read across both columns
    rec = _rec([{"t": "Arts ond industries, 180-188.", "y": 100}])
    assert rn.page_items(rec, _vis(), index=True)[0]["reasons"] == ["index"]


def test_footnotes_and_margin_notes_with_figures():
    rec = _rec([], footnotes=["Kings of Khurda, J.A.S.B., 1808, p. 383.", "Ibid."],
               margin=[{"t": "es 2) eee", "y": 400}, {"t": "Rainfall.", "y": 500}])
    items = rn.page_items(rec, _vis())
    assert _reasons(items) == {"Kings of Khurda, J.A.S.B., 1808, p. 383.": ["footnote"],
                               "es 2) eee": ["margin note"]}


def test_find_is_the_text_before_the_merge_and_corrected_lines_are_skipped():
    rec = _rec([{"t": "vital, 125-127;", "first_read": "vital, 195-127;", "y": 100},
                {"t": "Puri ... ... 1,528 1 1,889 658,048 431", "y": 130, "corrected": True}])
    items = rn.page_items(rec, _vis("vital, 125-128;"))
    assert [(it["text"], it["find"]) for it in items] == [("vital, 125-127;", "vital, 195-127;")]


def test_item_ids_are_stable():
    rec = _rec([{"t": "Seko, 196.", "y": 100, "col": 1}])
    assert rn.page_items(rec, None)[0]["id"] == rn.page_items(rec, None)[0]["id"]


def test_crop_box_scales_to_the_image_and_stays_inside():
    box = rn.crop_box(y=800, pitch=40, ocr_size=(1000, 1600), img_size=(2400, 3840))
    assert box[0] == 0 and box[2] == 2400 and box[1] < 800 * 2.4 < box[3]
    top = rn.crop_box(y=5, pitch=40, ocr_size=(1000, 1600), img_size=(2400, 3840))
    assert top[1] == 0
    foot = rn.crop_box(y=None, pitch=40, ocr_size=(1000, 1600), img_size=(2400, 3840))
    assert foot[3] == 3840 and foot[1] > 3840 / 2


def test_answers_become_corrections_and_a_review_log():
    items = [{"id": "a", "page": "310", "leaf": 330, "kind": "line", "text": "Seko, 196.", "find": "Seko, 196.",
              "reasons": ["index"]},
             {"id": "b", "page": "310", "leaf": 330, "kind": "line", "text": "Tangri, 187.", "find": "Tangri, 157.",
              "reasons": ["index"]},
             {"id": "c", "page": "35", "leaf": 53, "kind": "margin", "text": "es 2) eee", "find": "es 2) eee",
              "reasons": ["margin note"]}]
    answers = {"a": "Seko, 195.", "b": "Tangri, 187.", "c": ""}
    corr, log = rn.answers_to_corrections(items, answers, by="owner", date="2026-11-28")
    # b was already right after the merge: confirmed, and pinned so a later change to the merge cannot undo it
    assert [(c["page"], c["find"], c["replace"]) for c in corr] == [
        ("310", "Seko, 196.", "Seko, 195."), ("310", "Tangri, 157.", "Tangri, 187."), ("35", "es 2) eee", "")]
    assert all(c["by"] == "owner" and c["review"] == "done" and "leaf" in c["evidence"] for c in corr)
    assert {r["id"]: r["status"] for r in log} == {"a": "corrected", "b": "confirmed", "c": "corrected"}


def test_confirmed_line_the_merge_did_not_touch_needs_no_correction():
    items = [{"id": "a", "page": "1", "leaf": 2, "kind": "line", "text": "x 1", "find": "x 1", "reasons": []}]
    corr, log = rn.answers_to_corrections(items, {"a": "x 1"}, by="owner", date="2026-11-28")
    assert corr == [] and log[0]["status"] == "confirmed"


def test_unanswered_items_are_left_out():
    items = [{"id": "a", "page": "1", "leaf": 2, "kind": "line", "text": "x 1", "find": "x 1", "reasons": []}]
    assert rn.answers_to_corrections(items, {}, by="owner", date="2026-11-28") == ([], [])


def test_corrections_are_appended_as_valid_yaml(tmp_path):
    f = tmp_path / "ocr_corrections.yaml"
    f.write_text('# header comment\nversion: 1\ncorrections:\n  - page: "61"\n    find: "a"\n    replace: "b"\n')
    rn.append_corrections(f, [{"page": "310", "find": 'Seko, 196. "x"', "replace": "Seko, 195.", "evidence": "e",
                                "by": "owner", "date": "2026-11-28", "review": "done"}])
    text = f.read_text()
    assert text.startswith("# header comment")
    data = yaml.safe_load(text)
    assert [c["find"] for c in data["corrections"]] == ["a", 'Seko, 196. "x"']
