# Pipeline (spec §8)

Python 3.12 via `uv`. Every stage is a module with a CLI, reads the previous stage's output, writes to
`data/interim/<stage>/<source_id>/`, and is **idempotent** (reruns are byte-identical, TS-DATA-11) and
**resumable** (atomic writes; DP-00 never re-downloads verified files).

```
uv run python -m pipeline.run --source omalley-puri-1908 [--acquire]   # DP-00 → DP-07
uv run pytest                                                            # tests (idempotence runs only with raw data)
uv run python -m pipeline.gold score --source omalley-puri-1908          # TS-DATA-03 vs gold/GS-NUMERIC.jsonl
```

Raw files live in the private repo `vbroutray26/british-india-raw`, cloned at `data/raw/`
(`gh repo clone vbroutray26/british-india-raw data/raw`).

## Stage contracts (Appendix A)

| Stage | Module | Input → output | Checks / metrics | Failure modes |
|---|---|---|---|---|
| DP-00 Acquire | `acquire` | `config/acquire.yaml` → `data/raw/<src>/`, `data/manifests/<src>.json` | MD5 vs host, SHA-256 recorded, leaf count vs page map | MD5 mismatch → stop; changed upstream file → old kept as a version; 429/5xx → backoff |
| DP-01 OCR | `ocr` | hOCR + page map → `ocr/<src>/pages.jsonl`, `stats.json` | per-page mean word confidence; numeric flags; running heads; side-notes; footnotes; audited corrections from `data/review/<src>/ocr_corrections.yaml` | pages < 80 conf → review; a correction that no longer matches → `correction-not-applied` flag |
| DP-02 Segment | `segment` | pages → `segment/<src>/entries.jsonl` | gazetteer entries anchored to the checked heading list in `config/segment.yaml` (fuzzy + structure, alphabetical order); chapter sections split at side-notes; page spans per entry | heading not found → `missing_headings.jsonl` |
| DP-03 Classify | `classify` | entries → `classify/<src>/places.jsonl`, `passages.jsonl` | descriptor rules → place type; stable `place_id` and `passage_id` | low confidence or garbled heading → `data/review/<src>/classify_queue.jsonl` |
| DP-04 Rules | `rules` | passages → `rules/<src>/facts.jsonl`, `conflicts.jsonl` | coordinates, area, population (number paired with year only when adjacent), distance, height, subdivision; exact quote + offsets | same place/year with two figures → conflict for review (never overwritten) |
| DP-05 Vocab | `vocab` | passages + `vocab/vocab.yaml` → `vocab/<src>/tags.jsonl` | crops, trade, industry, calamity, monument, festival tags (candidates for DP-06) | — |
| DP-07 Verify | `verify` | facts → `verify/<src>/rules_accepted.jsonl`, `rules_attributes.jsonl`, `rules_rejected.jsonl` | quote in passage (≥ 0.92 after folding), numbers exact, offsets point at quote, fact schema | rejected → `data/review/<src>/verify_rules_queue.jsonl` |

Tools: `pipeline.scan` (page image from the local PDF, crop to OCR lines; `full=True` fetches the
full-resolution archive.org JP2), `pipeline.gold` (contact sheets for labelling; scoring),
`pipeline.gold_ocr` (GS-OCR: `sample`, `seed`, `view`, `done`, `exclude`, `score`). Not yet built: DP-06 (LLM extraction, M3), DP-08…DP-16.

## Status for `omalley-puri-1908` (2026-11-26)

- 340 leaves; mean OCR word confidence 87.3; 31 pages queued for OCR review.
- 24 of 25 gazetteer entries found (Udayagiri's page is missing from the scan); 83 chapter sections.
- 56 facts + 90 place attributes pass DP-07; 1 rejected (truncated OCR number).
- GS-NUMERIC: 12 labels so far (target 100), 12/12 exact after one audited OCR correction (p. 61).
- GS-OCR (2026-11-27): 50 pages transcribed against full-resolution scans, stratified by OCR
  confidence (seed 1908); p. 315 excluded (fold-out map) and replaced by p. 127. Owner review pending.
  **TS-DATA-01 fails** (target CER ≤ 2%, numerals ≤ 0.5%):

  | Set | CER | CER, diacritics folded | Numeral CER |
  |---|---|---|---|
  | All 50 pages | 7.91% | 7.41% | 37.1% (684/1,843 digits) |
  | Without the index page (p. 310) | 6.82% | 6.33% | 22.7% (333/1,466) |

  Main causes: dropped or reordered lines around tables and side-notes (pp. 24, 130, 200, 223, 277),
  interleaved columns on the index page (p. 310, 71%), missing macrons, and digit misreads
  (e.g. 13,600→15,600, 29·57→99°57, 1,04,351→1,04,d51). The audited corrections in
  `ocr_corrections.yaml` touch none of the sampled lines, so "reviewed" equals "raw".
  Implication: numbers must not be published from this OCR without re-OCR at full resolution or a
  checked correction step (DP-06 with quote verification against the scan).
- GS-EXTRACT: not started.
