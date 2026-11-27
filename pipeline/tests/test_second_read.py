from pipeline.second_read import assemble, fix_chars, page_numbers
from pipeline.validate import validator
from pipeline.verify import check

W, H = 2400, 3600


def ln(t, x0, y0, x1, h=60):
    return {"t": t, "conf": 1.0, "x0": x0, "y0": y0, "x1": x1, "y1": y0 + h}


def body(n, y=400):
    return [ln(f"body line {i} of the running text here", 300, y + i * 80, 2100) for i in range(n)]


def test_fix_chars_maps_umlauts_to_macrons_and_raised_points_to_middle_dot():
    assert fix_chars("Jagannäth Bhubanesvar 4:52 acres, 8.11 and Swetgangă") == "Jagannāth Bhubanesvar 4·52 acres, 8·11 and Swetgangā"


def test_fix_chars_maps_cyrillic_look_alikes_to_latin():
    assert fix_chars("Mоsт April mаx. Кагиu") == "Mosт April max. Kaгиu"  # т, г, и have no look-alike: left as read


def test_fix_chars_keeps_ordinary_punctuation():
    assert fix_chars("pp. 27-28; Ch. 114. In 1905.") == "pp. 27-28; Ch. 114. In 1905."


def test_assemble_drops_running_head_and_page_number():
    rec = {"w": W, "h": H, "lines": [ln("GAZETTEER.", 900, 200, 1300), ln("295", 2000, 200, 2100)] + body(8)}
    out = assemble(rec).split("\n")
    assert out[0].startswith("body line 0") and len(out) == 8


def test_assemble_joins_split_fragments_of_one_printed_line():
    lines = body(6)
    lines[2] = ln("the top of the linga visible to the worshippers.", 300, 560, 1400)
    lines.append(ln("This god is more", 1500, 552, 2100))
    out = assemble({"w": W, "h": H, "lines": lines}).split("\n")
    assert out[2] == "the top of the linga visible to the worshippers. This god is more"


def test_assemble_puts_a_left_margin_note_at_the_start_of_its_first_line():
    lines = body(6) + [ln("Purī as a", 40, 560, 250), ln("health", 40, 610, 200), ln("resort.", 40, 660, 200)]
    out = assemble({"w": W, "h": H, "lines": lines}).split("\n")
    assert out[2].startswith("Purī as a health resort. body line 2")


def test_assemble_reads_two_columns_left_then_right():
    left = [ln(f"Left {i}, 1{i}.", 100, 400 + i * 80, 1000) for i in range(6)]
    right = [ln(f"Right {i}, 2{i}.", 1300, 400 + i * 80, 2200) for i in range(6)]
    out = assemble({"w": W, "h": H, "lines": right + left}).split("\n")
    assert out[:2] == ["Left 0, 10.", "Left 1, 11."] and out[6] == "Right 0, 20."


def test_page_numbers_normalise_separators():
    assert page_numbers("covering 4·52 acres; population 1,04,351 in 1901") == {"4.52", "104351", "1901"}


PASSAGE = {"passage_id": "ps_t_00", "page": "12", "page_end": "12",
           "text": "The population in 1901 was 49,334 persons."}


def fact(quote, value):
    s = PASSAGE["text"].find(quote)
    return {"fact_id": "ft_x", "place_id": "pl_x-0000", "type": "population", "value": value, "as_of_year": 1901,
            "evidence": [{"passage_id": "ps_t_00", "quote": quote, "char_start": s, "char_end": s + len(quote)}],
            "method": "rule", "confidence": 0.9, "review": {"status": "unreviewed"}}


def test_verify_passes_when_the_second_read_agrees():
    f = fact("in 1901 was 49,334", {"number": 49334, "unit": "persons"})
    assert check(f, {"ps_t_00": PASSAGE}, validator("fact.schema.json"), second={"12": {"1901", "49334"}}) == []


def test_verify_queues_a_number_the_second_read_did_not_see():
    f = fact("in 1901 was 49,334", {"number": 49334, "unit": "persons"})
    r = check(f, {"ps_t_00": PASSAGE}, validator("fact.schema.json"), second={"12": {"1901", "49384"}})
    assert "second read disagrees: 49334" in r


def test_verify_flags_a_page_without_a_second_read():
    f = fact("in 1901 was 49,334", {"number": 49334, "unit": "persons"})
    r = check(f, {"ps_t_00": PASSAGE}, validator("fact.schema.json"), second={})
    assert "no second read for page 12" in r


def test_margin_notes_are_joined_and_placed_as_a_fraction_of_page_height():
    from pipeline.second_read import margin_notes
    lines = body(6) + [ln("Purī as a", 40, 560, 250), ln("health", 40, 610, 200), ln("resort.", 40, 660, 200)]
    assert margin_notes({"w": W, "h": H, "lines": lines}) == [{"t": "Purī as a health resort.", "y_frac": round(560 / H, 4)}]


# ---- recovering lines the first OCR dropped (DP-01 uses the second read)

def rows_of(texts, y=0.30, step=0.02, h=0.016):
    return [{"t": t, "y_frac": round(y + i * step, 4), "h_frac": h, "indent": False} for i, t in enumerate(texts)]


BOOK = ["The Puri Forest Division is situated entirely within the Khurda",
        "subdivision and consists of reserved and protected forests",
        "extending over an area of 485 square miles. The reserved",
        "forests contain 20 separate demarcated blocks having an area of",
        "113 square miles, while the protected forests comprise all"]


def test_missing_lines_finds_a_line_dropped_between_two_matched_lines():
    from pipeline.second_read import missing_lines
    tess = [BOOK[0].replace("Puri", "Pnri"), BOOK[1], BOOK[3], BOOK[4].replace("square", "squsre")]
    got = missing_lines(tess, rows_of(BOOK))
    assert [(i, r["t"]) for i, r in got] == [(1, BOOK[2])]


def test_missing_lines_ignores_a_line_the_first_ocr_read_badly():
    from pipeline.second_read import missing_lines
    tess = [BOOK[0], BOOK[1], "extcnd1ng ovcr an arca of 4S5 sqn1re mlles. Thc rescrvcd", BOOK[3], BOOK[4]]
    assert missing_lines(tess, rows_of(BOOK)) == []


def test_missing_lines_ignores_a_line_the_first_ocr_has_elsewhere_on_the_page():
    from pipeline.second_read import missing_lines
    tess = [BOOK[0], BOOK[1], BOOK[3], BOOK[4]]
    assert missing_lines(tess, rows_of(BOOK), page_text=" ".join(tess) + " " + BOOK[2]) == []


def test_missing_lines_recovers_the_last_lines_of_a_page_but_not_footnotes():
    from pipeline.second_read import missing_lines
    rows = rows_of(BOOK) + [{"t": "* Jarrett's translation, II, 127, and Stirling's account.", "y_frac": 0.5,
                             "h_frac": 0.009, "indent": False}]
    got = missing_lines(BOOK[:3], rows)
    assert [(i, r["t"]) for i, r in got] == [(2, BOOK[3]), (2, BOOK[4])]


def test_body_rows_mark_an_indented_line_and_leave_out_margin_notes():
    from pipeline.second_read import body_rows
    lines = body(6) + [ln("Purī as a", 40, 560, 250)]
    lines[3] = ln("A new paragraph starts here with an indent", 420, 640, 2100)
    rows = body_rows({"w": W, "h": H, "lines": lines})
    assert len(rows) == 6 and rows[3]["indent"] and not rows[2]["indent"] and "Purī" not in rows[2]["t"]


def test_missing_lines_never_recovers_a_footnote_into_the_body():
    from pipeline.second_read import missing_lines
    rows = rows_of(BOOK) + [{"t": "‡ Later Kings of Khurda, M. M. Chakravarti, J.A.S.B., 1898, p. 388.",
                             "y_frac": 0.40, "h_frac": 0.016, "indent": False}]
    assert missing_lines(BOOK, rows) == []
    rows = rows_of(BOOK) + rows_of(["was entertained in the year of the flood by the Raja"], y=0.60)
    assert missing_lines(BOOK, rows) == []  # after a gap below the last line: a footnote, not body


def test_missing_lines_ignores_a_present_line_with_a_side_note_glued_on():
    from pipeline.second_read import missing_lines
    tess = [BOOK[0], BOOK[1], BOOK[3], BOOK[4], "Fishing is at present one of the most important occupations"]
    rows = rows_of(BOOK[:2] + [BOOK[3] + " Fisheries."] + BOOK[3:])
    rows[2]["t"] = "Fishing is at present one of the most important occupations Fishericn."
    assert missing_lines(tess, rows) == []


def test_first_word_fixes_restore_letters_the_first_ocr_lost_at_a_line_start():
    from pipeline.second_read import first_word_fixes
    first = ["the result was to show for the district, as now constituted, a",
             "pulation of 769,779 persons. During the next 10 years the",
             "evidently the work of a later hand, and the carving is poor"]
    rows = rows_of(["the result was to show for the district, as now constituted, a",
                    "population of 769,779 persons, During the next 10 years the",
                    "-evidently the work of a later hand, and the carving is poor"])
    assert first_word_fixes(first, rows) == {1: ("population", False)}


def test_geometry_takes_position_and_indent_from_the_second_read_even_for_a_misplaced_line():
    from pipeline.second_read import geometry
    book = BOOK + ["Nearly a century ago Stirling said that the finest salt of all India"]
    rows = rows_of(book)
    rows[5]["indent"] = True
    first = [book[5], BOOK[0], BOOK[1], BOOK[2], BOOK[3], "Disrarct " + BOOK[4]]  # stored first; note glued on
    g = geometry(first, rows)
    assert g[0] == (rows[5]["y_frac"], True)   # the misplaced line goes back to its printed place
    assert g[1] == (None, False)               # in order: only the indent is taken
    assert g[5] == (None, False)               # a glued side-note does not fake an indent


def test_body_rows_see_a_shallow_indent_on_a_skewed_page():
    from pipeline.second_read import body_rows
    lines = [ln(f"body line {i} of the running text here", 300 + i * 6, 400 + i * 80, 2100) for i in range(8)]
    lines[5] = ln("A new paragraph with a shallow indent here", 300 + 5 * 6 + 70, 800, 2100)  # 2.9% of 2400
    assert [r["indent"] for r in body_rows({"w": W, "h": H, "lines": lines})] == [False] * 5 + [True] + [False] * 2


def test_rows_do_not_merge_a_short_line_with_the_next_when_vision_boxes_are_taller_than_the_spacing():
    from pipeline.second_read import body_rows
    lines = [ln(f"body line {i} of the running text here", 300, 400 + i * 55, 2100, h=115) for i in range(8)]
    lines[3] = ln("Gazetteer was published.", 300, 400 + 3 * 55, 900, h=90)
    lines[4] = ln("Regarding other fevers, Major Waters, writes as follows", 390, 400 + 4 * 55 + 10, 2100, h=113)
    rows = body_rows({"w": W, "h": H, "lines": lines})
    assert len(rows) == 8 and rows[4]["t"].startswith("Regarding") and rows[4]["indent"]


def test_geometry_takes_the_indent_of_the_row_that_matches_the_start_of_a_merged_line():
    from pipeline.second_read import geometry
    rows = rows_of(["below :-", "The average density of population, which is only 407 persons",
                    "Statistics. per square mile, is lower than it would otherwise be owing to the",
                    "inclusion of the area of the Chilka lake. Density of popula-"])
    rows[1]["indent"] = True
    first = ["below :-", ("The average density of population, which is only 407 persons per square mile, is lower "
                          "than it would otherwise be owing to the"), "inclusion of the area of the Chilka lake. Density of popula-"]
    assert geometry(first, rows)[1] == (None, True)


def test_geometry_rematches_a_misplaced_line_merged_with_the_next_by_its_opening():
    from pipeline.second_read import geometry
    stirling = "Nearly a century ago Stirling said that the finest salt of"
    rows = rows_of([BOOK[0], BOOK[1], BOOK[2], stirling, "all India was manufactured in the wild inhospitable tract along"])
    first = [BOOK[0], stirling + " Salt manu all India was manufactured in the wild inhospitable", BOOK[1], BOOK[2]]
    assert geometry(first, rows)[1] == (rows[3]["y_frac"], False)


def test_missing_lines_replaces_a_fragment_the_first_ocr_kept_of_lines_it_dropped():
    from pipeline.second_read import missing_lines
    tess = [BOOK[0], "ending over an area", BOOK[4]]
    got = missing_lines(tess, rows_of(BOOK))
    assert [(i, r["t"]) for i, r in got] == [(0, BOOK[1]), (0, BOOK[2]), (0, BOOK[3])]
    assert all(r["replaces"] == [1] for _, r in got)


def test_recover_lines_drops_the_fragment_it_replaces(tmp_path):
    import json

    from pipeline.ocr import recover_lines
    lines = [{"t": BOOK[0], "y": 1000, "indent": False}, {"t": "ending over an area", "y": 1100, "indent": False},
             {"t": BOOK[4], "y": 1400, "indent": False}]
    vis = tmp_path / "v.json"
    W2, H2 = 2400, 3600
    vis.write_text(json.dumps({"w": W2, "h": H2, "lines": [
        {"t": t, "conf": 1.0, "x0": 300, "y0": int(1000 * H2 / 5000) + k * 72, "x1": 2100, "y1": int(1000 * H2 / 5000) + k * 72 + 50}
        for k, t in enumerate(BOOK)]}))
    recover_lines(lines, vis, 5000, [])
    assert [ln["t"] for ln in lines] == BOOK


# ---- merging the two reads line by line (D-31)

VOCAB = {"the", "inscription", "on", "hatigumpha", "or", "elephant", "cave", "which", "an", "historical", "record",
         "for", "it", "shows", "that", "in", "was", "persons"}


def test_merge_takes_the_word_both_engines_attest_elsewhere_and_the_macrons_either_saw():
    from pipeline.second_read import merge_line
    h = "the inseription on the Hatigumpha or elephant cave, which"
    v = "the inscription on the Hātīgumphā or elephant cave, which"
    assert merge_line(h, v, VOCAB) == v


def test_merge_never_takes_a_figure_from_the_second_read():
    from pipeline.second_read import merge_line
    assert merge_line("in 1901 was 49,364 persons", "in 1901 was 49,334 persons", VOCAB) == "in 1901 was 49,364 persons"


def test_merge_drops_short_junk_only_the_first_ocr_has_and_keeps_its_words_when_unsure():
    from pipeline.second_read import merge_line
    assert merge_line("Sete an historical | record, for it shows", "an historical record, for it shows", VOCAB) == (
        "an historical record, for it shows")
    assert merge_line("the Kalinganagari cave", "the Kalinganagarl cave", VOCAB) == "the Kalinganagari cave"


def test_merge_takes_the_whole_line_when_the_first_read_is_garbled_and_the_figures_agree():
    from pipeline.second_read import merge_line
    h = "\\ whu hac| dicdfrorn chol era, floatimgin"
    v = "who had died from cholera, floating in"
    vocab = VOCAB | {"who", "had", "died", "from", "cholera", "floating"}
    assert merge_line(h, v, vocab) == v


def test_agreed_words_are_the_words_both_engines_read_on_the_same_line():
    from pipeline.second_read import agreed_words
    assert agreed_words([("the inseription on", "the inscription on")]) == {"the", "on"}


def test_merge_keeps_the_first_reads_punctuation_and_leaves_out_a_glued_side_note():
    from pipeline.second_read import merge_line
    vocab = {"first", "census", "of", "the", "district", "was", "taken", "in", "year", "and", "persons", "during"}
    h = "Tux firet consus of the district was taken in the year 1872, and Growrm"
    v = "THs frst census of the distriet was taken in the year 1872, and Gaowrz"
    assert merge_line(h, v, vocab) == "Tux firet census of the district was taken in the year 1872, and Growrm"


def test_merge_never_swaps_a_word_for_an_unlike_one():
    from pipeline.second_read import merge_line
    h = "Bhubaneswar.—A village in the Khurda subdivision, situated"
    v = "—A village in the Khurdā subdivision, situated"
    assert merge_line(h, v, {"a", "village", "in", "the", "khurda", "subdivision", "situated"}) == (
        "Bhubaneswar.—A village in the Khurdā subdivision, situated")


def _inset_page():
    """A page with a small table set into the left of the text column; the text wraps beside it."""
    lines = body(4)  # full-width lines above, y 400..640
    for i, t in enumerate(["exaggerate the number of deaths", "from fever (using the term to", "denote malarial fever), and to",
                           "group under that heading all", "diseases in which the temperature"]):
        lines.append(ln(t, 1050, 720 + i * 80, 2100))
    cells = [("YEARS.", 330, 760), ("1901-05.", 560, 752), ("1906.", 840, 752),
             ("Puri", 330, 860), ("8·59", 600, 856), ("7·27", 850, 853),
             ("Bengal", 330, 940), ("21·78", 590, 938), ("22·41", 840, 934)]
    lines += [ln(t, x, y, x + 150, 40) for t, x, y in cells]
    lines += [ln(f"after line {i} of the running text here", 300, 1120 + i * 80, 2100) for i in range(3)]
    return {"w": W, "h": H, "lines": lines}


def test_an_inset_table_is_read_row_by_row_from_its_cells():
    from pipeline.second_read import inset_tables
    (t,) = inset_tables(_inset_page())
    assert t["rows"] == ["YEARS. 1901-05. 1906.", "Puri 8·59 7·27", "Bengal 21·78 22·41"]
    assert abs(t["x_frac"] - 1050 / W) < 0.001 and t["y0_frac"] < 720 / H < 1040 / H < t["y1_frac"]


def test_body_rows_leave_out_the_cells_of_an_inset_table():
    from pipeline.second_read import body_rows
    texts = [r["t"] for r in body_rows(_inset_page())]
    assert "exaggerate the number of deaths" in texts and not any("8·59" in t or "Bengal" in t for t in texts)


def test_a_page_of_short_lines_is_not_an_inset_table():
    from pipeline.second_read import inset_tables
    lines = body(4) + [ln(t, 1050, 720 + i * 80, 2100) for i, t in enumerate(["one short line", "and another", "a third", "a fourth"])]
    assert inset_tables({"w": W, "h": H, "lines": lines}) == []
