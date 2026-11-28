"""DP-15 Assemble (spec §8.16): the curated bundle the site is built from, validated.

Writes data/curated/<source_id>/ (committed; the site reads only these files):
  source.json    citation fields of the source (source-summary.schema.json)
  places.json    places (place.schema.json); a place DP-03 could not classify is held back until
                 reviewed (its entry then names no place); parents from the district and each entry's subdivision
                 link, point geometry from coordinates printed in the entry heading
  facts.json     accepted facts linked to a place (fact.schema.json), with the page the figure is on;
                 unlinked figures are left out (D-39) but stay in the passages; verified DP-06 facts
                 (method llm) go to their entry's place
  entries.json   gazetteer entries and chapter sections (entry.schema.json), each with its place
  passages.json  every passage (passage.schema.json); IDs are stable (FR-TEXT-06)

check() is the publication gate: every record validates against its schema (TS-DATA-10), every
reference resolves (TS-DATA-09), and every quote sits at its offsets in its passage (TS-DATA-05).

Usage: python -m pipeline.assemble --source omalley-puri-1908
"""

from __future__ import annotations

import argparse
import json
import re
import sys

from pipeline.ocr import fold
from pipeline.util import DATA_DIR, INTERIM_DIR, log, read_jsonl, read_yaml
from pipeline.validate import validator

LG = log("DP-15")
OUT = DATA_DIR / "curated"
SOURCE_FIELDS = ("source_id", "title", "author", "year", "credit_line", "scan_ref", "acquired_from", "rights_basis")
PLACE_FIELDS = ("place_id", "type", "names", "parent_ids", "child_ids", "geometry", "status", "external_ids", "review")
FACT_TYPES = set(validator("fact.schema.json").schema["properties"]["type"]["enum"])
SCHEMAS = {"places": "place.schema.json", "facts": "fact.schema.json", "passages": "passage.schema.json",
           "entries": "entry.schema.json"}


def _page(notes: str | None) -> str | None:
    m = re.match(r"page (\S+?);", notes or "")
    return m.group(1) if m else None


def _name(p: dict) -> str:
    return fold(p["names"][0]["text"])


def bundle(places: list[dict], facts: list[dict], attrs: list[dict], passages: list[dict], entries: list[dict],
           source: dict, llm_facts: list[dict] | None = None) -> dict:
    types = set(validator("place.schema.json").schema["properties"]["type"]["enum"])
    held = sorted(p["place_id"] for p in places if p["type"] not in types)  # e.g. a bare cross-reference
    places = [p for p in places if p["type"] in types]
    out_places = {p["place_id"]: {k: v for k, v in p.items() if k in PLACE_FIELDS} for p in places}
    district = next((p["place_id"] for p in places if p["type"] == "district"), None)
    subdivisions = {_name(p).removesuffix(" subdivision"): p["place_id"] for p in places if p["type"] == "subdivision"}
    text = {e["entry_id"]: e.get("text", "") for e in entries}
    for p in places:  # "the headquarters subdivision": the one whose own entry opens by saying so
        if p["type"] == "subdivision" and any("headquarters subdivision" in fold(text.get(e, ""))[:160]
                                              for e in p.get("entry_ids", [])):
            subdivisions["headquarters"] = p["place_id"]
    parent: dict[str, str] = {}
    for a in sorted(attrs, key=lambda a: a["fact_id"]):
        pid = a["place_id"]
        if pid not in out_places:
            continue
        if a["type"] == "coordinates" and "geometry" not in out_places[pid]:
            v = a["value"]
            out_places[pid]["geometry"] = {"kind": "point", "coordinates": [v["lon"], v["lat"]],
                                           "quality": v.get("quality", "heading"), "source": a["fact_id"]}
        elif a["type"] == "admin_link" and pid not in parent:
            sub = subdivisions.get(fold(a["value"]["subdivision"]).strip())
            if sub and sub != pid:
                parent[pid] = sub
    for pid, p in out_places.items():
        if pid == district:
            continue
        up = parent.get(pid) or district
        if up:
            p["parent_ids"] = [up]
            out_places[up].setdefault("child_ids", []).append(pid)
    for p in out_places.values():
        if "child_ids" in p:
            p["child_ids"] = sorted(p["child_ids"])
    place_of = {e: p["place_id"] for p in places for e in p.get("entry_ids", [])}
    out_facts = []
    for f in sorted(facts, key=lambda f: f["fact_id"]):
        if f["place_id"] not in out_places or f["type"] not in FACT_TYPES:
            continue
        g = {k: v for k, v in f.items() if k != "notes"}
        page = _page(f.get("notes"))
        if page:
            g["page"] = page
        out_facts.append(g)
    for f in sorted(llm_facts or [], key=lambda f: f["fact_id"]):  # DP-06, verified: to the entry's place
        pid = place_of.get(f["entry_id"])
        if pid in out_places:
            out_facts.append({**{k: v for k, v in f.items() if k != "entry_id"}, "place_id": pid})
    out_entries = [{"entry_id": e["entry_id"], "source_id": e["source_id"], "kind": e["kind"], "heading": e["heading"],
                    "chapter": e.get("chapter"), "page_start": e["page_start"], "page_end": e["page_end"],
                    "place_id": place_of.get(e["entry_id"])} for e in entries]
    return {
        "source": {k: source[k] for k in SOURCE_FIELDS if k in source},
        "places": [out_places[k] for k in sorted(out_places)],
        "facts": out_facts,
        "entries": out_entries,
        "passages": passages,
        "held": held,
    }


def check(b: dict) -> list[str]:
    errs = [f"source: {e.message}" for e in validator("source-summary.schema.json").iter_errors(b["source"])]
    for key, schema in SCHEMAS.items():
        v = validator(schema)
        for rec in b[key]:
            errs += [f"{key}: {rec.get(key[:-1] + '_id', '?')}: {'/'.join(map(str, e.absolute_path))} {e.message}"
                     for e in v.iter_errors(rec)]
    places = {p["place_id"] for p in b["places"]}
    entries = {e["entry_id"] for e in b["entries"]}
    passages = {p["passage_id"]: p for p in b["passages"]}
    for key, ids in (("places", places), ("entries", entries), ("passages", passages)):
        if len(ids) != len(b[key]):
            errs.append(f"{key}: duplicate ids")
    for p in b["places"]:
        errs += [f"places: {p['place_id']}: unknown place {r}" for r in p.get("parent_ids", []) + p.get("child_ids", [])
                 if r not in places]
    for e in b["entries"]:
        if e["place_id"] is not None and e["place_id"] not in places:
            errs.append(f"entries: {e['entry_id']}: unknown place {e['place_id']}")
    for p in b["passages"]:
        if p["entry_id"] not in entries:
            errs.append(f"passages: {p['passage_id']}: unknown entry {p['entry_id']}")
    for f in b["facts"]:
        if f["place_id"] not in places:
            errs.append(f"facts: {f['fact_id']}: unknown place {f['place_id']}")
        for ev in f["evidence"]:
            p = passages.get(ev["passage_id"])
            if p is None:
                errs.append(f"facts: {f['fact_id']}: unknown passage {ev['passage_id']}")
            elif p["text"][ev["char_start"]:ev["char_end"]] != ev["quote"]:
                errs.append(f"facts: {f['fact_id']}: quote not at its offsets in {ev['passage_id']}")
    return errs


def _dump(path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n")


def build(source_id: str) -> dict:
    """The bundle from DP-02…DP-07 (and DP-06's verified facts), before DP-09's links are applied."""
    d = INTERIM_DIR
    src = next(s for s in read_yaml(DATA_DIR / "sources.yaml")["sources"] if s["source_id"] == source_id)
    return bundle(read_jsonl(d / "classify" / source_id / "places.jsonl"),
                  read_jsonl(d / "verify" / source_id / "rules_accepted.jsonl"),
                  read_jsonl(d / "verify" / source_id / "rules_attributes.jsonl"),
                  read_jsonl(d / "classify" / source_id / "passages.jsonl"),
                  read_jsonl(d / "segment" / source_id / "entries.jsonl"), src,
                  read_jsonl(llm) if (llm := d / "extract" / source_id / "llm_accepted.jsonl").exists() else [])


def historic_names(source_id: str) -> list[dict]:
    path = DATA_DIR / "review" / source_id / "historic_names.yaml"
    return (read_yaml(path) or {}).get("names", []) if path.exists() else []


def run(source_id: str) -> dict:
    from pipeline.resolve import apply_historic, apply_link, check_historic, load_links

    b = build(source_id)
    rows = historic_names(source_id)
    herrs = check_historic(rows, {p["passage_id"]: p for p in b["passages"]}, {p["place_id"] for p in b["places"]})
    if herrs:
        for e in herrs:
            LG.error(e)
        raise SystemExit(f"DP-15: {len(herrs)} error(s) in historic_names.yaml; nothing written")
    links = load_links(source_id)  # DP-09
    b["places"] = [apply_historic(apply_link(p, links.get(p["place_id"])), rows, source_id) for p in b["places"]]
    errs = check(b)
    if errs:
        for e in errs[:50]:
            LG.error(e)
        raise SystemExit(f"DP-15: {len(errs)} error(s); nothing written")
    out = OUT / source_id
    out.mkdir(parents=True, exist_ok=True)
    _dump(out / "source.json", b["source"])
    for key in ("places", "facts", "entries", "passages"):
        _dump(out / f"{key}.json", b[key])
    counts = {k: len(b[k]) for k in ("places", "facts", "entries", "passages")}
    LG.info("curated bundle: %s", counts)
    for pid in b["held"]:
        LG.warning("place held back until its type is reviewed: %s", pid)
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    run(ap.parse_args(argv).source)
    return 0


if __name__ == "__main__":
    sys.exit(main())
