# Asset register (spec §13.3)

Every brand, illustration and pattern asset. AI-generated assets must record the tool and prompt
and be checked for stray text and cultural errors.

| File | What | Creator / tool | Date | Licence | Edit history |
|---|---|---|---|---|---|
| `brand/brand_logo_source.webp` | Master logo artwork "Towns of British India" (2000×1125 raster, cream paper) | Project owner. **Tool and prompt: to be filled in by owner** (required if AI-generated) | 2026-11-26 | Project-owned | Supplied by owner; no SVG master exists |
| `brand/brand_logo_duotone.svg` | Full-detail vector: ink (`currentColor`) + accent (`--logo-accent`) | Traced by `design/tools/logo.py` (potrace + SVGO) from the master | 2026-11-26 | Project-owned | 250 KB / 96 KB gzip — hero use only |
| `brand/brand_logo_mono.svg` | Full-detail vector, ink only | Same | 2026-11-26 | Project-owned | 118 KB / 46 KB gzip |
| `brand/brand_logo_lite.svg` | Simplified vector for header/footer (≤ 120 px tall) | Same, traced at 520 px width | 2026-11-26 | Project-owned | 25 KB / 9 KB gzip |
| `brand/brand_favicon_t-initial.svg` | Favicon candidate: the ornate T from "TOWNS" | Same | 2026-11-26 | Project-owned | 5.6 KB — default favicon |
| `brand/brand_favicon_train.svg` | Favicon candidate: the locomotive | Same | 2026-11-26 | Project-owned | 12.8 KB — illegible at 16 px; kept for social avatar trials |
| `apps/web/public/brand/logo-{480,960,1440}.webp` | Raster of the master (cream background) for share cards / OG | `design/tools/logo.py` (cwebp q82) | 2026-11-26 | Project-owned | 48 / 135 / 215 KB |

## Exceptions to spec §13.2
- **Brand SVG ≤ 6 KB:** not achievable for this detailed artwork. Mitigation: the lite SVG (9 KB gzip)
  is used where the logo appears on every page; full-detail SVGs load only on the home hero.

## Review notes
- The architecture drawn inside the letters (domes, minarets) reads as Indo-Saracenic/Mughal rather than
  Odisha's temple forms (deul). Fine for an India-wide brand; noted per §13.1 for the owner's judgement.
- English only: Odia and Hindi wordmarks (spec §13.2) still to be produced.
