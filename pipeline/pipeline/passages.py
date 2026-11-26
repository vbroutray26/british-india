"""Passages: the citable units (spec §7.3). One passage per paragraph of an entry.

passage_id = ps_<entry_id without 'en_'>_<nn>: stable as long as the entry's paragraphing is stable
(FR-TEXT-06). Page = the page on which the passage starts; page_end where it ends.
"""
from __future__ import annotations


def page_at(spans: list[dict], pos: int) -> str | None:
    for s in spans:
        if s["start"] <= pos < max(s["end"], s["start"] + 1):
            return s["page"]
    return spans[-1]["page"] if spans else None


def passages(entry: dict) -> list[dict]:
    out, pos = [], 0
    for n, para in enumerate(entry["text"].split("\n\n")):
        start = entry["text"].index(para, pos)
        end = start + len(para)
        pos = end
        if not para.strip():
            continue
        out.append({
            "passage_id": f"ps_{entry['entry_id'][3:]}_{n:02d}",
            "entry_id": entry["entry_id"],
            "char_start": start,
            "char_end": end,
            "text": para,
            "page": page_at(entry["page_spans"], start),
            "page_end": page_at(entry["page_spans"], max(start, end - 1)),
            "lang": "en",
        })
    return out
