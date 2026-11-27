// Build-time access to the curated bundles (data/curated/<source>/, written by DP-15, D-40).
// The site reads nothing else: every fact here passed DP-07 and DP-15's schema, reference and quote gate.

export interface Name { text: string; lang: string; script?: string; kind: string; source_id?: string }
export interface Place {
  place_id: string; type: string; names: Name[]; status: string;
  parent_ids?: string[]; child_ids?: string[];
  geometry?: { kind: string; coordinates: number[]; quality: string; source?: string };
  review: { status: 'accepted' | 'edited' | 'unreviewed' | 'rejected' };
}
export interface Evidence { passage_id: string; quote: string; char_start: number; char_end: number }
export interface Fact {
  fact_id: string; place_id: string; type: string; value: { number?: number; unit?: string; [k: string]: unknown };
  as_of_year?: number; evidence: Evidence[]; method: 'rule' | 'llm' | 'manual'; confidence: number;
  review: Place['review']; page?: string;
}
export interface Entry {
  entry_id: string; source_id: string; kind: 'gazetteer' | 'section'; heading: string; chapter: string | null;
  page_start: string; page_end: string; place_id: string | null;
}
export interface Passage {
  passage_id: string; entry_id: string; char_start: number; char_end: number; text: string; page: string;
  page_end?: string; lang: string;
}
export interface Source {
  source_id: string; title: string; author: string; year: number; credit_line: string; scan_ref?: string;
  acquired_from?: string; rights_basis: string;
}

const pick = <T>(files: Record<string, unknown>): T[] => Object.values(files).flatMap((m) => (m as { default: T[] }).default);
const one = <T>(files: Record<string, unknown>): T[] => Object.values(files).map((m) => (m as { default: T }).default);

export const places: Place[] = pick(import.meta.glob('../../../../data/curated/*/places.json', { eager: true }));
export const facts: Fact[] = pick(import.meta.glob('../../../../data/curated/*/facts.json', { eager: true }));
export const entries: Entry[] = pick(import.meta.glob('../../../../data/curated/*/entries.json', { eager: true }));
export const passages: Passage[] = pick(import.meta.glob('../../../../data/curated/*/passages.json', { eager: true }));
export const sources: Source[] = one(import.meta.glob('../../../../data/curated/*/source.json', { eager: true }));

const byId = <T, K extends keyof T>(xs: T[], k: K) => new Map(xs.map((x) => [x[k] as unknown as string, x]));
const placeById = byId(places, 'place_id');
const entryById = byId(entries, 'entry_id');
const passageById = byId(passages, 'passage_id');
const sourceById = byId(sources, 'source_id');

/** URL slug of a place: its immutable ID without the prefix (FR-TEXT-06: links never change). */
export const slugOf = (placeId: string) => placeId.replace(/^pl_/, '');
export const placeBySlug = (slug: string) => placeById.get(`pl_${slug}`);
export const place = (id: string) => placeById.get(id);
export const entry = (id: string) => entryById.get(id);
export const passage = (id: string) => passageById.get(id);
export const source = (id: string) => sourceById.get(id);
export const fact = (id: string) => facts.find((f) => f.fact_id === id);

export const nameOf = (p: Place) => (p.names.find((n) => n.kind === 'primary') ?? p.names[0]).text;
export const oldSpellings = (p: Place) => p.names.filter((n) => n.kind === 'historic' || n.kind === 'alias').map((n) => n.text);

/** The district first, then subdivisions, towns and the rest, each by name. */
const ORDER = ['district', 'subdivision', 'town'];
export function sortPlaces(ps: Place[]): Place[] {
  const rank = (p: Place) => (ORDER.includes(p.type) ? ORDER.indexOf(p.type) : ORDER.length);
  return [...ps].sort((a, b) => rank(a) - rank(b) || nameOf(a).localeCompare(nameOf(b), 'en'));
}

/** Facts of one place, by type, newest figure first. */
export function factsFor(placeId: string): Fact[] {
  return facts
    .filter((f) => f.place_id === placeId)
    .sort((a, b) => a.type.localeCompare(b.type) || (b.as_of_year ?? 0) - (a.as_of_year ?? 0) || a.fact_id.localeCompare(b.fact_id));
}

/** One figure per value and year: the same census figure printed twice is shown once, with both passages. */
export function distinctFigures(fs: Fact[]): { fact: Fact; also: Fact[] }[] {
  const out: { fact: Fact; also: Fact[] }[] = [];
  for (const f of fs) {
    const same = out.find((o) => o.fact.type === f.type && o.fact.as_of_year === f.as_of_year
      && o.fact.value.number === f.value.number && o.fact.value.unit === f.value.unit);
    if (same) same.also.push(f);
    else out.push({ fact: f, also: [] });
  }
  return out;
}

export const entriesFor = (placeId: string) => entries.filter((e) => e.place_id === placeId);
export const passagesOf = (entryId: string) => passages.filter((p) => p.entry_id === entryId);
export const sourceOfEntry = (e: Entry) => sourceById.get(e.source_id);
export function sourceOfFact(f: Fact): Source | undefined {
  const p = passageById.get(f.evidence[0].passage_id);
  const e = p && entryById.get(p.entry_id);
  return e && sourceById.get(e.source_id);
}

/** Figures with the locale's digits and Indian grouping where the language uses it. */
export function formatNumber(n: number, lang: 'en' | 'or' | 'hi'): string {
  return new Intl.NumberFormat(lang === 'en' ? 'en-IN' : `${lang}-IN`).format(n);
}

/** "19° 48′ N, 85° 49′ E" from decimal degrees as DP-04 read them from the heading. */
export function formatCoords(lonLat: number[]): string {
  const dms = (x: number, pos: string, neg: string) => {
    const a = Math.abs(x);
    const d = Math.floor(a);
    const m = Math.round((a - d) * 60);
    return `${d}° ${String(m).padStart(2, '0')}′ ${x >= 0 ? pos : neg}`;
  };
  return `${dms(lonLat[1], 'N', 'S')}, ${dms(lonLat[0], 'E', 'W')}`;
}

/** Standard citation (FR-TEXT-05): Author, Title (Year), p. N. Permalink appended by the caller. */
export function citation(s: Source, page: string): string {
  return `${s.author}, ${s.title} (${s.year}), p. ${page}.`;
}

/** Places on the way up to the district, outermost first (for breadcrumbs). */
export function ancestors(p: Place): Place[] {
  const out: Place[] = [];
  let cur = p.parent_ids?.[0] ? placeById.get(p.parent_ids[0]) : undefined;
  while (cur && !out.includes(cur)) {
    out.unshift(cur);
    cur = cur.parent_ids?.[0] ? placeById.get(cur.parent_ids[0]) : undefined;
  }
  return out;
}
