# Project: British India — Places in the colonial record, 1860s–1947
Read the relevant sections of `docs/spec.md` before coding (cite FR/DP/AC IDs in commits).
Current milestone and decisions: `docs/decisions.md`.

## Rules
- Never invent source data, quotes, numbers or credits. If missing, stop and say so.
- Every extracted fact needs an exact quote verified by pipeline/verify.
- Every AI output records method, model, prompt_version.
- Prompts live in prompts/ and are versioned; changing one requires a version bump and a gold-set run.
- All user-facing strings go through i18n keys (en, or, hi) in apps/web/src/i18n/messages.json. No hard-coded text.
- Use design tokens only (packages/ui/tokens.json → CSS vars); no raw hex values in components.
- Animations: transform/opacity only; provide reduced-motion and lite fallbacks.
- Every image/map/audio needs a data/media.yaml row (credit, alt, caption, rights_basis).
- Pipeline stages are idempotent and resumable; add a test for each rule.
- Performance and accessibility budgets in spec §6 are failing conditions.
- No inline scripts or styles in built HTML (strict CSP in apps/web/public/_headers).
- Write tests first; run the full test suite before declaring a task done.
- Keep PRs small; update docs and the data dictionary.
- Raw scans never go in this public repo; they belong in the private british-india-raw repo.

## Commands (repo root)
- `pnpm install` — install JS deps (Node >= 22.23.4, pnpm 12)
- `pnpm dev` — Astro dev server (apps/web)
- `pnpm test` — all JS tests (tokens contrast, i18n, worker)
- `pnpm build` — tokens → CSS, then static site to apps/web/dist
- `pnpm --filter @bi/web deploy` — deploy site to Cloudflare (needs `wrangler login`)
- `pnpm --filter @bi/api deploy` — deploy API worker
- `cd pipeline && uv run pytest` — pipeline tests
- `pnpm validate:data` — validate data/sources.yaml and data/media.yaml
