"""DP-09 entity resolution and geocoding (spec §8.10). Synthetic candidates; no downloads needed."""

from __future__ import annotations

import pytest

from pipeline import resolve as rs

# --- names ----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("old,new", [
    ("Pooree", "Puri"), ("Konārak", "Konark"), ("Khurdā", "Khordha"), ("Bhubaneswar", "Bhubaneshwar"),
    ("Kākatpur", "Kakatapur"), ("Bānpur", "Banapur"), ("Pipli", "Pipili"), ("Satyabādī", "Satyabadi"),
])
def test_old_and_modern_spellings_share_a_key(old, new):
    assert rs.name_score(old, [new]) >= rs.NAME_STRONG


@pytest.mark.parametrize("a,b", [("Puri", "Pipli"), ("Atri", "Arei"), ("Baral", "Barang"), ("Dhauli", "Dhanua")])
def test_different_places_do_not(a, b):
    assert rs.name_score(a, [b]) < rs.NAME_STRONG


def test_type_words_are_not_part_of_the_name():
    assert rs.norm("Biswanāth Hill") == rs.norm("Biswanath")
    assert rs.norm("Khurdā subdivision") == rs.norm("Khurda")


# --- tiers ----------------------------------------------------------------------------------------------

PURI = {"place_id": "pl_puri", "type": "town", "names": [{"text": "Purī", "lang": "en", "kind": "primary"}],
        "geometry": {"kind": "point", "coordinates": [85.8167, 19.8], "quality": "heading"}}
JATNI = {"place_id": "pl_jatni", "type": "village", "names": [{"text": "Jatnī", "lang": "en", "kind": "primary"}],
         "parent_ids": ["pl_khurda-sub"]}
ESTATE = {"place_id": "pl_kotdesh", "type": "estate", "names": [{"text": "Kotdesh", "lang": "en", "kind": "primary"}]}


def _cand(cid, name, lon, lat, kind="P", admin2="386", qid=None, alt=()):
    return {"cid": cid, "names": [name, *alt], "lon": lon, "lat": lat, "fclass": kind, "admin2": admin2,
            "wikidata": qid, "geonames": cid if cid.isdigit() else None, "labels": {"en": name}}


def test_name_type_and_heading_coordinates_agreeing_is_high():
    link = rs.match(PURI, [_cand("1259184", "Puri", 85.825, 19.798, admin2="387", qid="Q207799"),
                           _cand("Q1", "Pipili", 85.83, 20.11)])
    assert link["tier"] == "high" and link["candidate"]["wikidata"] == "Q207799"
    assert link["signals"]["distance_km"] < 2


def test_a_name_match_far_from_the_heading_coordinates_is_not_high():
    link = rs.match(PURI, [_cand("Q2", "Puri", 83.0, 21.5)])
    assert link["tier"] in ("medium", "low")


def test_containment_in_the_parents_modern_district_counts_like_coordinates():
    c = [_cand("Q3", "Jatni", 85.70, 20.17, admin2="386")]
    assert rs.match(JATNI, c, expected_admin2={"386"})["tier"] == "high"
    assert rs.match(JATNI, c, expected_admin2={"387"})["tier"] == "medium"


def test_two_equally_good_candidates_are_left_for_review():
    c = [_cand("Q4", "Jatni", 85.70, 20.17), _cand("Q5", "Jatni", 85.50, 20.30)]
    link = rs.match(JATNI, c, expected_admin2={"386"})
    assert link["tier"] == "medium" and link["runner_up"]


def test_the_same_place_in_two_sources_is_one_candidate():
    groups = rs.merge([_cand("1266616", "Jatni", 85.70, 20.17, qid="Q6"),
                       _cand("Q6", "Jatni", 85.701, 20.171, qid="Q6")])
    assert len(groups) == 1 and groups[0]["geonames"] == "1266616" and groups[0]["wikidata"] == "Q6"


def test_old_estates_and_admin_units_are_never_matched_automatically():
    link = rs.match(ESTATE, [_cand("Q7", "Kotdesh", 85.9, 20.0)], expected_admin2={"386"})
    assert link["tier"] != "high"


def test_no_candidate_means_a_candidate_ghost():
    assert rs.match(ESTATE, [_cand("Q8", "Bhubaneswar", 85.8, 20.3)])["tier"] == "none"


def test_hills_need_a_hill_and_villages_a_settlement():
    hill = {**JATNI, "type": "hill", "names": [{"text": "Chitrakot Hill", "lang": "en", "kind": "primary"}]}
    assert rs.match(hill, [_cand("Q9", "Chitrakot", 85.7, 20.1, kind="P")], expected_admin2={"386"})["tier"] != "high"
    assert rs.match(hill, [_cand("Q9", "Chitrakot", 85.7, 20.1, kind="T")], expected_admin2={"386"})["tier"] == "high"


# --- historic names from the source's own text -----------------------------------------------------------

PASSAGES = {"ps_1": {"passage_id": "ps_1", "page": "287",
                     "text": "the town was sometimes called Jagannath-Pooree; and Mr. W. Hamilton mentions it as Pooree"}}


def test_a_historic_name_needs_its_quote_in_the_source():
    rows = [{"place_id": "pl_puri", "name": "Jagannath-Pooree", "passage_id": "ps_1",
             "quote": "the town was sometimes called Jagannath-Pooree"}]
    assert rs.check_historic(rows, PASSAGES, {"pl_puri"}) == []
    bad = [{**rows[0], "quote": "the town was called Pooree by all"}]
    assert any("quote" in e for e in rs.check_historic(bad, PASSAGES, {"pl_puri"}))
    bad = [{**rows[0], "name": "Juggernaut"}]
    assert any("not in its quote" in e for e in rs.check_historic(bad, PASSAGES, {"pl_puri"}))


# --- publishing ---------------------------------------------------------------------------------------

def test_a_high_link_adds_ids_names_and_a_point_without_replacing_the_heading():
    link = {"place_id": "pl_puri", "tier": "high", "candidate": {
        "wikidata": "Q207799", "geonames": "1259184", "lon": 85.825, "lat": 19.798,
        "labels": {"en": "Puri", "or": "ପୁରୀ", "hi": "पुरी"}, "aliases": ["Pooree", "Sri Jagannath Dham"]}}
    p = rs.apply_link(dict(PURI, names=list(PURI["names"])), link)
    assert p["external_ids"] == {"wikidata": "Q207799", "geonames": "1259184"}
    assert p["geometry"]["quality"] == "heading"  # the 1908 heading stays; the modern point is in the link
    assert {"text": "ପୁରୀ", "lang": "or", "script": "Orya", "kind": "primary", "source_id": "wikidata"} in p["names"]
    assert {"text": "Pooree", "lang": "en", "kind": "alias", "source_id": "wikidata"} in p["names"]
    assert not any(n["text"] == "Sri Jagannath Dham" for n in p["names"])  # another name, not a spelling
    j = rs.apply_link(dict(JATNI, names=list(JATNI["names"])), {**link, "place_id": "pl_jatni"})
    assert j["geometry"] == {"kind": "point", "coordinates": [85.825, 19.798], "quality": "exact",
                             "source": "wikidata:Q207799"}


def test_unmatched_places_become_uncertain_and_review_tiers_change_nothing():
    assert rs.apply_link(dict(ESTATE), {"place_id": "pl_kotdesh", "tier": "none"})["status"] == "uncertain"
    p = rs.apply_link(dict(ESTATE), {"place_id": "pl_kotdesh", "tier": "medium", "candidate": {"wikidata": "Q1"}})
    assert "external_ids" not in p and p.get("status") != "uncertain"


def test_same_name_close_together_in_two_sources_is_one_candidate_without_a_link():
    groups = rs.merge([_cand("1266616", "Khordha", 85.616, 20.183, admin2="386"),
                       _cand("Q2241122", "Khordha", 85.62, 20.18, qid="Q2241122", admin2=None)])
    assert len(groups) == 1 and groups[0]["wikidata"] == "Q2241122" and groups[0]["admin2"] == "386"
    far = rs.merge([_cand("1", "Jatni", 85.70, 20.17), _cand("Q9", "Jatni", 85.50, 20.30, qid="Q9")])
    assert len(far) == 2


def test_expected_districts_come_from_the_parent_or_the_whole_old_district():
    places = [{"place_id": "pl_d", "type": "district", "names": [{"text": "Purī", "lang": "en", "kind": "primary"}]},
              {"place_id": "pl_ks", "type": "subdivision", "parent_ids": ["pl_d"],
               "names": [{"text": "Khurdā subdivision", "lang": "en", "kind": "primary"}]},
              {"place_id": "pl_kt", "type": "town", "parent_ids": ["pl_ks"], "names": [{"text": "Khurdā", "lang": "en", "kind": "primary"}]},
              {"place_id": "pl_pt", "type": "town", "parent_ids": ["pl_d"], "names": [{"text": "Purī", "lang": "en", "kind": "primary"}]},
              {"place_id": "pl_v", "type": "village", "parent_ids": ["pl_ks"], "names": [{"text": "Jatnī", "lang": "en", "kind": "primary"}]},
              {"place_id": "pl_w", "type": "village", "parent_ids": ["pl_d"], "names": [{"text": "Atri", "lang": "en", "kind": "primary"}]}]
    links = {"pl_kt": {"tier": "high", "candidate": {"admin2": "386"}}, "pl_pt": {"tier": "high", "candidate": {"admin2": "387"}}}
    assert rs.expected_admin2(places[4], places, links) == {"386"}
    assert rs.expected_admin2(places[5], places, links) == {"386", "387"}


def test_a_rival_must_pass_every_check_and_be_named_as_well():
    town = {**PURI, "place_id": "pl_k", "names": [{"text": "Khurdā", "lang": "en", "kind": "primary"}],
            "geometry": {"kind": "point", "coordinates": [85.6333, 20.1833], "quality": "heading"}}
    c = [_cand("Q1", "Khordha", 85.62, 20.18, alt=("Khurda",)), _cand("Q2", "Khordha district", 85.6, 20.2, kind="A"),
         _cand("Q3", "Korada", 85.7, 20.25)]
    assert rs.match(town, c)["tier"] == "high"


def test_odia_and_hindi_labels_lose_qualifiers_and_must_be_names_not_descriptions():
    c = {"wikidata": "Q4817538", "lon": 85.3, "lat": 20.15, "aliases": [],
         "labels": {"en": "Atri", "or": "ଅଟ୍ରି ଉଷ୍ମପ୍ରସ୍ରବଣ", "hi": "अट्री, खोर्धा"}}
    atri = {"place_id": "pl_atri", "type": "village", "names": [{"text": "Atri", "lang": "en", "kind": "primary"}]}
    p = rs.apply_link(atri, {"place_id": "pl_atri", "tier": "high", "candidate": c})
    assert [n["text"] for n in p["names"] if n["lang"] != "en"] == ["अट्री"]


def test_owner_decisions_accept_the_proposed_candidate_or_make_a_ghost():
    link = {"place_id": "pl_dhauli", "tier": "medium", "candidate": {"wikidata": "Q3498218", "geonames": "1272806"}}
    assert rs._decide(link, {"place_id": "pl_dhauli", "decision": "accept", "wikidata": "Q3498218"})["tier"] == "high"
    assert rs._decide(link, {"place_id": "pl_dhauli", "decision": "ghost"})["tier"] == "none"
    with pytest.raises(ValueError):
        rs._decide(link, {"place_id": "pl_dhauli", "decision": "accept", "wikidata": "Q1"})


# --- the source's own distances (D-47) -----------------------------------------------------------------

def _dist(pid, miles, to, rel="from"):
    return {"place_id": pid, "type": "distance", "value": {"miles": miles, "relation": rel, "to": to}}


def _link(pid, lon, lat, tier="high"):
    return {"place_id": pid, "tier": tier, "candidate": {"lon": lon, "lat": lat}, "signals": {}}


def test_a_point_far_from_where_the_source_puts_it_is_sent_to_review():
    places = [{"place_id": "pl_k", "type": "town", "names": [{"text": "Khurdā", "lang": "en", "kind": "primary"}]},
              {"place_id": "pl_a", "type": "village", "names": [{"text": "Atri", "lang": "en", "kind": "primary"}]}]
    links = {"pl_k": _link("pl_k", 85.616, 20.183), "pl_a": _link("pl_a", 85.30, 20.15)}  # 33 km; text says 8 miles
    out = rs.check_distances(links, [_dist("pl_a", 8, "Khurda")], places)
    assert out["pl_a"]["tier"] == "medium"
    assert out["pl_a"]["signals"]["distances"][0] == {"to": "Khurda", "miles": 8, "km": 33.2, "agrees": False}


def test_road_distances_and_moved_town_centres_are_tolerated():
    places = [{"place_id": "pl_p", "type": "town", "names": [{"text": "Purī", "lang": "en", "kind": "primary"}]},
              {"place_id": "pl_s", "type": "village", "names": [{"text": "Satyabādī", "lang": "en", "kind": "primary"}]}]
    links = {"pl_p": _link("pl_p", 85.825, 19.798), "pl_s": _link("pl_s", 85.814, 19.947)}  # 16.6 km; 12 miles
    out = rs.check_distances(links, [_dist("pl_s", 12, "Puri town", "north of")], places)
    assert out["pl_s"]["tier"] == "high" and out["pl_s"]["signals"]["distances"][0]["agrees"]


def test_distances_to_unknown_or_unlinked_places_are_not_evidence():
    places = [{"place_id": "pl_s", "type": "village", "names": [{"text": "S", "lang": "en", "kind": "primary"}]}]
    links = {"pl_s": _link("pl_s", 85.8, 19.9)}
    out = rs.check_distances(links, [_dist("pl_s", 12, "the"), _dist("pl_s", 5, "Cuttack")], places)
    assert out["pl_s"]["tier"] == "high" and out["pl_s"]["signals"].get("distances", []) == []


def test_an_owner_can_reject_a_candidate():
    link = {"place_id": "pl_b", "tier": "low", "candidate": {"geonames": "1"}}
    assert rs._decide(link, {"place_id": "pl_b", "decision": "reject"})["tier"] == "rejected"
    assert rs.apply_link({"place_id": "pl_b", "names": [], "status": "existing"}, {"tier": "rejected"})["status"] == "existing"


def test_twice_the_printed_distance_is_too_far():
    places = [{"place_id": "pl_p", "type": "town", "names": [{"text": "Purī", "lang": "en", "kind": "primary"}]},
              {"place_id": "pl_b", "type": "village", "names": [{"text": "Baral", "lang": "en", "kind": "primary"}]}]
    links = {"pl_p": _link("pl_p", 85.825, 19.798), "pl_b": _link("pl_b", 86.322, 20.124, "medium")}  # 63 km; 18 miles
    out = rs.check_distances(links, [_dist("pl_b", 18, "Puri town", "north of")], places)
    assert out["pl_b"]["signals"]["distances"][0]["agrees"] is False


def test_a_rejection_applies_only_to_the_candidate_it_names():
    link = {"place_id": "pl_b", "tier": "low", "candidate": {"geonames": "1"}}
    assert rs._decide(link, {"place_id": "pl_b", "decision": "reject", "geonames": "1"})["tier"] == "rejected"
    assert rs._decide(link, {"place_id": "pl_b", "decision": "reject", "geonames": "2"})["tier"] == "low"
