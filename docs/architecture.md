# Architecture (summary of spec §7)

```
data/sources.yaml ─► pipeline (Python, uv) ─► data/curated (JSON, git)
                                                   │
                                     apps/web (Astro static) ─► Cloudflare Workers static assets
                                                   │
                       workers/api (/corrections, later /ask /takedown) ─► KV, Turnstile, LLM free tiers
```

- **Raw data** (spec DP-00): scans and OCR text live in the private repo `british-india-raw`,
  cloned into `data/raw/` (gitignored here). Only manifests and SHA-256 sums are in `sources.yaml`.
  Large PDFs use Git LFS. GitHub's free LFS quota is limited **[verify]**; the 14 candidate
  sources total about 0.4 GB, so re-check before adding the census series.
- **Security headers / CSP**: `apps/web/public/_headers`. No inline scripts or styles.
- **i18n**: `apps/web/src/i18n/messages.json` (all three languages per key), URL prefix per locale.
