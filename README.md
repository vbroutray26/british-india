# Towns of British India
*Places in the colonial record, 1860s–1947.*

A free, public, multilingual (English, ଓଡ଼ିଆ, हिन्दी) place-history site. Type a place and see what
the colonial-era record said about it, how it changed, and how it stands today — with every fact
traced to its source and read critically. First district: **Puri, Odisha**.

The sources were written by colonial officials. This project presents them critically, with context.

- Spec: [docs/spec.md](docs/spec.md) · Decisions: [docs/decisions.md](docs/decisions.md)
- Code: MIT ([LICENSE](LICENSE)) · Data: CC BY 4.0, third-party media excluded ([DATA-LICENSE.md](DATA-LICENSE.md))

## Layout
| Path | What |
|---|---|
| `apps/web` | Astro static site (Svelte islands), `/en/`, `/or/`, `/hi/` |
| `packages/ui` | Design tokens → CSS, base styles (Storybook from M1) |
| `packages/schema` | JSON Schemas for registers and data |
| `workers/api` | Cloudflare Worker: `/corrections` (later `/takedown`, `/ask`) |
| `pipeline` | Python data pipeline (DP-00…DP-16) |
| `data` | `sources.yaml`, `media.yaml`, curated data, review decisions |

See [CLAUDE.md](CLAUDE.md) for commands.

## Corrections
Email vbroutray@gmail.com or open an issue. A human responds within 7 days.
