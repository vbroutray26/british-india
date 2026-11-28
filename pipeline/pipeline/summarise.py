"""DP-08 summaries (spec §8.9, §10.2; FR-PLACE-05, AC-PLACE-03).

Input is only a place's published facts and their quotes from the curated bundle (DP-15), never model memory.
One call per place with at least `MIN_FACTS` facts; prompt `prompts/summarise-v1.md`, low temperature, JSON with
three lengths (one line, one paragraph, long), in English.

Verification, per sentence (§8.9):
  numbers      - every figure (and number word) is in the input facts: a quote, a label, a value or a year
  proper nouns - every capitalised word is in the facts, the place's or its parents' names, or the source's
                 title and author (diacritics and case folded)
  the record   - a sentence stating the past as fact ("There were…") is dropped (§10.2)
Sentences failing a check are dropped. A summary fails if a length is left empty or its first sentence does not
give the source's year (§10.2); a failed summary is regenerated once, told why, then goes to review instead of
the site.

Outputs:
  data/curated/<source>/summaries.json        verified summaries (method llm, model, prompt_version), unreviewed
  data/interim/summarise/<source>/summaries.jsonl   the same with the sentences dropped and why
  data/interim/summarise/<source>/review.jsonl      summaries that failed twice, with reasons

Usage: python -m pipeline.summarise run --source omalley-puri-1908 [--model M] [--limit N]
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from dataclasses import dataclass

import yaml

from pipeline.util import DATA_DIR, INTERIM_DIR, REPO_ROOT, log, sha256_text, write_jsonl

LG = log("DP-08")
PROMPTS = REPO_ROOT / "prompts"
CURATED = DATA_DIR / "curated"
MIN_FACTS = 3
MAX_FACTS = 40
QUOTE_CHARS = 400
LENGTHS = ("one_line", "short", "long")
# Words a sentence may start with that are not names (any other capitalised word must be in the facts).
STARTERS = {"the", "a", "an", "it", "its", "this", "these", "that", "those", "here", "in", "at", "on", "by",
            "for", "from", "with", "of", "as", "according", "near", "both", "some", "other", "besides", "also",
            "among", "close", "beside", "between", "during", "under", "after", "before", "since", "when",
            "while", "most", "many", "each", "every", "one", "such", "they", "their", "he", "his", "she", "her",
            # connectives and common nouns models open sentences with
            "additionally", "furthermore", "finally", "moreover", "however", "later", "earlier", "overall",
            "local", "various", "several", "population", "features", "landmarks", "transportation", "transport",
            "agricultural", "agriculture", "regarding", "trade", "religious", "historical", "notable", "today"}
ABBREV = re.compile(r"(?:\b(?:Dr|Mr|Mrs|Lieut|Col|Capt|Rev|St|No|Rs|Sir|viz|i\.e|e\.g|A\.D|B\.C)|\b[A-Z])\.$")
UNREADABLE = re.compile(r"\||\b(?=\w*\d)(?=\w*[^\W\d_])(?!\d+(?:st|nd|rd|th)\b)\w+")
NUMBER_WORDS = {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
                "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty",
                "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety", "hundred", "thousand", "lakh",
                "lakhs", "crore", "million", "dozen", "dozens", "half", "twice", "thrice", "single"}
AS_FACT = re.compile(r"^\s*there\s+(is|are|was|were|had been|has been|have been)\b", re.IGNORECASE)
NUM = re.compile(r"\d[\d,]*(?:[·.]\d+)?")
WORD = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)?")


def fold(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()


def _numbers(text: str) -> set[str]:
    out = set()
    for m in NUM.findall(text):
        n = m.replace(",", "").replace("·", ".").rstrip(".")
        if "." in n:
            n = n.rstrip("0").rstrip(".")
        out.add(n)
    return out


def _num(x) -> str:
    return str(int(x)) if float(x).is_integer() else str(x).rstrip("0").rstrip(".")


# --- prompt ---------------------------------------------------------------------------------------------

@dataclass
class Prompt:
    version: str
    system: str
    template: str
    temperature: float

    def user(self, place: str, source: str, facts: list[dict]) -> str:
        body = "\n".join(json.dumps(f, ensure_ascii=False) for f in facts)
        body = re.sub(r"</?\s*facts\b", lambda m: m.group(0).replace("facts", "facts\u200b"), body, flags=re.IGNORECASE)
        return self.template.replace("{place}", place).replace("{source}", source).replace("{facts}", body)


def load_prompt(version: str) -> Prompt:
    raw = (PROMPTS / f"{version}.md").read_text()
    _, front, body = raw.split("---\n", 2)
    meta = yaml.safe_load(front)
    if meta["version"] != version:
        raise ValueError(f"{version}.md declares version {meta['version']}")
    sections = dict(re.findall(r"^## (\w+)\n(.*?)(?=^## |\Z)", body, flags=re.DOTALL | re.MULTILINE))
    return Prompt(version, sections["System"].strip(), sections["User"].strip() + "\n", float(meta.get("temperature", 0)))


def choose(facts: list[dict], max_facts: int = MAX_FACTS) -> list[dict]:
    """The facts the model sees. Over the cap, types take turns so one long list (temples) cannot crowd out the
    rest."""
    if len(facts) <= max_facts:
        return list(facts)
    by_type: dict[str, list[dict]] = {}
    for f in facts:
        by_type.setdefault(f["type"], []).append(f)
    chosen, i = [], 0
    while len(chosen) < max_facts:
        for fs in by_type.values():
            if i < len(fs) and len(chosen) < max_facts:
                chosen.append(fs[i])
        i += 1
    return chosen


def facts_for_prompt(facts: list[dict], max_facts: int = MAX_FACTS) -> list[dict]:
    rows = []
    for n, f in enumerate(choose(facts, max_facts), 1):
        v = f.get("value") or {}
        r = {"n": n, "type": f["type"], "label": v.get("label"), "number": v.get("number"), "unit": v.get("unit"),
             "year": f.get("as_of_year"), "page": f.get("page"), "quote": f["evidence"][0]["quote"][:QUOTE_CHARS]}
        rows.append({k: x for k, x in r.items() if x is not None})
    return rows


# --- verification ---------------------------------------------------------------------------------------

@dataclass
class Support:
    words: set[str]
    numbers: set[str]


def _names(p: dict) -> list[str]:
    return [n["text"] for n in p.get("names", [])]


def support(place: dict, facts: list[dict], source: dict, ancestors: list[dict] = ()) -> Support:
    texts = _names(place) + [n for a in ancestors for n in _names(a)] + [source["title"], source["author"]]
    numbers = {str(source["year"])}
    for f in facts:
        v = f.get("value") or {}
        texts += [str(v.get("label") or "")] + [e["quote"] for e in f["evidence"]]
        if isinstance(v.get("number"), (int, float)):
            numbers.add(_num(v["number"]))
        if f.get("as_of_year"):
            numbers.add(str(f["as_of_year"]))
    joined = " ".join(texts)
    return Support({fold(w) for w in WORD.findall(joined)}, numbers | _numbers(joined))


def sentences(text: str) -> list[str]:
    """Sentences, not split after "Dr.", "A.D." or an initial ("M. Senart", "C. S. I.")."""
    out: list[str] = []
    for part in re.split(r"(?<=[.!?])\s+(?=[\"'‘“(]?[A-Z0-9])", text.strip()):
        if out and ABBREV.search(out[-1]):
            out[-1] += " " + part
        elif part.strip():
            out.append(part.strip())
    return out


def unsupported(sentence: str, sup: Support) -> list[str]:
    why = []
    if UNREADABLE.search(sentence):
        why.append("unreadable OCR text")
    if AS_FACT.match(sentence):
        why.append("states the past as fact; say what the record records")
    for n in sorted(_numbers(sentence)):
        if n not in sup.numbers:
            why.append(f"number {n} is not in the facts")
    words = WORD.findall(sentence)
    for i, w in enumerate(words):
        f = fold(w)
        if f in NUMBER_WORDS and f not in sup.words:
            why.append(f"number word {w!r} is not in the facts")
        elif w[0].isupper() and f not in sup.words and not (i == 0 and f in STARTERS):
            why.append(f"name {w!r} is not in the facts")
    return why


def check_text(text: str, sup: Support) -> tuple[str, list[dict]]:
    """Keep the sentences every token of which the facts support; return the rest with reasons."""
    out = []
    for para in re.split(r"\n\s*\n", text.strip()):
        kept = []
        for s in sentences(para):
            why = unsupported(s, sup)
            if why:
                out.append({"text": s, "reasons": why})
            else:
                kept.append(s)
        if kept:
            out.append(" ".join(kept))
    paras = [x for x in out if isinstance(x, str)]
    return "\n\n".join(paras), [x for x in out if isinstance(x, dict)]


def verify(raw: dict, sup: Support, source_year: int) -> tuple[dict | None, list[str]]:
    why: list[str] = []
    res: dict = {"dropped": []}
    for k in LENGTHS:
        text = raw.get(k)
        if not isinstance(text, str) or not text.strip():
            why.append(f"{k}: missing")
            continue
        kept, dropped = check_text(text, sup)
        res["dropped"] += [{**d, "length": k} for d in dropped]
        if not kept:
            why += [f"{k}: every sentence dropped"] + [r for d in dropped for r in d["reasons"]]
        elif str(source_year) not in sentences(kept)[0]:
            why.append(f"{k}: the first sentence does not give the source's year ({source_year})")
        res[k] = kept
    return (None, why) if why else (res, [])


def parse(raw: str) -> tuple[dict | None, str | None]:
    try:
        d = json.loads(raw)
    except json.JSONDecodeError as e:
        return None, f"malformed JSON: {e}"
    return (d, None) if isinstance(d, dict) else (None, "malformed JSON: not an object")


# --- stage ----------------------------------------------------------------------------------------------

def _ancestors(p: dict, by_id: dict[str, dict]) -> list[dict]:
    out, cur = [], p
    while cur.get("parent_ids") and (nxt := by_id.get(cur["parent_ids"][0])) and nxt not in out:
        out.append(nxt)
        cur = nxt
    return out


def _primary(p: dict) -> str:
    return next((n["text"] for n in p["names"] if n.get("kind") == "primary"), p["names"][0]["text"])


def summarise_bundle(b: dict, runner, prompt_version: str = "summarise-v1", min_facts: int = MIN_FACTS,
                     limit: int | None = None) -> dict:
    from pipeline.llm import BudgetExhausted

    prompt = load_prompt(prompt_version)
    model = runner.client.model
    src = b["source"]
    by_id = {p["place_id"]: p for p in b["places"]}
    by_place: dict[str, list[dict]] = {}
    for f in b["facts"]:
        by_place.setdefault(f["place_id"], []).append(f)
    todo = [p for p in b["places"] if len(by_place.get(p["place_id"], [])) >= min_facts]
    published, kept, review, calls = [], [], [], 0
    for p in todo[:limit] if limit else todo:
        used = choose(by_place[p["place_id"]])
        rows = facts_for_prompt(used)
        ids = [f["fact_id"] for f in used]
        sup = support(p, used, src, _ancestors(p, by_id))
        user = prompt.user(_primary(p), f"{src['author']}, {src['title']} ({src['year']})", rows)
        res, why = None, []
        try:
            for attempt in range(2):  # failures regenerate once, then go to review (§8.9)
                msg = user if attempt == 0 else (
                    user + "\nYour previous answer was rejected: " + "; ".join(dict.fromkeys(why))
                    + ". Write it again using only the facts above.\n")
                raw = runner.complete(prompt.system, msg, prompt_version, temperature=prompt.temperature)
                calls += 1
                d, err = parse(raw)
                res, why = verify(d, sup, src["year"]) if d is not None else (None, [err])
                if res:
                    break
        except BudgetExhausted as ex:
            LG.warning("%s; stopping, rerun to resume (cached calls are free)", ex)
            break
        if not res:
            review.append({"place_id": p["place_id"], "reasons": why})
            continue
        s = {"summary_id": "sm_" + sha256_text(p["place_id"], prompt_version, model)[:12], "place_id": p["place_id"],
             "source_id": src["source_id"], "lang": "en", **{k: res[k] for k in LENGTHS}, "fact_ids": ids,
             "method": "llm", "model": model, "prompt_version": prompt_version,
             "run_id": f"{prompt_version}:{model}", "review": {"status": "unreviewed"}}
        published.append(s)
        kept.append({**s, "dropped": res["dropped"]})
    return {"published": published, "kept": kept, "review": review, "calls": calls}


def check(b: dict, summaries: list[dict]) -> list[str]:
    """CI's gate for published summaries: schema, references, and AC-PLACE-03 against the bundle's facts."""
    from pipeline.validate import validator

    v = validator("summary.schema.json")
    by_id = {p["place_id"]: p for p in b["places"]}
    facts = {f["fact_id"]: f for f in b["facts"]}
    errs = []
    for s in summaries:
        sid = s.get("summary_id", "?")
        errs += [f"summaries: {sid}: {'/'.join(map(str, e.absolute_path))} {e.message}" for e in v.iter_errors(s)]
        p = by_id.get(s.get("place_id"))
        if p is None:
            errs.append(f"summaries: {sid}: unknown place {s.get('place_id')}")
            continue
        missing = [i for i in s.get("fact_ids", []) if i not in facts or facts[i]["place_id"] != p["place_id"]]
        if missing:
            errs.append(f"summaries: {sid}: unknown fact(s) for this place: {', '.join(missing)}")
            continue
        sup = support(p, [facts[i] for i in s["fact_ids"]], b["source"], _ancestors(p, by_id))
        for k in LENGTHS:
            for sent in sentences(" ".join(str(s.get(k, "")).split())):
                errs += [f"summaries: {sid}: {k}: {r}" for r in unsupported(sent, sup)]
            first = sentences(str(s.get(k, "")))
            if not first or str(b["source"]["year"]) not in first[0]:
                errs.append(f"summaries: {sid}: {k}: the first sentence does not give the source's year")
    return errs


def load_bundle(source_id: str) -> dict:
    d = CURATED / source_id
    b = {"source": json.loads((d / "source.json").read_text())}
    for k in ("places", "facts"):
        b[k] = json.loads((d / f"{k}.json").read_text())
    return b


def run(source_id: str, prompt_version: str = "summarise-v1", runner=None, model: str | None = None,
        limit: int | None = None) -> dict:
    from pipeline.llm import configured_runner

    b = load_bundle(source_id)
    out = summarise_bundle(b, runner or configured_runner(model), prompt_version, limit=limit)
    errs = check(b, out["published"])
    if errs:  # cannot happen if verify and check agree; never publish if they do not
        for e in errs[:50]:
            LG.error(e)
        raise SystemExit(f"DP-08: {len(errs)} error(s); nothing written")
    path = CURATED / source_id / "summaries.json"
    path.write_text(json.dumps(sorted(out["published"], key=lambda s: s["place_id"]), ensure_ascii=False, indent=1,
                               sort_keys=True) + "\n")
    d = INTERIM_DIR / "summarise" / source_id
    write_jsonl(d / "summaries.jsonl", out["kept"])
    write_jsonl(d / "review.jsonl", out["review"])
    res = {"calls": out["calls"], "published": len(out["published"]), "review": len(out["review"]),
           "sentences_dropped": sum(len(k["dropped"]) for k in out["kept"])}
    LG.info("DP-08 %s", res)
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["run"])
    ap.add_argument("--source", required=True)
    ap.add_argument("--prompt", default="summarise-v1")
    ap.add_argument("--model", help="override config/llm.yaml's model")
    ap.add_argument("--limit", type=int)
    a = ap.parse_args(argv)
    from pipeline.llm import MissingKey

    try:
        print(json.dumps(run(a.source, a.prompt, model=a.model, limit=a.limit), indent=2))
    except MissingKey as e:
        print(f"DP-08: {e}. Add it to pipeline/.env as GEMINI_API_KEY=... (that file is gitignored).")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
