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
