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


# ---- a leaf the scan repeats (D-37)

def _page_text(seed, n=60):
    import random
    vocab = ["the", "of", "and", "to", "in", "revenue", "district", "Khurda", "Puri", "rebels", "troops", "estates", "temple", "Collector", "Rs.", "lakhs", "pilgrims", "road", "river", "village", "Raja", "tank", "sea", "salt", "excise", "land", "police", "Cuttack", "miles"]
    rnd = random.Random(seed)
    return " ".join(rnd.choice(vocab) for _ in range(n))


def _misread(text):
    """The same page read again: a few words come out differently."""
    w = text.split()
    for k in (3, 17, 40):
        w[k] = w[k][:-1] + "e"
    return " ".join(w)


def test_a_rescanned_leaf_is_a_duplicate_of_its_earlier_copy():
    """O'Malley leaves 68-72: pp. 52, 53, 52 again, 53 again, 54. The host guessed numbers for 68-70."""
    from pipeline.ocr import duplicate_leaves
    p52, p53, p54 = _page_text(52), _page_text(53), _page_text(54)
    texts = {68: p52, 69: p53, 70: _misread(p52), 71: _misread(p53), 72: p54}
    page_map = {68: "52", 69: "53", 70: "54", 71: "53", 72: "54"}
    conf = {68: 0, 69: 0, 70: 0, 71: 100, 72: 100}
    assert duplicate_leaves(texts, page_map, conf) == {70: 68, 71: 69}


def test_a_leaf_that_only_shares_a_page_number_is_kept():
    from pipeline.ocr import duplicate_leaves
    texts = {10: _page_text(1), 11: _page_text(2)}
    assert duplicate_leaves(texts, {10: "8", 11: "8"}, {10: 0, 11: 100}) == {}


def test_like_text_is_kept_when_the_host_read_two_different_page_numbers():
    """The page map must back the text: two leaves whose printed numbers the host read are two pages."""
    from pipeline.ocr import duplicate_leaves
    texts = {10: _page_text(1), 12: _misread(_page_text(1))}
    assert duplicate_leaves(texts, {10: "8", 12: "10"}, {10: 100, 12: 100}) == {}


def test_a_copy_of_a_copy_points_to_the_first_leaf():
    from pipeline.ocr import duplicate_leaves
    t = _page_text(7)
    texts = {20: t, 21: _page_text(8), 22: _misread(t), 23: t}
    assert duplicate_leaves(texts, {20: "7", 21: "8", 22: "7", 23: "7"}, {20: 100, 21: 100, 22: 0, 23: 0}) == {22: 20, 23: 20}


def test_blank_and_plate_leaves_are_never_duplicates():
    from pipeline.ocr import duplicate_leaves
    texts = {1: "", 2: "PLATE I.", 3: "", 4: "PLATE I."}
    assert duplicate_leaves(texts, {}, {1: 0, 2: 0, 3: 0, 4: 0}) == {}


def test_leaves_far_apart_are_not_compared():
    from pipeline.ocr import duplicate_leaves
    t = _page_text(9)
    assert duplicate_leaves({30: t, 60: t}, {30: "30", 60: "30"}, {30: 0, 60: 0}) == {}


def _hocr(pages):
    """Minimal hOCR: each page is a list of lines, each line a string of words set across the page."""
    out = ["<html><body>"]
    for lines in pages:
        out.append('<div class="ocr_page" title="bbox 0 0 2000 3000">')
        for i, text in enumerate(lines):
            y = 300 + i * 60
            out.append(f'<span class="ocr_line" title="bbox 200 {y} 1800 {y + 40}">')
            for k, w in enumerate(text.split()):
                x = 200 + k * 200
                out.append(f'<span class="ocrx_word" title="bbox {x} {y} {x + 150} {y + 40}; x_wconf 95">{w}</span>')
            out.append("</span>")
        out.append("</div>")
    return "\n".join(out + ["</body></html>"])


def _source(tmp_path, texts, numbers):
    import json
    folder = tmp_path / "raw" / "dup-src"
    folder.mkdir(parents=True)
    pages = [[" ".join(t.split()[k:k + 8]) for k in range(0, len(t.split()), 8)] for t in texts]
    (folder / "x_hocr.html").write_text(_hocr(pages))
    (folder / "x_page_numbers.json").write_text(json.dumps({"pages": [
        {"leafNum": i, "pageNumber": n, "confidence": c} for i, (n, c) in enumerate(numbers)]}))
    return tmp_path / "raw", tmp_path / "out"


def test_run_keeps_one_leaf_per_printed_page_and_flags_the_copy(tmp_path):
    from pipeline.ocr import run
    p1, p2 = _page_text(1), _page_text(2)
    raw, out = _source(tmp_path, [p1, p2, _misread(p1), _page_text(3)],
                       [("1", 100), ("2", 0), ("3", 0), ("3", 100)])
    rows = run("dup-src", raw_dir=raw, out_dir=out)
    assert [(r["leaf"], r["page"]) for r in rows] == [(0, "1"), (1, "2"), (2, None), (3, "3")]
    assert "duplicate-leaf-of:0" in rows[2]["flags"] and rows[2]["text_clean"]  # kept for the record, off the page sequence
    assert not any(f.startswith("duplicate") for r in rows if r["leaf"] != 2 for f in r["flags"])


def test_run_with_a_repeated_leaf_is_idempotent(tmp_path):
    from pipeline.ocr import run
    p1 = _page_text(1)
    raw, out = _source(tmp_path, [p1, _page_text(2), _misread(p1)], [("1", 100), ("2", 0), ("3", 0)])
    run("dup-src", raw_dir=raw, out_dir=out)
    first = (out / "dup-src" / "pages.jsonl").read_bytes()
    run("dup-src", raw_dir=raw, out_dir=out)
    assert (out / "dup-src" / "pages.jsonl").read_bytes() == first


def test_a_repeated_leaf_is_left_out_of_the_second_read_merge(tmp_path):
    """Its words would count twice towards the words both engines agree on, and its lines are not used."""
    import json

    from pipeline.ocr import run
    p1 = _page_text(1)
    copy = _misread(p1)
    raw, out = _source(tmp_path, [p1, _page_text(2), copy], [("1", 100), ("2", 0), ("3", 0)])
    vision = raw / "dup-src" / "ocr_vision"
    vision.mkdir()
    for leaf, text in ((0, p1), (2, p1)):  # the second read gets the copy's words right
        lines = [" ".join(text.split()[k:k + 8]) for k in range(0, len(text.split()), 8)]
        (vision / f"leaf_{leaf:04d}.json").write_text(json.dumps({"w": 2000, "h": 3000, "lines": [
            {"conf": 1, "t": t, "x0": 200, "x1": 1750, "y0": 300 + i * 60, "y1": 340 + i * 60} for i, t in enumerate(lines)]}))
    rows = run("dup-src", raw_dir=raw, out_dir=out)
    assert not any(f.startswith("merged-lines") for f in rows[2]["flags"])
    assert not any("first_read" in ln for ln in rows[2]["lines"])
