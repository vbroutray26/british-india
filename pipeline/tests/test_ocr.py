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
