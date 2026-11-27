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
| DP-01b Second read | `second_read` | full-resolution scans → `data/raw/<src>/ocr_vision/leaf_NNNN.json` (cache) → `ocr2/<src>/pages.jsonl` (text + figures per page) | an independent engine (Apple Vision, `tools/vision_ocr.swift`) reads every page; its figures are DP-07's cross-check (D-24) | no macOS → cached leaves only, the rest logged; leaf without a full scan → logged, its facts queue as "no second read" |
| DP-02 Segment | `segment` | pages → `segment/<src>/entries.jsonl` | gazetteer entries anchored to the checked heading list in `config/segment.yaml` (fuzzy + structure, alphabetical order); chapter sections split at side-notes; page spans per entry | heading not found → `missing_headings.jsonl` |
| DP-03 Classify | `classify` | entries → `classify/<src>/places.jsonl`, `passages.jsonl` | descriptor rules → place type; stable `place_id` and `passage_id` | low confidence or garbled heading → `data/review/<src>/classify_queue.jsonl` |
| DP-04 Rules | `rules` | passages → `rules/<src>/facts.jsonl`, `conflicts.jsonl` | coordinates, area, population (number paired with year only when adjacent), distance, height, subdivision; exact quote + offsets | same place/year with two figures → conflict for review (never overwritten) |
| DP-05 Vocab | `vocab` | passages + `vocab/vocab.yaml` → `vocab/<src>/tags.jsonl` | crops, trade, industry, calamity, monument, festival tags (candidates for DP-06) | — |
| DP-07 Verify | `verify` | facts → `verify/<src>/rules_accepted.jsonl`, `rules_attributes.jsonl`, `rules_rejected.jsonl` | quote in passage (≥ 0.92 after folding), numbers exact, offsets point at quote, fact schema, every figure in the quote also found by the second read on the passage's pages | rejected → `data/review/<src>/verify_rules_queue.jsonl` |

Tools: `pipeline.scan` (page image from the local PDF, crop to OCR lines; `full=True` fetches the
full-resolution archive.org JP2), `pipeline.gold` (contact sheets for labelling; scoring),
`pipeline.gold_ocr` (GS-OCR: `sample`, `seed`, `view`, `done`, `exclude`, `score [--engine vision]`). Not yet built: DP-06 (LLM extraction, M3), DP-08…DP-16.

## Status for `omalley-puri-1908` (2026-11-26)

- 340 leaves; mean OCR word confidence 87.3; 31 pages queued for OCR review.
- 25 of 25 gazetteer entries found (Udayagiri since D-27); 219 chapter sections.
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
- **Second read (DP-01b, D-24), 2026-11-27.** Vision alone is no better overall (CER 7.53%, numeral
  CER 20.7%) and it silently skips lines (three on p. 21), so it checks figures rather than replacing
  the text. On the GS-OCR pages a figure read the same by both engines is right 96.2% of the time,
  against 79.4% (Tesseract) and 81.4% (Vision) alone. The figures both get wrong are fractions (4¼ →
  "44", 67⅓ → "674") and broken type.
  In DP-07 (after the decimal fix below) the check queues 6 facts: 2 are real misreads (67⅓ printed,
  Tesseract "674", twice) and 4 are false alarms — Vision skipped the line (p. 165 "9 square miles"),
  dropped a decimal point (4·03 → "403") or misread a degree (85° → "80°"). *Correction (2026-11-27):
  an earlier note here counted "9" and "03" as caught misreads; "9" is correct as printed and "03" was
  a DP-04 decimal bug.* Agreement is therefore a review filter with a high false-alarm rate, not proof.
- **GS-NUMERIC (2026-11-27): 69 labels** (12 earlier + 57 new), every figure read from the
  full-resolution scan; owner review pending. Candidates were found by searching both engines' text
  for coordinates, areas and populations, so the set measures recall as well as precision. Scope:
  areas and populations of named land units (district, subdivisions, estates, forests, tanks, famine
  tracts) and place coordinates, including the 1901 census table on p. 60; not crop acreages, tenure
  holdings, density, revenue or religious counts. The book has fewer than 100 such figures; the rest of
  the spec's 100 should come from the 1905 Statistics volume (`puri-statistics-1905`), which is tables.
  **TS-DATA-03 fails: 66/69 exact (95.7%); 60/63 (95.2%) on labels independent of OCR corrections**,
  target ≥ 98% (was 31/69). *Update (D-28): the p. 60 table rows are now audited OCR corrections and a
  census-table rule reads them; the 6 table labels depend on that transcription.* *Update (D-29): **67/69
  (97.1%); 61/63 (96.8%) independent.** p. 59 fixed. Then p. 138 (recovered line read 480 for
  485) and p. 294 ("3-83" for 3·83).* *Update: those two were Vision misreadings on recovered lines,
  checked against the scans and added as audited OCR corrections. **TS-DATA-03 passes on Puri: 69/69;
  63/63 independent.** Both facts stay queued by DP-07 (one engine only), so the owner still reviews them.* Half the misses were figures
  extracted but credited to the page their paragraph starts on; DP-04 now takes the page from the
  entry's page map at the figure itself. New patterns: "in 1891 was returned at", census year elsewhere
  in the clause (only when the clause names exactly one year), yearless counts ("its population 10,000
  souls", "contained 3,000 souls", kept with no year), land-unit acres ("extending over 68,000 acres"),
  OCR's "squsre miles"; percentages and "24 million" are not counts (D-26). The 9 still failing are not
  reachable by rules on this OCR: the p. 60 census table (6; both engines garble it, e.g. 1,528 read as
  1,698 and 1,588, and a third read of the enlarged crop gives 1,039…1,698), two lines Tesseract dropped
  (pp. 138, 294) and a paragraph split mid-word on p. 59. Since D-27 both dropped lines are recovered, but
  only as Vision read them: "an aren of 480 square miles" (printed 485; extracted, wrong, and queued as
  one-engine) and "3-83 acres" (a hyphen for the raised point; not read as a decimal).
- **GS-SEG (2026-11-27): 50 boundaries; TS-DATA-02 at 45/50 (90%)**, target ≥ 98%. *Now 50/50 (D-30, D-33).* Gazetteer entries
  25/25 (Udayagiri's line was absent from the first OCR; recovered since D-27). Chapter sections were 3/25: DP-02 gave all of
  a page's side-notes to its first paragraph, and Tesseract's hOCR drops many side-notes. Fixed by
  placing each note beside its paragraph and adding the second read's notes; sections now 20/25
  (DP-02 makes 219 sections, up from 83). Still merged: pp. 79, 181, 215, 218, 226. Spurious splits
  are not measured; 31 section headings contain no real word (e.g. "110%.", ",*") and some of those
  are likely specks.
- **Dropped lines (D-27, 2026-11-27).** The archive.org hOCR silently drops body lines (11 in a row on
  p. 276). DP-01 aligns its lines with the second read by text and inserts a Vision line only where the
  hOCR has nothing between the two matched lines around it and the text is nowhere else on its page;
  footnotes (reference mark, or below a gap at the foot) are never recovered into the body. 110 lines on
  62 pages. `text_raw` stays as the hOCR read it; recovered lines are listed per page (`recovered`) and
  DP-07 queues any figure on them ("one engine only"). GS-OCR CER 7.91% → 7.29% (numerals 37.1% →
  36.9%); the raw column is the hOCR alone. One gold page reads worse (p. 181, +35 edits): the recovered
  line is right but lands out of order in the hOCR's already scrambled page.
- **Cut-off first words (D-29).** Where the hOCR lost the first letters of a line ("pulation" for
  "population", 33 lines), DP-01 restores the word from the matching second-read line (letters only, 1–3
  lost) and takes that line's indent from the second read: the lost letters had shifted the line right,
  which looked like a paragraph start (p. 59 split the 1872 census sentence in two). A blanket "lowercase
  line is never a paragraph start" rule was tried and rejected: it hid real entry starts whose heading
  OCR garbled (Kālupārā Ghāt) and cost 1 GS-SEG boundary. The side-note words glued onto p. 59's lines
  ("Growrm", "Tivo.") are still in the text; trimming them is not yet safe (it would also cut real words).
- **Line geometry from the second read (D-30).** The five merged GS-SEG boundaries all came from the
  hOCR's line boxes: side-notes glued onto a line's start (pp. 218, 226) move its left edge and fake or
  hide indents (p. 218 had 25 false paragraph starts); some lines are stored out of order (pp. 181,
  215). DP-01 now takes every line's indent from the matching Vision line (by in-order text alignment;
  where the hOCR merged two printed lines, from the row its opening matches), and position as well
  for lines the hOCR stored out of order. Two Vision bugs fixed on the way: fragments were grouped by
  box height, but Vision's boxes are taller than the line pitch, so a paragraph's short last line was
  merged with the start of the next (that hid most paragraph starts); and its indent threshold (3.5% of
  page width) was above the book's 3–4.5% indents. **TS-DATA-02: 49/50 (98%)**; GS-OCR CER 7.28% →
  6.46%; Vision alone 7.53% → 5.55%. Still merged: p. 79, where the text wraps around a castes table
  set into the column (wrapped lines look indented) and Vision read only "CASTES." of the side-note.
  Spurious splits unchanged: 31 of 214 section headings are OCR junk (specks read as side-notes).
- **Merging the two reads (D-31).** GS-OCR CER 6.46% → **3.90%** (diacritics folded 3.46%; numerals
  36.9% → 21.7%), step by step: garbled running heads ("D4 Punt, ;") are told by the gap below them, so
  the lines under them can be recovered (5.87%); the index's two columns, which the hOCR runs across the
  gutter, are split at the gutter by word boxes and read left then right (5.09%); fragments the hOCR kept
  of lines it dropped give way to the recovered lines (4.53%; p. 24 got 13 lines back); index lines with a
  narrower gutter gap (4.46%); then every other line is merged with its Vision line, word by word, judged
  by the 10,000 words both engines read on the same line somewhere in the book, and only for a word that looks like a misreading of the other (3.90%; without that check
  Vision's "—A" replaced "Bhubaneswar.—A" where it missed the bold heading). Figures are never
  taken from Vision, so DP-07's two-reading check still means two engines; corrected and recovered lines
  are left alone; a merged line keeps the hOCR's reading in `first_read`. Taking the whole Vision line
  when it looks better scored lower (3.80%) but broke punctuation DP-04 relies on (a census year lost on
  p. 59) and brought in glued side-notes, so it is used only when the word merge is still worse. Macrons
  restored from the book's Vision spellings gained only 0.06 points and were left out.
  **TS-DATA-01 still fails.** What is left: three tables set into the text column (pp. 33, 127, 223:
  the hOCR runs table cells into the wrapped text, 80% of the remaining numeral errors), a creased page
  (p. 130), the index (p. 310), missing macrons (0.6 points) and ordinary letter misreads. Without the
  five worst pages CER is 2.7% and numerals 8.7%, so two free engines will not reach 2% / 0.5%: that needs
  a third reader (D-24's open question) or owner review of the text, which the spec's "after review"
  allows for numerals. GS-NUMERIC 69/69 and GS-SEG 49/50 unchanged.
- **Inset tables and gathered lines (D-32).** GS-OCR CER 3.90% → **3.44%** (folded 3.00%; numerals
  21.7% → **11.4%**). Where a small table is set into the text column, Vision reads each cell as its own
  box: a run of at least four short lines starting at one place right of the column edge, with at least
  six boxes wholly left of them, is an inset table. Its cells are grouped into rows by the label column and
  inserted before the wrapped text, as recovered lines (`table: true`, listed in `recovered`), so DP-07
  queues their figures as read by one engine only; the hOCR's words left of the wrapped text are cut, and
  the wrapped lines are not taken as indents. Found on pp. 79, 127, 175, 223 and 297. Separately, the hOCR
  sometimes gathers words from several printed lines into one "line" (p. 33: the running head and two
  dropped lines; pp. 215, 228: text and side-note lines run together); each word keeps its own box, so a
  line is split where a word jumps back left by more than a fifth of the page and down or up by more
  than half a word's height, and each piece sorts into its place (3.52% → 3.48%, and p. 215's heading
  is found again). That brings real side-notes back, one of which ("Density of population", p. 60) falls
  between the p. 60 census table and the "census of 1901" above it, so DP-04 now looks for a table's
  census year back through its chapter, not only its section (gazetteer entries still look only within
  themselves). Vision's Cyrillic look-alike letters are mapped to Latin. Table cells are still misread
  by both engines ("8-69" for 8·59) and Vision misses some (p. 175). GS-NUMERIC 69/69 and GS-SEG 49/50
  unchanged; p. 79 is still merged.
- **Indents beside inset tables (D-33).** GS-SEG **50/50 (TS-DATA-02 passes at 100%)**; GS-OCR CER
  3.44% → **3.30%** (folded 2.86%; numerals 11.4%). The p. 79 castes table was found only from its lower
  half, so the wrapped lines above it counted as full-width lines and the paragraph start "There are only
  9 castes" did not look indented; its side-note ("CASTES.") went to the paragraph before. Now: the run
  of wrapped lines takes in an indented first line and a paragraph's short last line, and a box that fits
  no run (a wide heading cell, a split-off word) no longer ends it; the region reaches a quarter line, not
  half, above and below the run, and is moved into the first OCR's page coordinates by the median offset
  of the lines both read alike; beside a table, indents are measured from the wrapped text's own edge, in
  both reads, and the wrapped lines are not used as the full-width neighbours other lines are measured
  against. Pp. 127 and 223 also gain (195 → 104 and 225 → 134 edits).
- **The index and the creased page (D-34).** GS-OCR CER 3.30% → **3.02%** (folded 2.57%; numerals
  11.4% → **9.2%**). The index (p. 310, 444 → 194 edits) had no help from the second read: Vision's
  layout step handles single-column pages only, so merging and recovery were off for it. Now Vision's
  index is read as two columns split at the page's centre, without the running head and page number,
  and each column is recovered and merged against the hOCR's same column, figures still from the hOCR.
  On the creased page (p. 130, 372 → 284) the hOCR reads some printed lines as two pieces side by side;
  pieces at the same height that do not overlap are joined. It also cuts lines short at the crease: a line
  ending more than 5% of the page short of the column edge, with no paragraph start after it, takes the
  second read's words after the last word both read alike (the words that still pair up keep the
  hOCR's reading). Only there may figures come from Vision; the 3 such lines in the book are listed in
  the page's `recovered`, so DP-07 queues their figures as read by one engine. Pp. 34, 63, 69, 139 and
  200 also gain a little. Left on p. 130: the first line's opening ("4 ot Govern ent,") and Vision's own
  misreadings of the words it supplies ("Cnnal").
- GS-EXTRACT: not started.
