# Prompts (spec §9.2, Appendix B)

Prompts are code: versioned files, reviewed like code, tested against the gold sets. Changing a prompt means a
new file with the next version (`extract-v2.md`), never an edit in place, and a GS-EXTRACT run
(`python -m pipeline.gold_extract score`). Every AI output records the prompt `version` it came from.

Each file has YAML front matter (`version`, `examples_from`: the gold rows used as worked examples, which are
then left out of scoring) and three sections: `## System`, `## Examples` (appended to the system message) and
`## User` (the template; `{entry_id}`, `{source}`, `{page}`, `{text}`; the entry text is data inside
`<entry>` delimiters and cannot close them).

| File | Used by |
|---|---|
| `extract-v1.md` | DP-06 extraction (`pipeline.extract`) |
