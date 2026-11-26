# Decisions log (extends spec §19)

| ID | Decision | Date |
|---|---|---|
| D-06a | Host the static site on **Cloudflare Workers static assets** (not Pages), account subdomain `british-india-towns.workers.dev`. Site: `british-india.british-india-towns.workers.dev`; API: `british-india-api.british-india-towns.workers.dev`. | 2026-11-26 |
| D-09a | Corrections/contact email: vbroutray@gmail.com (public on the site). | 2026-11-26 |
| D-10 | Odia **and Hindi** reviewer: project owner. | 2026-11-26 |
| D-14 | Island framework: Svelte 5. | 2026-11-26 |
| D-08a | Analytics: Cloudflare Web Analytics (beacon token via `PUBLIC_CF_BEACON_TOKEN`). | 2026-11-26 |
| D-15 | Code repo is public (`vbroutray26/british-india`). Raw scans go in a separate **private** repo `vbroutray26/british-india-raw` (Git LFS), checked out at `data/raw/`. | 2026-11-26 |
| D-16 | Gold sets are drafted by Claude and reviewed by the owner. Risk: evaluation is less independent; mitigate by owner re-labelling a 20% sample blind (spec §14.2). | 2026-11-26 |
| D-17 | Fonts — **pairing A**: Gloock (display) + Urbanist (sans) + Newsreader (passages). Odia: Noto Serif Oriya (display) + Anek Odia (sans). Hindi: Rozha One (display) + Anek Devanagari (sans). All OFL, self-hosted via Fontsource. Per-language stacks list only their own script; Indic sans use static 400/600 files. Measured font weight per home page: en ≈130 KB, or ≈230 KB, hi ≈293 KB. No synthetic italic/bold. Open: a text serif for long Hindi passages (Rozha One is display-only) — decide in M7. | 2026-11-26 |
| D-18 | Node >= 22.23.4 (Astro 7), pnpm 12, Python 3.12 via uv. | 2026-11-26 |

## Milestone status
- **M0 Foundations** — done 2026-11-26. Live: https://british-india.british-india-towns.workers.dev · API: https://british-india-api.british-india-towns.workers.dev. CI green. Deferred to M1: Storybook; CI auto-deploy (needs CLOUDFLARE_API_TOKEN secret + DEPLOY_ENABLED var); no synthetic italics for Odia/Devanagari.
