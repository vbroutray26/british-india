from pipeline.ocr import Line, Page, fold, join_lines, layout, normalise_chars, split_running_head


def test_normalise_keeps_diacritics_and_fixes_ligatures():
    assert normalise_chars("Jagannáth ﬁeld “car”") == 'Jagannáth field "car"'


def test_fold_for_search():
    assert fold("Jagannáth Purī") == "jagannath puri"


def test_hyphen_repair_joins_broken_words():
    assert join_lines(["the waters dis-", "appeared quickly"], set()) == "the waters disappeared quickly"


def test_hyphen_kept_when_attested():
    assert join_lines(["the Khurda sub-", "division"], {"sub-division"}) == "the Khurda sub-division"


def test_hyphen_kept_before_capital():
    assert join_lines(["Bengal-", "Nagpur Railway"], set()) == "Bengal- Nagpur Railway"


def _ln(text, x0, y, x1=None, fs=100.0):
    return Line(words=[(w, 95) for w in text.split()], bbox=(x0, y, x1 or x0 + 2400, y + 80), fsize=fs)


def test_layout_separates_margin_notes_and_sorts_lines():
    lines = [_ln("second body line", 400, 800), _ln("first body line", 400, 700),
             _ln("Natural", 80, 700, 300, 60), _ln("divisions", 80, 760, 330, 60)]
    out = layout(lines, 3200, 5300)
    assert [l.text for l in out["body"]] == ["first body line", "second body line"]
    assert [l.text for l in out["margin"]] == ["Natural", "divisions"]


def test_running_head_with_misread_page_number():
    p = Page(index=0, width=3000, height=5000, lines=[_ln("PHYSICAL ASPECTS, o", 1000, 500, 2600), _ln("In the deltaic tract", 300, 700)])
    head, body = split_running_head(p, "3")
    assert head == "PHYSICAL ASPECTS, o" and [l.text for l in body] == ["In the deltaic tract"]


def test_recover_lines_inserts_a_dropped_line_in_reading_order(tmp_path):
    import json

    from pipeline.ocr import recover_lines
    text = ["The Puri Forest Division is situated entirely within the Khurda",
            "subdivision and consists of reserved and protected forests",
            "extending over an area of 485 square miles. The reserved",
            "forests contain 20 separate demarcated blocks having an area of",
            "113 square miles, while the protected forests comprise all"]
    vis = tmp_path / "leaf_0001.json"
    vis.write_text(json.dumps({"w": 2400, "h": 3600, "lines": [
        {"t": t, "conf": 1, "x0": 300, "y0": 400 + i * 80, "x1": 2100, "y1": 460 + i * 80} for i, t in enumerate(text)]}))
    recs = [{"t": text[0], "y": 600, "indent": False}, {"t": text[1], "y": 720, "indent": False},
            {"t": text[3], "y": 960, "indent": False}, {"t": text[4], "y": 1080, "indent": False}]
    assert recover_lines(recs, vis, 5400, []) == [text[2]]
    assert [r["t"] for r in recs] == text and recs[2]["recovered"]
    assert recover_lines([{"t": text[0], "y": 600, "indent": False}], tmp_path / "none.json", 5400, []) == []


def test_recover_lines_restores_a_cut_first_word_and_the_true_indent(tmp_path):
    import json

    from pipeline.ocr import recover_lines
    text = ["The first census of the district was taken in the year 1872, and",
            "the result was to show for the district, as now constituted, a",
            "population of 769,779 persons. During the next 10 years the",
            "population increased by no less than 15·4 per cent., being",
            "returned in 1881 at 888,592 souls, but it is probable that a"]
    vis = tmp_path / "leaf_0001.json"
    vis.write_text(json.dumps({"w": 2400, "h": 3600, "lines": [
        {"t": t, "conf": 1, "x0": 300, "y0": 400 + i * 80, "x1": 2100, "y1": 460 + i * 80} for i, t in enumerate(text)]}))
    recs = [{"t": t, "y": 600 + i * 120, "indent": False} for i, t in enumerate(text)]
    recs[2] = {"t": "pulation of 769,779 persons. During the next 10 years the", "y": 840, "indent": True}
    recover_lines(recs, vis, 5400, [])
    assert recs[2]["t"] == text[2] and recs[2]["first_word"] == "pulation" and not recs[2]["indent"]
