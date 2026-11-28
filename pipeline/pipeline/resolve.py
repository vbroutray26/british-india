"""DP-09 entity resolution and geocoding (spec §8.10).

Candidates (data/external/, downloaded 2026-11-28 with the owner's permission; gitignored):
  geonames/dump/IN.txt, geonames/alt/IN.txt   GeoNames India (CC BY 4.0): names, feature class, district (admin2)
  wikidata/box.csv                           one Wikidata query (CC0) for items with coordinates in the old
                                             district's bounding box: labels in en/or/hi, aliases, classes
Plus the 1908 heading coordinates (DP-04).

Matching (§8.10.2): names are normalised (diacritics, type words, oo/u, ee/i, ph/f, j/y, aspirates, w/v, double
letters) and compared exactly, by consonant skeleton and by fuzzy ratio; then type agreement (a hill needs a hill,
a village a settlement), place (within 15 km of the heading coordinates, or in the modern district of the parent
subdivision's headquarters) and uniqueness (no other candidate as good).

Tiers (§8.10.3): high = all of these (published); medium = a strong name but a signal missing or a rival (review);
low = a weak name match (manual); none = no candidate (the place becomes `uncertain`, a candidate ghost). Old
estates, subdivisions and districts are never matched automatically: their boundaries changed (DP-10).

Historic spellings come only from the source's own text, each with its quote: data/review/<src>/historic_names.yaml.
Owner decisions on medium/low links: data/review/<src>/place_matches.yaml (accept a candidate, or ghost).

Output: data/interim/resolve/<src>/place_links.jsonl; DP-15 applies the links (`apply_link`).
"""

from __future__ import annotations

import csv
import json
import math
import re
import unicodedata

from rapidfuzz import fuzz

from pipeline.util import DATA_DIR, INTERIM_DIR, log, read_yaml, write_jsonl

LG = log("DP-09")
EXTERNAL = DATA_DIR / "external"
BBOX = (84.8, 19.4, 86.6, 20.6)  # lon/lat: the 1908 Puri district with a margin (also the Wikidata query's box)
NAME_STRONG = 90.0
NAME_WEAK = 75.0
NEAR_KM = 15.0
SAME_KM = 3.0
CAPPED = {"estate", "subdivision", "district", "region", "state"}  # boundaries changed: review only
TYPE_OK = {"village": {"P"}, "town": {"P"}, "hill": {"T"}, "temple": {"S", "P"}, "monument": {"S"},
           "estate": {"P", "A"}, "subdivision": {"A", "P"}, "district": {"A"}, "river": {"H"}, "lake": {"H"},
           "port": {"P", "S"}, "railway-station": {"R"}}
# Wikidata classes seen in the box, mapped to GeoNames-like feature classes; items with none are not candidates
WD_CLASS = {"Q486972": "P", "Q56436498": "P", "Q515": "P", "Q1549591": "P", "Q3957": "P", "Q532": "P",
            "Q54050": "T", "Q8502": "T", "Q842402": "S", "Q44539": "S", "Q839954": "S", "Q35509": "S",
            "Q109607": "S", "Q4989906": "S", "Q1149652": "A", "Q4022": "H", "Q23397": "H", "Q55488": "R"}
TYPE_WORDS = r"\b(hill|hills|subdivision|district|ghat|river|town|village|estate|temple|station)\b"
SCRIPT = {"or": "Orya", "hi": "Deva"}


# --- names ----------------------------------------------------------------------------------------------

def fold(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()


def norm(name: str) -> str:
    s = re.sub(TYPE_WORDS, " ", fold(name))
    s = re.sub(r"[^a-z]", "", s)
    s = s.replace("oo", "u").replace("ee", "i")  # before doubles collapse: Pooree = Puri
    s = re.sub(r"(.)\1+", r"\1", s)  # double letters
    for a, b in (("ph", "f"), ("kh", "k"), ("gh", "g"), ("chh", "c"), ("ch", "c"), ("jh", "j"), ("th", "t"),
                 ("dh", "d"), ("bh", "b"), ("sh", "s"), ("w", "v"), ("y", "j"), ("oo", "u"), ("ee", "i"),
                 ("ou", "u")):
        s = s.replace(a, b)
    return re.sub(r"(.)\1+", r"\1", s)


def skeleton(n: str) -> str:
    return n[:1] + re.sub(r"[aeiou]", "", n[1:])


def name_score(name: str, others: list[str]) -> float:
    a = norm(name)
    best = 0.0
    for o in others:
        b = norm(o)
        if not a or not b:
            continue
        if a == b:
            return 100.0
        if skeleton(a) == skeleton(b) and len(skeleton(a)) >= 3:
            best = max(best, 95.0)
        best = max(best, fuzz.ratio(a, b))
    return best


# --- candidates -----------------------------------------------------------------------------------------

def km(lon1, lat1, lon2, lat2) -> float:
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 12742 * math.asin(math.sqrt(a))


def _inside(lon, lat) -> bool:
    return BBOX[0] <= lon <= BBOX[2] and BBOX[1] <= lat <= BBOX[3]


def load_geonames(d=EXTERNAL / "geonames") -> list[dict]:
    rows, ids = [], set()
    with open(d / "dump" / "IN.txt", encoding="utf-8") as f:
        for line in f:
            c = line.rstrip("\n").split("\t")
            lat, lon = float(c[4]), float(c[5])
            if not _inside(lon, lat):
                continue
            ids.add(c[0])
            rows.append({"cid": c[0], "geonames": c[0], "wikidata": None, "names": [c[1], c[2]] + c[3].split(",")[:30],
                         "lon": lon, "lat": lat, "fclass": "R" if c[7] == "RSTN" else c[6], "fcode": c[7],
                         "admin2": c[11] or None, "labels": {"en": c[1]}, "aliases": []})
    by = {r["cid"]: r for r in rows}
    with open(d / "alt" / "IN.txt", encoding="utf-8") as f:
        for line in f:
            c = line.rstrip("\n").split("\t")
            r = by.get(c[1])
            if r is None:
                continue
            if c[2] == "wkdt":
                r["wikidata"] = c[3]
            elif c[2] in SCRIPT and c[2] not in r["labels"]:
                r["labels"][c[2]] = c[3]
    return [r for r in rows if r["names"][0]]


def load_wikidata(path=EXTERNAL / "wikidata" / "box.csv", geonames: list[dict] = ()) -> list[dict]:
    admin_pts = [g for g in geonames if g["admin2"]]
    out = []
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        cls = [WD_CLASS[t] for t in r["types"].split("|") if t in WD_CLASS]
        m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", r["coord"])
        if not cls or not m or not r["en"]:
            continue
        lon, lat = float(m.group(1)), float(m.group(2))
        near = min(admin_pts, key=lambda g: km(lon, lat, g["lon"], g["lat"]), default=None)
        admin2 = near["admin2"] if near and km(lon, lat, near["lon"], near["lat"]) <= NEAR_KM else None
        qid = r["item"].rsplit("/", 1)[-1]
        aliases = [a for a in r["aliases"].split("|") if a]
        out.append({"cid": qid, "wikidata": qid, "geonames": None, "names": [r["en"], *aliases], "lon": lon,
                    "lat": lat, "fclass": cls[0], "admin2": admin2,
                    "labels": {k: r[k] for k in ("en", "or", "hi") if r[k]}, "aliases": aliases})
    return out


def merge(cands: list[dict]) -> list[dict]:
    """One candidate per real place: records that link to the same Wikidata item, or that have the same name
    within SAME_KM of each other (GeoNames rarely carries the Wikidata link)."""
    groups: list[dict] = []
    by_qid: dict[str, dict] = {}
    for c in sorted(cands, key=lambda c: c.get("wikidata") is None):  # Wikidata records first
        g = by_qid.get(c.get("wikidata") or "")
        if g is None:
            g = next((x for x in groups if km(x["lon"], x["lat"], c["lon"], c["lat"]) <= SAME_KM
                      and (x.get("wikidata") is None or c.get("wikidata") is None)
                      and name_score(c["names"][0], x["names"][:1]) >= 95), None)
        if g is None:
            g = {**c, "names": list(c["names"]), "labels": dict(c.get("labels", {})), "aliases": list(c.get("aliases", []))}
            groups.append(g)
            if c.get("wikidata"):
                by_qid[c["wikidata"]] = g
            continue
        g["names"] += [n for n in c["names"] if n not in g["names"]]
        g["aliases"] += [a for a in c.get("aliases", []) if a not in g["aliases"]]
        for lang, v in c.get("labels", {}).items():
            g["labels"].setdefault(lang, v)
        if c.get("geonames") and not g.get("geonames"):  # GeoNames gives the feature class and district
            g["geonames"], g["fclass"], g["admin2"] = c["geonames"], c["fclass"], c.get("admin2") or g.get("admin2")
        g["wikidata"] = g.get("wikidata") or c.get("wikidata")
        if g["wikidata"]:
            by_qid[g["wikidata"]] = g
    return groups


def expected_admin2(p: dict, places: list[dict], links: dict[str, dict]) -> set[str] | None:
    """Modern districts a place should be in: its subdivision's headquarters town's, or, for a place under the
    district, any headquarters town's (the old district now spans several)."""
    by_id = {q["place_id"]: q for q in places}

    def hq_admin2(sub: dict) -> str | None:
        hq = next((q for q in places if q["type"] == "town" and norm(q["names"][0]["text"]) == norm(sub["names"][0]["text"])), None)
        hl = links.get(hq["place_id"]) if hq else None
        return hl["candidate"].get("admin2") if hl and hl["tier"] == "high" else None

    parent = by_id.get((p.get("parent_ids") or [None])[0])
    if parent and parent["type"] == "subdivision":
        a = hq_admin2(parent)
        return {a} if a else None
    if parent and parent["type"] == "district":
        towns = [q for q in places if q["type"] == "town" and links.get(q["place_id"], {}).get("tier") == "high"]
        found = {links[q["place_id"]]["candidate"].get("admin2") for q in towns} - {None}
        return found or None
    return None


# --- matching -------------------------------------------------------------------------------------------

def _names(p: dict) -> list[str]:
    return [n["text"] for n in p["names"] if n.get("lang", "en") == "en"]


def match(place: dict, cands: list[dict], expected_admin2: set[str] | None = None) -> dict:
    heading = (place.get("geometry") or {}).get("coordinates") if (place.get("geometry") or {}).get("quality") == "heading" else None
    scored = []
    for g in merge(cands):
        s = max(name_score(n, g["names"]) for n in _names(place))
        if s < NAME_WEAK:
            continue
        dist = km(heading[0], heading[1], g["lon"], g["lat"]) if heading else None
        if heading:
            geo = dist <= NEAR_KM
        else:
            geo = bool(expected_admin2) and g.get("admin2") in expected_admin2
        type_ok = g.get("fclass") in TYPE_OK.get(place["type"], set())
        scored.append({"g": g, "name": s, "geo": geo, "type": type_ok, "dist": dist,
                       "strong": s >= NAME_STRONG and geo and type_ok})
    if not scored:
        return {"place_id": place["place_id"], "tier": "none"}
    scored.sort(key=lambda x: (x["strong"], x["name"], x["geo"], x["type"]), reverse=True)
    best, rest = scored[0], scored[1:]
    rivals = [x for x in rest if x["strong"] and x["name"] > best["name"] - 5
              and not (km(x["g"]["lon"], x["g"]["lat"], best["g"]["lon"], best["g"]["lat"]) <= SAME_KM)]
    if best["strong"] and not rivals and place["type"] not in CAPPED:
        tier = "high"
    elif best["name"] >= NAME_STRONG:
        tier = "medium"
    else:
        tier = "low"
    keep = ("wikidata", "geonames", "lon", "lat", "fclass", "admin2", "labels", "aliases")
    return {"place_id": place["place_id"], "tier": tier,
            "candidate": {"name": best["g"]["names"][0], **{k: best["g"].get(k) for k in keep}},
            "signals": {"name": round(best["name"], 1), "type": best["type"], "place": best["geo"],
                        "distance_km": round(best["dist"], 1) if best["dist"] is not None else None},
            "runner_up": [{"name": x["g"]["names"][0], "wikidata": x["g"].get("wikidata"),
                           "geonames": x["g"].get("geonames"), "score": round(x["name"], 1)} for x in rest[:3]]}


# --- publishing -----------------------------------------------------------------------------------------

def apply_link(place: dict, link: dict | None) -> dict:
    """The place as DP-15 publishes it: ids, Odia and Hindi names, modern spellings and a point for a high (or
    owner-accepted) link; `uncertain` for none; nothing for medium or low until reviewed."""
    if not link:
        return place
    if link["tier"] == "none":
        return {**place, "status": "uncertain"}
    if link["tier"] != "high":
        return place
    c = link["candidate"]
    p = {**place, "names": list(place["names"])}
    p["external_ids"] = {k: c[k] for k in ("wikidata", "geonames") if c.get(k)}
    src = "wikidata" if c.get("wikidata") else "geonames-in"
    labels = c.get("labels") or {}
    words = len((labels.get("en") or "").split())
    for lang in ("or", "hi"):
        t = re.split(r"\s*[,(（]", labels.get(lang) or "")[0].strip()  # "अट्री, खोर्धा" -> "अट्री"
        # a name, not a description: as many words as the item's English name ("Atri" is not "Atri hot spring")
        if t and len(t.split()) == words and not any(n["lang"] == lang for n in p["names"]):
            p["names"].append({"text": t, "lang": lang, "script": SCRIPT[lang], "kind": "primary", "source_id": src})
    have = {fold(n["text"]) for n in p["names"] if n.get("lang", "en") == "en"}
    own = _names(place)
    for t in [labels.get("en"), *(c.get("aliases") or [])]:
        # modern spellings of the same name only ("Khordha" for Khurdā), never other names ("Sri Jagannath Dham")
        if (t and fold(t) not in have and re.fullmatch(r"[A-Za-z\u00C0-\u024F\u1E00-\u1EFF' .-]+", t)
                and max(name_score(o, [t]) for o in own) >= NAME_STRONG):
            have.add(fold(t))
            p["names"].append({"text": t, "lang": "en", "kind": "alias", "source_id": src})
    if not p.get("geometry"):
        p["geometry"] = {"kind": "point", "coordinates": [c["lon"], c["lat"]], "quality": "exact",
                         "source": f"wikidata:{c['wikidata']}" if c.get("wikidata") else f"geonames:{c['geonames']}"}
    return p


def check_historic(rows: list[dict], passages: dict[str, dict], place_ids: set[str]) -> list[str]:
    errs = []
    for i, r in enumerate(rows):
        tag = f"historic_names[{i}] {r.get('name')!r}"
        if r.get("place_id") not in place_ids:
            errs.append(f"{tag}: unknown place {r.get('place_id')}")
        p = passages.get(r.get("passage_id"))
        if p is None:
            errs.append(f"{tag}: unknown passage {r.get('passage_id')}")
        elif r.get("quote", "") not in p["text"]:
            errs.append(f"{tag}: quote not found in {r['passage_id']}")
        if r.get("name", "") not in r.get("quote", ""):
            errs.append(f"{tag}: name not in its quote")
    return errs


def apply_historic(place: dict, rows: list[dict], source_id: str) -> dict:
    mine = [r for r in rows if r["place_id"] == place["place_id"]]
    if not mine:
        return place
    names = list(place["names"])
    for r in mine:
        n = {"text": r["name"], "lang": "en", "kind": "historic", "source_id": source_id}
        if r.get("years"):
            n["years"] = str(r["years"])
        if n not in names:
            names.append(n)
    return {**place, "names": names}


# --- stage ----------------------------------------------------------------------------------------------

def _decide(link: dict, decision: dict) -> dict:
    """Owner's decision on a link: accept a candidate (by Wikidata or GeoNames id) or mark a ghost."""
    if decision["decision"] == "ghost":
        return {**link, "tier": "none", "reviewed": decision.get("reviewer", "owner")}
    if decision["decision"] == "accept":
        want = decision.get("wikidata") or decision.get("geonames")
        c = link.get("candidate") or {}
        if want in (c.get("wikidata"), c.get("geonames")):
            return {**link, "tier": "high", "reviewed": decision.get("reviewer", "owner")}
        raise ValueError(f"{link['place_id']}: accepted {want} is not the proposed candidate; rerun and check")
    return link


def run(source_id: str, places: list[dict] | None = None) -> dict:
    """Match the bundle's places (DP-15 builds them; `places` lets assemble pass them in)."""
    if not (EXTERNAL / "wikidata" / "box.csv").exists() or not (EXTERNAL / "geonames" / "dump" / "IN.txt").exists():
        LG.warning("data/external/ is missing (GeoNames, Wikidata): DP-09 skipped, earlier links kept")
        return {}
    if places is None:
        from pipeline.assemble import build

        places = build(source_id)["places"]
    gn = load_geonames()
    cands = gn + load_wikidata(geonames=gn)
    links: dict[str, dict] = {}
    # headquarters towns first: their modern district is where the rest of their subdivision is looked for
    # towns first: their modern district is where the rest of their subdivision is looked for
    order = sorted(places, key=lambda p: (p["type"] != "town", (p.get("geometry") or {}).get("quality") != "heading"))
    for p in order:
        links[p["place_id"]] = match(p, cands, expected_admin2(p, places, links))
    decisions = DATA_DIR / "review" / source_id / "place_matches.yaml"
    for d in (read_yaml(decisions) or {}).get("decisions", []) if decisions.exists() else []:
        if d["place_id"] in links:
            links[d["place_id"]] = _decide(links[d["place_id"]], d)
    out = INTERIM_DIR / "resolve" / source_id
    write_jsonl(out / "place_links.jsonl", [links[k] for k in sorted(links)])
    tiers: dict[str, int] = {}
    for link in links.values():
        tiers[link["tier"]] = tiers.get(link["tier"], 0) + 1
    LG.info("DP-09 %d places: %s", len(links), tiers)
    return tiers


def load_links(source_id: str) -> dict[str, dict]:
    path = INTERIM_DIR / "resolve" / source_id / "place_links.jsonl"
    if not path.exists():
        return {}
    return {r["place_id"]: r for r in map(json.loads, path.read_text().splitlines()) if r}


if __name__ == "__main__":
    import sys

    print(json.dumps(run(sys.argv[sys.argv.index("--source") + 1]), indent=2))
