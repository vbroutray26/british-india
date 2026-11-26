from pipeline.segment import find_anchors, lines_to_text


def L(t, indent=False, page="233"):
    return {"t": t, "indent": indent, "y": 0, "page": page, "conf": 90}


def test_anchors_follow_expected_order_and_tolerate_ocr():
    lines = [
        L("Atri.—aA village situated in kila Kuspalle,", True), L("8 miles from Khurda."),
        L("? maacak—A ruined temple in the headquarters"), L("subdivision."),
        L("Pipli.—aA village situated on the Trunk Road,", True),
    ]
    found = find_anchors(lines, ["Atri", "Konārak", "Pipli"])
    assert [(i, h) for i, h, _ in found] == [(0, "Atri"), (2, "Konārak"), (4, "Pipli")]


def test_anchor_with_headquarters_descriptor():
    lines = [L("Khurda.— Headquarters of the subdivision", True), L("Khurda Subdivision —Western subdivision", True)]
    found = find_anchors(lines, ["Khurdā", "Khurdā subdivision"])
    assert [h for _, h, _ in found] == ["Khurdā", "Khurdā subdivision"]


def test_quoted_dash_is_not_an_entry():
    lines = [L("Atri.—A village.", True), L('writes:—"The portions that have suffered'), L("Baral.—A village", True)]
    found = find_anchors(lines, ["Atri", "Baral"])
    assert [i for i, _, _ in found] == [0, 2]


def test_lines_to_text_paragraphs_and_page_spans():
    text, spans = lines_to_text([L("First para", True, "1"), L("continues", False, "1"), L("Second para", True, "2")])
    assert text == "First para continues\n\nSecond para"
    assert spans[0]["page"] == "1" and spans[-1]["page"] == "2" and spans[-1]["end"] == len(text)
