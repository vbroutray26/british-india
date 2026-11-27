from pipeline.rules import consistency, extract


def P(text):
    return {"passage_id": "ps_test_00", "entry_id": "en_test", "char_start": 0, "char_end": len(text), "text": text, "page": "1"}


def facts(text, t):
    return [f for f in extract(P(text), "pl_x-0000") if f["type"] == t]


def test_coordinates_three_printed_forms():
    for s, lat, lon in [("in 19° 48' north latitude and 85° 49' east longitude", 19.8, 85.8167),
                        ("in 19° 53' N, and 86° 6'E.", 19.8833, 86.1),
                        ("situated in 20° 16' N.and 85° 47' E.", 20.2667, 85.7833)]:
        f = facts(s, "coordinates")
        assert len(f) == 1 and f[0]["value"]["lat"] == lat and f[0]["value"]["lon"] == lon, s


def test_population_pairs_only_adjacent_number_and_year():
    f = facts("The population of the subdivision was 359,236 in 1901, as against 331,423 in 1891.", "population")
    assert sorted((x["as_of_year"], x["value"]["number"]) for x in f) == [(1891, 331423), (1901, 359236)]


def test_population_from_to_does_not_invent_a_year():
    f = facts("The population rose from 28,794 in 1891 to 49,334 within the decade.", "population")
    assert [(x["as_of_year"], x["value"]["number"]) for x in f] == [(1891, 28794)]


def test_population_census_of_form():
    f = facts("a population, according to the census of 1901, of 1,017,284 souls", "population")
    assert [(x["as_of_year"], x["value"]["number"]) for x in f] == [(1901, 1017284)]


def test_area_and_height():
    assert facts("It extends over an area of 2,499 square miles.", "area")[0]["value"] == {"number": 2499, "unit": "sq_miles"}
    assert facts("A hill, with a height of 100 feet above", "height")[0]["value"] == {"number": 100, "unit": "feet"}


def test_distance_with_number_word():
    f = facts("A hill situated one mile south of Khurda town", "distance")
    assert f == [] or f[0]["value"]["miles"] == 1  # 'mile' singular is accepted by the pattern
    f = facts("situated 4 miles south-west of Bhubaneswar", "distance")
    assert f[0]["value"] == {"miles": 4, "relation": "south-west of", "to": "Bhubaneswar"}


def test_evidence_offsets_point_at_quote():
    text = "Some words. The population of the town in 1901 was 49,364 persons."
    f = facts(text, "population")[0]
    ev = f["evidence"][0]
    assert text[ev["char_start"]:ev["char_end"]] == ev["quote"]


def test_consistency_flags_two_figures_for_same_year():
    text = "The population of the town in 1901 was 49,364. The population rose from 28,794 in 1891 to 49,334 in 1901."
    c = consistency(extract(P(text), "pl_x-0000"))
    assert len(c) == 1 and c[0]["values"] == [49334, 49364]


def test_area_reads_the_raised_decimal_point_as_printed_or_misread():
    assert facts("The area within municipal limits is 4°03 square miles.", "area")[0]["value"] == {"number": 4.03, "unit": "sq_miles"}
    assert facts("an estate with an area of 5·8 square miles.", "area")[0]["value"] == {"number": 5.8, "unit": "sq_miles"}
    assert facts("covering an area of 8:11 acres.", "area")[0]["value"] == {"number": 8.11, "unit": "acres"}


def pops(text):
    return sorted((x.get("as_of_year"), x["value"]["number"]) for x in facts(text, "population"))


def test_fact_page_is_the_page_the_figure_is_printed_on_not_where_the_paragraph_starts():
    text = "The town lies on the coast. " * 3 + "Its area is 4 square miles."
    spans = [{"page": "286", "start": 0, "end": 40}, {"page": "287", "start": 40, "end": 200}]
    f = next(x for x in extract(P(text), "pl_x-0000", spans) if x["type"] == "area")
    assert f["notes"].startswith("page 287;")


def test_population_returned_at_and_inhabitants_phrasings():
    assert pops("During the next 10 years the population increased by 15·4 per cent., being returned "
                "in 1881 at 888,592 souls, but it is probable") == [(1881, 888592)]
    assert pops("the number of inhabitants in 1891 was returned at 944,998, representing an increase") == [(1891, 944998)]


def test_population_with_the_census_year_elsewhere_in_the_clause():
    assert pops("and the census of 1901 showed that the population had risen to 1,017,284, i.e. by 7·6 per cent.") == [(1901, 1017284)]
    assert pops("According to the census of 1901, the population is 3,053: it is almost exclusively Hindu") == [(1901, 3053)]
    assert pops("The town, which has a population of 3,424 according to the census of 1901, contains") == [(1901, 3424)]


def test_population_without_a_year_is_kept_without_one():
    assert pops("its area was 20 square miles, and its population 10,000 souls.") == [(None, 10000)]
    assert pops("it measured 14 square miles, and Contained 3,000 souls.") == [(None, 3000)]
    assert pops("The seventh tract measured 23 square miles with 7,000 souls, and lay") == [(None, 7000)]
    assert pops("Relief measures were necessary in 365 square miles, contain: ing 102,000 souls, the area") == [(None, 102000)]
    assert pops("with an area of 10 square miles and a population of 4,000 souls.") == [(None, 4000)]


def test_population_does_not_take_a_year_when_the_clause_has_two():
    assert pops("The population of 49,334 in the census of 1901 compares with the census of 1891.") == [(None, 49334)]
    assert pops("a population of 5,000, against 4,000 at the census of 1891 and 3,000 at the census of 1881") == [(None, 5000)]


def test_population_ignores_density_and_other_counts():
    assert pops("the population, which falls to 254 persons to the square mile") == []
    assert pops("only 351 being Musalmans and 110 Christians, the population being Hindu") == []


def test_area_in_acres_for_land_units():
    a = lambda s: [x["value"] for x in facts(s, "area")]
    assert a("has an area, according to the latest survey, of 618,154 acres, of") == [{"number": 618154, "unit": "acres"}]
    assert a("the Ekhrajat Mahals, extending over 68,000 acres of land") == [{"number": 68000, "unit": "acres"}]
    assert a("The area held under the direct management of Government in this estate is 565,356 acres comprised") == \
        [{"number": 565356, "unit": "acres"}]
    assert a("1,309 villages containing 540,376 acres lie in the Khurda subdivision") == [{"number": 540376, "unit": "acres"}]
    assert a("the outturn was 4,500 maunds from 900 acres under sugarcane") == []


def test_area_tolerates_ocr_misreads_of_square():
    assert [x["value"] for x in facts("having an area of 113 squsre miles, while", "area")] == [{"number": 113, "unit": "sq_miles"}]


def test_population_ignores_percentages_and_millions():
    assert pops("according to the statistics obtained at the census of 1901, 60 per cent. of the population are") == []
    assert pops("the Province, with its population of 24 million of souls, all was darkness") == []


def test_counts_without_a_year_are_not_numeric_conflicts():
    text = "its population 10,000 souls; and its population 2,000 souls."
    assert consistency(extract(P(text), "pl_x-0000")) == []


TABLE = ("~\" 'Towns. | Villages, Puri ... ... 1,528 1 1,889 658,048 431 Khurda ... ... 971 ... 1,212 359,236 370 "
         "District total 2,499 1 3,101 1,017,284 407 +7·6")


def test_census_table_rows_give_area_and_population_with_the_census_year_from_before():
    fs = extract(P(TABLE), "pl_x-0000", before="The salient statistics of the census of 1901 are reproduced below :-")
    got = sorted((f["type"], f["value"]["number"], f.get("as_of_year"), f["notes"].split("table row: ")[1]) for f in fs)
    assert got == [("area", 971, None, "Khurda"), ("area", 1528, None, "Puri"), ("area", 2499, None, "District total"),
                   ("population", 359236, 1901, "Khurda"), ("population", 658048, 1901, "Puri"),
                   ("population", 1017284, 1901, "District total")]
    for f in fs:
        ev = f["evidence"][0]
        assert TABLE[ev["char_start"]:ev["char_end"]] == ev["quote"]


def test_census_table_row_must_agree_with_its_own_density():
    bad = "Puri ... ... 1,628 1 1,889 658,048 431"  # one misread area digit breaks population / area = density
    assert extract(P(bad), "pl_x-0000", before="census of 1901") == []


def test_census_table_needs_a_census_year():
    assert extract(P(TABLE), "pl_x-0000", before="The following figures are reproduced below") == []


def test_census_table_rows_are_different_places_not_conflicts():
    assert consistency(extract(P(TABLE), "pl_unlinked", before="census of 1901")) == []
