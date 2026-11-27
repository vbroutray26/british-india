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


def test_garbled_running_head_is_told_by_the_gap_below_it():
    body = [_ln(f"body line {i} of the running text", 300, 700 + i * 102) for i in range(3)]
    p = Page(index=0, width=3300, height=5300, lines=[_ln("D4 Punt, ;", 500, 500, 1400), *body])
    head, rest = split_running_head(p, "24")
    assert head == "D4 Punt, ;" and len(rest) == 3


def test_junk_above_the_running_head_is_dropped_with_it():
    body = [_ln(f"body line {i} of the running text", 300, 700 + i * 102) for i in range(3)]
    p = Page(index=0, width=3600, height=5500, lines=[_ln('Vek" geet', 900, 0, 1300), _ln("128 PuRt.", 900, 533, 1500), *body])
    head, rest = split_running_head(p, "128")
    assert [l.text for l in rest] == [l.text for l in body] and "128 PuRt." in head


def test_a_short_first_line_with_ordinary_spacing_is_not_a_running_head():
    body = [_ln(f"body line {i} of the running text", 300, 602 + i * 102) for i in range(3)]
    p = Page(index=0, width=3300, height=5300, lines=[_ln("of the country.", 300, 500, 1000), *body])
    assert split_running_head(p, "77") == (None, p.lines)
    p = Page(index=0, width=3300, height=5300, lines=[_ln("B.", 1500, 500, 1600), *[_ln(f"Entry {i}, 12.", 300, 512 + i * 102) for i in range(3)]])
    assert split_running_head(p, "301")[0] is None


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


def _words(*cols, y=0):
    """A line from (x0, text) fragments; each word 100 px wide with 20 px spaces."""
    words, xs = [], []
    for x, text in cols:
        for w in text.split():
            words.append((w, 95))
            xs.append((x, x + 100))
            x += 120
    return Line(words=words, bbox=(xs[0][0], y, xs[-1][1], y + 80), fsize=100.0, xs=xs)


def test_a_two_column_index_page_is_read_left_column_then_right():
    rows = [_words((300, f"Left entry {i}, 1{i}."), (1800, f"Right entry {i}, 2{i}."), y=500 + i * 100) for i in range(6)]
    rows.append(_words((300, "revenue, 201-204."), y=1100))  # a turnover line in the left column only
    rows[2] = _words((300, "Left entry 2, 12."), (1400, "Right entry 2, 22."), y=700)  # the gap read narrower
    out = layout(rows, 3300, 5300)
    assert len(out["right"]) == 6
    assert [l.text for l in out["body"]] == [f"Left entry {i}, 1{i}." for i in range(6)] + ["revenue, 201-204."] + [
        f"Right entry {i}, 2{i}." for i in range(6)]


def test_running_text_with_wide_word_spacing_is_not_split_into_columns():
    rows = [_words((300, "The quick brown fox jumps over"), (1300 + (i % 3) * 400, "the lazy dog and runs"), y=500 + i * 100)
            for i in range(6)]
    out = layout(rows, 3300, 5300)
    assert len(out["body"]) == 6


def test_a_line_gathered_from_several_printed_lines_is_split_back_into_them():
    good = [_words((300, f"body line {i} of the running text"), y=500 + i * 100) for i in range(5)]
    mash = _words((1000, "Jagannath and his domain, held sacred"), (300, "But the Afghans, though defeated,"), y=0)
    mash.ys = [(650, 700)] * 6 + [(950, 1000)] * 5  # the OCR's one line holds words from two printed lines
    mash.bbox = (2390, 1100, 2440, 1160)
    out = layout(good + [mash], 3300, 5300)
    assert [l.text for l in out["body"]] == [good[0].text, good[1].text, "Jagannath and his domain, held sacred",
                                             good[2].text, good[3].text, good[4].text, "But the Afghans, though defeated,"]


def test_a_line_with_a_side_note_glued_on_is_not_split():
    ln = _words((300, "settlement they numbered 1,000 with an"), (2900, "Kherids"), y=500)
    ln.ys = [(500, 560)] * 6 + [(470, 530)]
    from pipeline.ocr import split_jumps
    assert split_jumps(ln, 3300) == [ln]


def test_inset_table_cells_are_cut_from_the_lines_beside_it():
    from pipeline.ocr import cut_inset
    rows = [_words((300, "full width line of the running text above"), y=500),
            _words((300, "Puri 8,59"), (1750, "from fever (using the"), y=600),
            _words((1750, "denote malarial fever"), y=700)]
    kept = cut_inset(rows, [{"x_frac": 1750 / 3300, "y0_frac": 580 / 5300, "y1_frac": 760 / 5300}], 3300, 5300)
    assert [l.text for l in kept] == ["full width line of the running text above", "from fever (using the", "denote malarial fever"]


def test_beside_an_inset_table_an_indent_is_measured_from_the_wrapped_texts_edge():
    from pipeline.ocr import inset_indent
    t = {"x_frac": 0.3}
    assert not inset_indent(1000, t, 3300) and inset_indent(1120, t, 3300) and not inset_indent(None, t, 3300)


def test_inset_regions_move_into_the_first_ocrs_page_coordinates():
    from pipeline.ocr import shift_insets
    texts = [f"line {i} of the running text on this page" for i in range(5)]
    body = [_words((300, t), y=1000 + i * 100) for i, t in enumerate(texts)]  # tops at 0.2, 0.22, ... of 5000
    rows = [{"t": t, "y_frac": 0.18 + i * 0.02} for i, t in enumerate(texts)]  # the second read has them 0.02 higher
    (t,) = shift_insets([{"y0_frac": 0.5, "y1_frac": 0.6, "first_frac": 0.51, "x_frac": 0.3}], body, rows, 5000)
    assert round(t["y0_frac"], 4) == 0.52 and round(t["first_frac"], 4) == 0.53 and t["x_frac"] == 0.3


def test_pieces_of_one_printed_line_are_joined():
    rows = [_words((300, f"body line {i} of the running text set full across the page width here"), y=500 + i * 100)
            for i in range(5)]
    a, b = _words((300, "4 ot Govern"), y=1000), _words((1100, "ent, travelling on the Orissa"), y=1030)
    out = layout(rows + [b, a], 3300, 5300)
    assert [l.text for l in out["body"]][-1] == "4 ot Govern ent, travelling on the Orissa"
    assert len(out["body"]) == 6


# --- audited corrections reach footnotes and margin notes; an empty replacement deletes (numeral review)

def _corr(find, replace, page="12"):
    return {"page": page, "find": find, "replace": replace}


def test_correction_applies_to_lines_and_marks_them():
    from pipeline.ocr import apply_corrections
    lines = [{"t": "came into force from the Ist July 1906.", "y": 10}]
    applied = apply_corrections([_corr("Ist July", "1st July")], "12", lines, [], [])
    assert lines[0]["t"] == "came into force from the 1st July 1906." and lines[0]["corrected"]
    assert applied == ["Ist July"]


def test_correction_only_on_its_own_page():
    from pipeline.ocr import apply_corrections
    lines = [{"t": "Tangri, 157.", "y": 10}]
    assert apply_corrections([_corr("157", "187", page="13")], "12", lines, [], []) == []
    assert lines[0]["t"] == "Tangri, 157."


def test_correction_applies_to_footnotes_and_margin():
    from pipeline.ocr import apply_corrections
    foot = ["Kings of Khurda, J.A.S.B., 1808, p. 383."]
    margin = [{"t": "Rainfall in 1891", "y": 40}]
    applied = apply_corrections([_corr("1808, p. 383", "1898, p. 383"), _corr("in 1891", "in 1892")],
                                "12", [], margin, foot)
    assert foot == ["Kings of Khurda, J.A.S.B., 1898, p. 383."]
    assert margin[0]["t"] == "Rainfall in 1892"
    assert sorted(applied) == ["1808, p. 383", "in 1891"]


def test_empty_replacement_deletes_a_junk_line():
    from pipeline.ocr import apply_corrections
    lines = [{"t": "real text", "y": 10}, {"t": "es 2) eee", "y": 20}]
    margin = [{"t": "es 2) eee", "y": 20}]
    apply_corrections([_corr("es 2) eee", "")], "12", lines, margin, [])
    assert [ln["t"] for ln in lines] == ["real text"] and margin == []
