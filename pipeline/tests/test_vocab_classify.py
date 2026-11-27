from pipeline.classify import classify_entry, place_id
from pipeline.vocab import compile_vocab, tag


def test_vocab_tags_period_spellings():
    v = compile_vocab()
    p = {"passage_id": "ps_t_00", "entry_id": "en_t", "text": "During the Durga pujd and the car festival, paddy and salt were sold."}
    terms = {(t["category"], t["term"]) for t in tag(p, v)}
    assert {("festival", "durga_puja"), ("festival", "rath_jatra"), ("crop", "rice"), ("trade_item", "salt")} <= terms


def test_classify_descriptors():
    E = lambda h, t: {"heading": h, "text": t}
    assert classify_entry(E("Purī", "Pari.— Headquarters of the district situated on the shore"))[0] == "town"
    assert classify_entry(E("Satyabādī", "Satyabadi—A villoge in the headquarters subdivision"))[0] == "village"
    assert classify_entry(E("Kodhār", "Kodhar.—aAn estate situated in the extreme north-east"))[0] == "estate"
    assert classify_entry(E("Biswanāth Hill", "Biswanath Hill.—The highest in a line of low hills"))[0] == "hill"
    assert classify_entry(E("Khurdā subdivision", "Khurda Subdivision —Western subdivision of the district"))[0] == "subdivision"


def test_place_ids_are_stable_and_ascii():
    assert place_id("Purī", "town") == place_id("Purī", "town")
    assert place_id("Purī", "town").startswith("pl_puri-")


def test_district_place_comes_from_the_source_config():
    from pipeline.classify import district_place
    d = district_place("Purī", "omalley-puri-1908")
    assert d["type"] == "district" and d["names"][0]["text"] == "Purī"
    assert d["place_id"].startswith("pl_puri-district-")
    assert d["entry_ids"] == []  # its facts are linked one by one (fact_subjects.yaml), never a whole chapter
    assert d["place_id"] == district_place("Purī", "omalley-puri-1908")["place_id"]
