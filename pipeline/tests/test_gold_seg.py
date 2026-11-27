from pipeline.gold_seg import match


def rec(kind, page, text):
    return {"kind": kind, "page_start": page, "text": text}


GOLD = {"kind": "gazetteer", "page": "250", "first_words": "Kaipadar.—A village situated on the Ganjām-Cuttack road,"}


def test_boundary_found_despite_ocr_noise_and_diacritics():
    recs = [rec("gazetteer", "250", "Kaipadar.—A village situated on the Ganjam-Cuttaok road, 7 miles to the south-west")]
    assert match(GOLD, recs) == "found"


def test_boundary_on_wrong_page_or_kind_is_not_found():
    assert match(GOLD, [rec("gazetteer", "251", "Kaipadar.—A village situated on the Ganjam-Cuttack road,")]) != "found"
    assert match(GOLD, [rec("section", "250", "Kaipadar.—A village situated on the Ganjam-Cuttack road,")]) != "found"


def test_boundary_inside_a_record_is_merged_not_found():
    text = "It contains the residences of the railway staff. Kaipadar.—A village situated on the Ganjam-Cuttack road,"
    recs = [rec("gazetteer", "250", "Jatni.—A village containing the railway junction known as Khurda Road Station. " * 4 + text)]
    assert match(GOLD, recs) == "merged"


def test_section_start_may_follow_a_chapter_heading():
    g = {"kind": "section", "page": "198", "first_words": "During the time of the Hindu kings of Orissa the country was"}
    recs = [rec("section", "198", "CHAPTER XII.\n\nLAND REVENUE ADMINISTRATION. Durine the time of the Hindu kings of Orissa the country was")]
    assert match(g, recs) == "found"


def test_garbled_heading_ocr_is_not_a_segmentation_error():
    g = {"kind": "gazetteer", "page": "250", "first_words": "Kālupara Ghāt.—A village on the Chilkā lake, which was"}
    recs = [rec("gazetteer", "250", "ri pirat village on the Chilka lake, which was an important centre of trade")]
    assert match(g, recs) == "found"
