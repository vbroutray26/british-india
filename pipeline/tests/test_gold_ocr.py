from pipeline.gold_ocr import cer, normalise, parse_gold, replacement_page, sample_pages


def test_normalise_folds_typography_not_letters():
    assert normalise("“Puri’s”  —\n thāna") == "\"Puri's\" - thāna"
    assert normalise("thāna", fold_diacritics=True) == "thana"
    assert normalise("{Migration.} Apart") == "Migration. Apart"  # side-note braces are markup


def test_cer_counts_edits_over_gold_length():
    r = cer("Bānpur thāna", "Banpur thina")
    assert r["edits"] == 2 and r["chars"] == 12
    assert cer("Bānpur thāna", "Banpur thina", fold_diacritics=True)["edits"] == 1  # ā→i is still wrong


def test_cer_numerals_counts_only_digit_errors():
    r = cer("was 49,334 in 1901", "wns 49,364 in 1901")
    assert r["digits"] == 9 and r["digit_edits"] == 1


def test_cer_numerals_counts_inserted_digits():
    r = cer("in 1901", "in 19011")
    assert r["digit_edits"] == 1


def test_parse_gold_reads_sections_and_ignores_comments():
    text = "% GS-OCR omalley-puri-1908 p. 61\n@@ body\nline one\n{Note.} line two\n@@ footnotes\n* A note.\n"
    g = parse_gold(text)
    assert g["body"] == "line one\n{Note.} line two" and g["footnotes"] == "* A note."


def test_sample_is_stable_and_stratified():
    pages = [{"page": str(i), "leaf": i, "confidence": 50 + i % 50, "flags": []} for i in range(1, 301)]
    a, b = sample_pages(pages, 20, seed=1908), sample_pages(pages, 20, seed=1908)
    assert a == b and len(a) == 20 and len(set(a)) == 20
    conf = {p["page"]: p["confidence"] for p in pages}
    assert sum(conf[p] < 63 for p in a) >= 4  # lowest-confidence quartile is represented


def test_replacement_comes_from_the_same_stratum_and_is_stable():
    pages = [{"page": str(i), "leaf": i, "confidence": 50 + i % 50, "flags": []} for i in range(1, 301)]
    taken = sample_pages(pages, 20, seed=1908)
    low = min(taken, key=lambda p: pages[int(p) - 1]["confidence"])
    r1, r2 = replacement_page(pages, low, taken), replacement_page(pages, low, taken)
    assert r1 == r2 and r1 not in taken
    assert pages[int(r1) - 1]["confidence"] < 63  # same (lowest) quartile as the page it replaces


def test_raw_text_leaves_out_recovered_lines_and_reviewed_keeps_them():
    from pipeline.gold_ocr import ocr_text
    rec = {"text_raw": "first line\nthird line", "margin": [], "footnotes": [],
           "lines": [{"t": "first line", "y": 1}, {"t": "second line", "y": 2, "recovered": True}, {"t": "third line", "y": 3}]}
    assert ocr_text(rec, reviewed=False) == "first line\nthird line"
    assert ocr_text(rec, reviewed=True) == "first line\nsecond line\nthird line"
