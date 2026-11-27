# Gold sets (spec §14.2)

Gold sets are labelled from the page images, never from pipeline output, so they can measure the
pipeline. Per D-16, Claude drafts every label and the owner reviews it. Each row records `labeller`,
`method` and `review.status` (`pending` until the owner signs it off).

| Set | File | Measures |
|---|---|---|
| GS-NUMERIC | `GS-NUMERIC.jsonl` | TS-DATA-03: rule extraction of coordinates, area and population (`python -m pipeline.gold score`) |
| GS-OCR | `GS-OCR.jsonl` + `GS-OCR/<source>/p<page>.txt` | TS-DATA-01: OCR character error rate (`python -m pipeline.gold_ocr score`) |
| GS-SEG | `GS-SEG.jsonl` | TS-DATA-02: entry and section boundary accuracy (`python -m pipeline.gold_seg score`) |

## GS-OCR transcription conventions

The 50 pages per source are a stratified sample by OCR confidence quartile, fixed seed 1908
(`pipeline.gold_ocr sample`). Each file starts as the OCR text. It is then corrected line by line
against the full-resolution scan (archive.org JP2, stored at 2400 px in the private raw repo).
`status` becomes `transcribed` only after every line has been checked.

- **What is included.** Lines are transcribed as printed, one printed line per file line. That covers
  end-of-line hyphens, spelling and punctuation, and diacritics (ā ī ū ṛ ṇ ṣ, in Unicode NFC).
- **What is left out.** The running head and page number are not transcribed; the OCR stores them
  separately. Italics are not marked.
- **Side-notes** (O'Malley's margin headings) are written in `{braces}` on the printed line they sit
  beside: at the start of the line for a left-margin note, at the end for a right-margin note. Braces
  are markup and are removed before scoring. A note that runs over several lines is joined and placed
  on its first line.
- **Footnotes** go under `@@ footnotes` with their markers (`*`, `†`), one printed line per file line.
- **Tables** are transcribed row by row, left to right, with cells separated by spaces. Leader dots
  (`...`) are left out. A table set into the text column comes before the short text lines beside it.
- **Printer's signature marks** at the foot of a page (`D`, `G 2`) are left out, like page numbers.
- **Decimal points** are printed as raised dots and transcribed `·` (29·57). Fractions use `½ ¼ ¾`.
- **Two-column pages** (the index) are transcribed left column first, then right column.
- **Broken type** is read as the intended letter when the word is unambiguous, and the reading is noted
  in a `%` comment at the top of the file.
- **Illegible characters** are written `[?]`. None are guessed.
- **Pages with no running text** (maps, plates) that the page flags missed are not transcribed:
  `pipeline.gold_ocr exclude --page N --reason "…"` marks them `excluded` and draws a replacement from
  the same confidence quartile.

Scoring normalises whitespace and typographic variants (curly and straight quotes, dash lengths,
prime marks). It does not fold letters, diacritics or digits. `cer_diacritics_folded` is reported
alongside the strict figure, because the Tesseract OCR has no macrons. The numeral CER counts every
edit that touches a digit, divided by the digits in the gold text.

## GS-NUMERIC

Each row records the printed figure (`as_printed`), the normalised value, year, page, and how it was
read. It is matched against extracted facts by page, type and year, so corrected OCR does not break
the link.

Scope: coordinates of places, and areas and populations of named land units (district, subdivisions,
estates, forests, tanks, famine tracts), in running text or tables. Not in scope: crop acreages, tenure
holdings, densities, revenue, religious or occupational counts. A figure printed twice (text and
table, or two pages) is labelled at each place it is printed. Candidates come from searching both OCR
engines' text, never from the extraction output, and every value is read from the full-resolution scan.
