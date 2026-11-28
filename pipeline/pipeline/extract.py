"""DP-06 LLM extraction (spec §8.7, Appendix B) with its DP-07 checks (§8.8).

One call per gazetteer entry; long entries are split into chunks of whole passages. The prompt is a versioned
file in prompts/; temperature 0; JSON only; every fact must carry an exact quote. Responses are cached
(pipeline.llm), so a rerun costs nothing and gives the same output.

Every candidate is then verified against the source, never trusted:
  quote   - found in the chunk's text (whitespace, case and diacritics folded, ratio >= 92); the evidence
            stored is the source's own text at that place, with its offsets in the passage
  schema  - an allowed type, a non-empty value.label, a year that is an int or null
  numbers - every number in the label, and the year, is printed in the quote (no inferred years)
  vocab   - the label maps to the controlled vocabulary (DP-05) or is marked `new-term`

Outputs (data/interim/extract/<source>/):
  candidate_facts.jsonl  every candidate as the model gave it (scored by pipeline.gold_extract, TS-DATA-04)
  llm_accepted.jsonl     verified facts in fact-schema shape (method llm, model, prompt_version, run_id)
  llm_rejected.jsonl     the rest, with reasons
Facts start `unreviewed`; the site labels them as machine-read (§9.2).

Usage: python -m pipeline.extract run --source omalley-puri-1908 [--limit N]
       python -m pipeline.extract models        # list the provider's models (needs the key)
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from dataclasses import dataclass, field

import yaml
from rapidfuzz import fuzz

from pipeline.passages import page_at
from pipeline.util import INTERIM_DIR, REPO_ROOT, log, read_jsonl, sha256_text, write_jsonl

LG = log("DP-06")
PROMPTS = REPO_ROOT / "prompts"
TYPES = ("crop", "industry", "trade_item", "market_or_fair", "port", "railway", "canal", "road", "flood", "famine",
         "cyclone", "epidemic", "temple", "monument", "festival", "school", "hospital", "admin_change",
         "notable_person", "language")
QUOTE_MIN = 92.0  # DP-07 quote check
MAX_CHARS = 6000  # chunk size for long entries
VOCAB_CATEGORY = {"crop": "crop", "trade_item": "trade_item", "industry": "industry", "festival": "festival",
                  "temple": "monument", "monument": "monument", "flood": "calamity", "famine": "calamity",
                  "cyclone": "calamity", "epidemic": "calamity"}


# --- prompt ---------------------------------------------------------------------------------------------

@dataclass
class Prompt:
    version: str
    system: str
    template: str
    example_gold_ids: list[str] = field(default_factory=list)

    def user(self, entry_id: str, source: str, page: str, text: str) -> str:
        safe = re.sub(r"</?\s*entry\b", lambda m: m.group(0).replace("entry", "entry\u200b"), text, flags=re.IGNORECASE)
        return (self.template.replace("{entry_id}", entry_id).replace("{source}", source).replace("{page}", page)
                .replace("{text}", safe))


def load_prompt(version: str) -> Prompt:
    raw = (PROMPTS / f"{version}.md").read_text()
    _, front, body = raw.split("---\n", 2)
    meta = yaml.safe_load(front)
    sections = dict(re.findall(r"^## (\w+)\n(.*?)(?=^## |\Z)", body, flags=re.DOTALL | re.MULTILINE))
    system = sections["System"].strip() + "\n\nEXAMPLES\n\n" + sections["Examples"].strip()
    template = sections["User"].strip() + "\n"
    if meta["version"] != version:
        raise ValueError(f"{version}.md declares version {meta['version']}")
    return Prompt(version, system.replace("{{", "{").replace("}}", "}"), template, list(meta.get("examples_from", [])))


# --- response ---------------------------------------------------------------------------------------------

def parse_response(raw: str) -> tuple[list[dict], list[str]]:
    """Strict: malformed JSON rejects the whole response; a fact without a quote or with a type outside the
    closed list is dropped with a reason."""
    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as e:
        return [], [f"malformed JSON: {e}"]
    if not isinstance(doc, dict) or not isinstance(doc.get("facts"), list):
        return [], ["malformed JSON: no facts list"]
    facts, errors = [], []
    for i, f in enumerate(doc["facts"]):
        if not isinstance(f, dict):
            errors.append(f"fact {i}: not an object")
        elif f.get("type") not in TYPES:
            errors.append(f"fact {i}: type {f.get('type')!r} not allowed")
        elif not str(f.get("quote") or "").strip():
            errors.append(f"fact {i}: no quote")
        else:
            facts.append(f)
    return facts, errors


def chunks(passages: list[dict], max_chars: int = MAX_CHARS) -> list[list[dict]]:
    out: list[list[dict]] = [[]]
    size = 0
    for p in passages:
        if out[-1] and size + len(p["text"]) > max_chars:
            out.append([])
            size = 0
        out[-1].append(p)
        size += len(p["text"]) + 2
    return [c for c in out if c]


# --- verification ---------------------------------------------------------------------------------------

def _folded(text: str) -> tuple[str, list[int]]:
    """Folded text (diacritics, case, whitespace) and, for each folded character, its index in `text`."""
    out, idx = [], []
    for i, c in enumerate(text):
        f = "".join(x for x in unicodedata.normalize("NFKD", c) if not unicodedata.combining(x)).lower()
        if c.isspace():
            f = " "
            if out and out[-1] == " ":
                continue
        for ch in f:
            out.append(ch)
            idx.append(i)
    return "".join(out), idx


def _locate(quote: str, passages: list[dict]) -> tuple[dict, int, int] | None:
    q, _ = _folded(quote.strip())
    best = None
    for p in passages:
        ft, idx = _folded(p["text"])
        if not q or not ft:
            continue
        a = fuzz.partial_ratio_alignment(q, ft)
        if a.score >= QUOTE_MIN and (best is None or a.score > best[0]):
            s, e = idx[a.dest_start], idx[a.dest_end - 1] + 1
            while s < e and p["text"][s].isspace():
                s += 1
            while e > s and p["text"][e - 1].isspace():
                e -= 1
            best = (a.score, p, s, e)
    return (best[1], best[2], best[3]) if best else None


_VOCAB = None


def _vocab(ftype: str, label: str) -> str:
    global _VOCAB
    from pipeline.ocr import fold
    from pipeline.vocab import compile_vocab

    if _VOCAB is None:
        _VOCAB = compile_vocab()
    cat = VOCAB_CATEGORY.get(ftype)
    for c, term, rx in _VOCAB:
        if c == cat and rx.search(fold(label)):
            return f"{c}:{term}"
    return "new-term"


def verify(c: dict, passages: list[dict], model: str = "", prompt_version: str = "", run_id: str = "",
           spans: list[dict] | None = None) -> tuple[dict | None, list[str]]:
    why = []
    label = (c.get("value") or {}).get("label")
    if c.get("type") not in TYPES:
        why.append(f"type {c.get('type')!r} not allowed")
    if not isinstance(label, str) or not label.strip():
        why.append("no value.label")
        label = ""
    year = c.get("year")
    if year is not None and not isinstance(year, int):
        why.append(f"year {year!r} is not an integer")
    hit = _locate(str(c.get("quote") or ""), passages)
    if hit is None:
        why.append("quote not found in the entry")
        return None, why
    p, s, e = hit
    quote = p["text"][s:e]
    digits = set(re.findall(r"\d+", quote.replace(",", "")))
    if isinstance(year, int) and str(year) not in digits:
        why.append(f"year {year} is not printed in the quote")
    for n in re.findall(r"\d+", label.replace(",", "")):
        if n not in digits:
            why.append(f"number {n} in the value is not in the quote")
    if why:
        return None, why
    fact = {
        "fact_id": "ft_" + sha256_text(p["passage_id"], c["type"], label, str(s), str(e))[:12],
        "type": c["type"],
        "value": {"label": label.strip(), "vocab": _vocab(c["type"], label)},
        "evidence": [{"passage_id": p["passage_id"], "quote": quote, "char_start": s, "char_end": e}],
        "method": "llm", "model": model, "prompt_version": prompt_version, "run_id": run_id,
        "confidence": float(c.get("confidence") or 0.5), "review": {"status": "unreviewed"},
        # the page the quote is printed on (DP-02's page map), not the page its passage starts on
        "page": str((page_at(spans, p["char_start"] + s) if spans and "char_start" in p else None) or p.get("page", "")),
    }
    if isinstance(year, int):
        fact["as_of_year"] = year
    return fact, []


# --- stage ----------------------------------------------------------------------------------------------

def run(source_id: str, prompt_version: str = "extract-v1", limit: int | None = None, runner=None) -> dict:
    from pipeline.llm import BudgetExhausted, configured_runner

    prompt = load_prompt(prompt_version)
    runner = runner or configured_runner()
    model = runner.client.model
    run_id = f"{prompt_version}:{model}"
    entries = [e for e in read_jsonl(INTERIM_DIR / "segment" / source_id / "entries.jsonl") if e["kind"] == "gazetteer"]
    passages = read_jsonl(INTERIM_DIR / "classify" / source_id / "passages.jsonl")
    by_entry: dict[str, list[dict]] = {}
    for p in passages:
        by_entry.setdefault(p["entry_id"], []).append(p)
    cands, accepted, rejected, calls = [], [], [], 0
    for e in entries[:limit] if limit else entries:
        for chunk in chunks(by_entry.get(e["entry_id"], [])):
            text = "\n\n".join(p["text"] for p in chunk)
            try:
                raw = runner.complete(prompt.system, prompt.user(e["entry_id"], source_id, str(chunk[0]["page"]), text),
                                      prompt_version)
            except BudgetExhausted as ex:
                LG.warning("%s; stopping, rerun to resume (cached calls are free)", ex)
                break
            calls += 1
            facts, errors = parse_response(raw)
            for err in errors:
                rejected.append({"entry_id": e["entry_id"], "reasons": [err]})
            for f in facts:
                cands.append({**f, "entry_id": e["entry_id"], "model": model, "prompt_version": prompt_version})
                ok, why = verify(f, chunk, model, prompt_version, run_id, e.get("page_spans"))
                if ok:
                    accepted.append({**ok, "entry_id": e["entry_id"]})
                else:
                    rejected.append({"entry_id": e["entry_id"], "candidate": f, "reasons": why})
        else:
            continue
        break
    out = INTERIM_DIR / "extract" / source_id
    write_jsonl(out / "candidate_facts.jsonl", cands)
    write_jsonl(out / "llm_accepted.jsonl", sorted(accepted, key=lambda f: f["fact_id"]))
    write_jsonl(out / "llm_rejected.jsonl", rejected)
    res = {"calls": calls, "candidates": len(cands), "accepted": len(accepted), "rejected": len(rejected)}
    LG.info("DP-06 %s", res)
    return res


def models() -> list[str]:
    import urllib.request

    from pipeline.llm import GeminiClient

    c = GeminiClient(model="")
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models",
                                 headers={"x-goog-api-key": c._key})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
    return [m["name"].removeprefix("models/") for m in data.get("models", [])
            if "generateContent" in m.get("supportedGenerationMethods", [])]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["run", "models"])
    ap.add_argument("--source")
    ap.add_argument("--prompt", default="extract-v1")
    ap.add_argument("--limit", type=int)
    a = ap.parse_args(argv)
    if a.cmd == "models":
        print("\n".join(models()))
        return 0
    if not a.source:
        ap.error("run needs --source")
    from pipeline.llm import MissingKey

    try:
        print(json.dumps(run(a.source, a.prompt, a.limit), indent=2))
    except MissingKey as e:
        print(f"DP-06: {e}. Add it to pipeline/.env as GEMINI_API_KEY=... (that file is gitignored).")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


