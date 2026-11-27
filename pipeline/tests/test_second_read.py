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
