from pipeline.validate import validator
from pipeline.verify import check, quote_ok

PASSAGE = {"passage_id": "ps_t_00", "text": "Jagannáth temple. The population in 1901 was 49,334 persons."}


def fact(quote, value, ftype="population", start=None):
    s = PASSAGE["text"].find(quote) if start is None else start
    return {"fact_id": "ft_x", "place_id": "pl_x-0000", "type": ftype, "value": value, "as_of_year": 1901,
            "evidence": [{"passage_id": "ps_t_00", "quote": quote, "char_start": s, "char_end": s + len(quote)}],
            "method": "rule", "confidence": 0.9, "review": {"status": "unreviewed"}}


def test_quote_match_ignores_diacritics_and_case():
    assert quote_ok("jagannath TEMPLE", PASSAGE["text"])[0]


def test_numbers_must_match_exactly():
    assert not quote_ok("in 1901 was 49,364", PASSAGE["text"])[0]


def test_valid_fact_passes():
    assert check(fact("in 1901 was 49,334", {"number": 49334, "unit": "persons"}), {"ps_t_00": PASSAGE}, validator("fact.schema.json")) == []


def test_value_number_must_be_in_quote():
    r = check(fact("in 1901 was 49,334", {"number": 49364, "unit": "persons"}), {"ps_t_00": PASSAGE}, validator("fact.schema.json"))
    assert any("number 49364 not in quote" in x for x in r)


def test_llm_fact_needs_model_and_prompt_version():
    f = fact("in 1901 was 49,334", {"number": 49334, "unit": "persons"}) | {"method": "llm"}
    r = check(f, {"ps_t_00": PASSAGE}, validator("fact.schema.json"))
    assert any("schema" in x for x in r)


def test_offsets_must_point_at_quote():
    r = check(fact("in 1901 was 49,334", {"number": 49334, "unit": "persons"}, start=0), {"ps_t_00": PASSAGE}, validator("fact.schema.json"))
    assert "offsets do not point at the quote" in r


def test_numbers_in_reads_raised_decimal_points_but_not_coordinates():
    from pipeline.verify import numbers_in
    assert numbers_in("limits is 4°03 square miles") == ["4.03"]
    assert numbers_in("in 20°11′ N. and 85° 38′ E.") == ["20", "11", "85", "38"]


def test_a_figure_on_a_recovered_line_is_queued_as_read_by_one_engine():
    from pipeline.verify import recovered_reasons
    p = {"passage_id": "ps_t_00", "page": "138", "page_end": "138",
         "text": "consists of forests extending over an area of 480 square miles. The reserved"}
    q = "480 square miles"
    f = {"evidence": [{"passage_id": "ps_t_00", "quote": q, "char_start": p["text"].find(q), "char_end": 0}]}
    rec = {"138": ["extending over an area of 480 square miles. The reserved"]}
    assert recovered_reasons(f, {"ps_t_00": p}, rec) == ["one engine only: line missing from the first OCR (p. 138)"]
    assert recovered_reasons(f, {"ps_t_00": p}, {"138": ["another line entirely, of 12 acres"]}) == []
