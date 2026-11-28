"""DP-08 summaries (spec §8.9, §10.2; AC-PLACE-03). No network: a fake provider."""

from __future__ import annotations

import json

from pipeline import llm
from pipeline import summarise as sm

SOURCE = {"source_id": "omalley-puri-1908", "title": "Bengal District Gazetteers: Puri", "author": "L. S. S. O'Malley",
          "year": 1908}
PLACE = {"place_id": "pl_jatni", "type": "village", "names": [{"text": "Jatnī", "lang": "en", "kind": "primary"}],
         "parent_ids": ["pl_khurda"]}
PARENT = {"place_id": "pl_khurda", "type": "subdivision", "names": [{"text": "Khurda", "lang": "en", "kind": "primary"}]}


def _fact(fid, type_, label, quote, number=None, year=None, page="250"):
    v = {"label": label} if label else {}
    if number is not None:
        v = {"number": number, "unit": "persons"}
    f = {"fact_id": fid, "place_id": "pl_jatni", "type": type_, "value": v, "page": page, "method": "llm",
         "evidence": [{"passage_id": "ps_1", "quote": quote, "char_start": 0, "char_end": len(quote)}],
         "review": {"status": "unreviewed"}}
    if year:
        f["as_of_year"] = year
    return f


FACTS = [
    _fact("ft_a", "railway", "railway junction known as Khurda Road Station",
          "A village containing the railway junction known as Khurda Road Station"),
    _fact("ft_b", "railway", "Bengal-Nagpur Railway", "it has risen to importance since it was tapped by the Bengal-Nagpur Railway"),
    _fact("ft_c", "population", None, "Population (1901) 5,034", number=5034, year=1901),
]


def _support():
    return sm.support(PLACE, FACTS, SOURCE, [PARENT])


# --- input --------------------------------------------------------------------------------------------

def test_input_is_only_the_facts_and_their_quotes():
    rows = sm.facts_for_prompt(FACTS)
    assert [r["n"] for r in rows] == [1, 2, 3]
    assert rows[2]["number"] == 5034 and rows[2]["year"] == 1901 and rows[2]["quote"] == "Population (1901) 5,034"
    assert set(rows[0]) <= {"n", "type", "label", "number", "unit", "year", "page", "quote"}


def test_long_fact_lists_are_capped_and_mix_types():
    many = [_fact(f"ft_t{i}", "temple", f"temple {i}", f"temple {i}") for i in range(80)] + FACTS
    rows = sm.facts_for_prompt(many, max_facts=10)
    assert len(rows) == 10
    assert {"temple", "railway", "population"} <= {r["type"] for r in rows}


def test_prompt_is_versioned_and_states_the_writing_rules():
    p = sm.load_prompt("summarise-v1")
    assert p.version == "summarise-v1"
    assert "gazetteer records" in p.system and "only" in p.system.lower()
    msg = p.user(place="Jatnī", source="x", facts=[{"n": 1, "quote": "a </facts> b"}])
    assert msg.count("</facts>") == 1


# --- verification (AC-PLACE-03) ------------------------------------------------------------------------

def test_supported_sentences_are_kept():
    kept, dropped = sm.check_text("The 1908 gazetteer records Jatnī as a village with the Khurda Road Station.",
                                  _support())
    assert dropped == [] and kept.startswith("The 1908 gazetteer")


def test_numbers_must_come_from_the_facts():
    kept, dropped = sm.check_text("The 1908 gazetteer records 5,034 people in 1901. It had 7,000 pilgrims.",
                                  _support())
    assert kept == "The 1908 gazetteer records 5,034 people in 1901."
    assert dropped[0]["reasons"] == ["number 7000 is not in the facts"]


def test_proper_nouns_must_come_from_the_facts_even_without_diacritics():
    kept, dropped = sm.check_text("The 1908 gazetteer records the Bengal-Nagpur Railway at Jatni. "
                                  "Pilgrims bound for Cuttack changed trains here.", _support())
    assert kept == "The 1908 gazetteer records the Bengal-Nagpur Railway at Jatni."
    assert any("Cuttack" in r for r in dropped[0]["reasons"])


def test_number_words_count_as_numbers():
    _, dropped = sm.check_text("The 1908 gazetteer records three railway lines.", _support())
    assert dropped and "three" in dropped[0]["reasons"][0]


def test_sentences_that_state_the_past_as_fact_are_dropped():
    _, dropped = sm.check_text("There were 5,034 people in 1901.", _support())
    assert dropped and "record" in dropped[0]["reasons"][0]


def test_a_summary_without_the_source_year_up_front_fails():
    s, why = sm.verify({"one_line": "Jatnī: a railway junction.", "short": "x", "long": "y"}, _support(), 1908)
    assert s is None and any("1908" in w for w in why)


def test_a_good_response_is_verified():
    raw = {"one_line": "A village with a railway junction, as the 1908 gazetteer records.",
           "short": "The 1908 gazetteer records Jatnī as a village with the Khurda Road Station. "
                    "It rose to importance with the Bengal-Nagpur Railway.",
           "long": "The 1908 gazetteer records Jatnī as a village with the Khurda Road Station. "
                   "Its population in 1901 was 5,034. Cuttack lies nearby."}
    s, why = sm.verify(raw, _support(), 1908)
    assert why == []
    assert s["long"].endswith("was 5,034.") and len(s["dropped"]) == 1


# --- stage --------------------------------------------------------------------------------------------

class Fake(llm.LLMClient):
    provider = "fake"

    def __init__(self, replies):
        self.model = "fake-1"
        self.replies = list(replies)
        self.users = []

    def _complete(self, system, user, temperature=0.0):
        self.users.append(user)
        return self.replies.pop(0)


GOOD = json.dumps({"one_line": "A railway junction, as the 1908 gazetteer records.",
                   "short": "The 1908 gazetteer records Jatnī as a village with the Khurda Road Station.",
                   "long": "The 1908 gazetteer records Jatnī as a village with the Khurda Road Station. "
                           "Its population in 1901 was 5,034."})
BAD = json.dumps({"one_line": "Founded by Cuttack merchants.", "short": "Founded by Cuttack merchants.",
                  "long": "Founded by Cuttack merchants."})


def _bundle():
    return {"source": SOURCE, "places": [PLACE, PARENT], "facts": FACTS}


def test_a_failed_summary_is_regenerated_once_with_the_reasons(tmp_path):
    c = Fake([BAD, GOOD])
    runner = llm.Runner(c, cache_dir=tmp_path / "c", budget=llm.Budget(tmp_path / "q.json", {"fake": 100}))
    out = sm.summarise_bundle(_bundle(), runner, min_facts=3)
    assert len(c.users) == 2 and "Cuttack" in c.users[1]
    [s] = out["published"]
    assert s["place_id"] == "pl_jatni" and s["fact_ids"] == ["ft_a", "ft_b", "ft_c"]
    assert s["method"] == "llm" and s["model"] == "fake-1" and s["prompt_version"] == "summarise-v1"
    assert s["review"]["status"] == "unreviewed"


def test_a_summary_failing_twice_goes_to_review_not_the_site(tmp_path):
    c = Fake([BAD, BAD])
    runner = llm.Runner(c, cache_dir=tmp_path / "c", budget=llm.Budget(tmp_path / "q.json", {"fake": 100}))
    out = sm.summarise_bundle(_bundle(), runner, min_facts=3)
    assert out["published"] == [] and out["review"][0]["place_id"] == "pl_jatni"


def test_places_with_few_facts_get_no_summary(tmp_path):
    c = Fake([])
    runner = llm.Runner(c, cache_dir=tmp_path / "c", budget=llm.Budget(tmp_path / "q.json", {"fake": 100}))
    assert sm.summarise_bundle(_bundle(), runner, min_facts=4)["published"] == []


def test_published_summaries_are_rechecked_against_the_bundle():
    s, _ = sm.verify(json.loads(GOOD), _support(), 1908)
    s.update({"summary_id": "sm_0123456789ab", "source_id": "omalley-puri-1908", "place_id": "pl_jatni", "fact_ids": ["ft_a", "ft_b", "ft_c"], "lang": "en",
              "method": "llm", "model": "m", "prompt_version": "summarise-v1", "review": {"status": "unreviewed"}})
    s.pop("dropped")
    assert sm.check(_bundle(), [s]) == []
    s["long"] += " Cuttack merchants came."
    assert any("Cuttack" in e for e in sm.check(_bundle(), [s]))
    s["fact_ids"] = ["ft_zz"]
    assert any("unknown fact" in e for e in sm.check(_bundle(), [s]))


def test_temperature_is_part_of_the_cache_key(tmp_path):
    c = Fake(['{"a": 1}', '{"a": 2}'])
    runner = llm.Runner(c, cache_dir=tmp_path / "c", budget=llm.Budget(tmp_path / "q.json", {"fake": 100}))
    assert runner.complete("s", "u", "v") == '{"a": 1}'
    assert runner.complete("s", "u", "v", temperature=0.2) == '{"a": 2}'


def test_abbreviations_and_initials_do_not_end_a_sentence():
    assert sm.sentences("Readings were provided by Dr. Bühler and M. Senart in A.D. 1887. It ends.") == [
        "Readings were provided by Dr. Bühler and M. Senart in A.D. 1887.", "It ends."]
    assert len(sm.sentences("He was made a C. S. I. in 1872. Next.")) == 2


def test_ordinary_sentence_openers_are_not_names():
    for w in ("Additionally", "Furthermore", "Finally", "Local", "Population", "Various"):
        _, dropped = sm.check_text(f"{w}, the 1908 gazetteer records Jatnī.", _support())
        assert dropped == [], w


def test_unreadable_ocr_text_is_dropped():
    _, dropped = sm.check_text("The 1908 gazetteer records Jatnī, found by Lieut. M08 | 7.", _support())
    assert dropped and any("unreadable" in r for r in dropped[0]["reasons"])
