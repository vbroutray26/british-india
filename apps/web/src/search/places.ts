// Place autocomplete (FR-SRCH-01/02, AC-SRCH-01): names and old spellings, matched with diacritics and case
// folded, so "banpur" finds Bānpur and an alias like "Pooree" finds Purī and says which spelling matched.
import type { SearchOption } from '@bi/ui/components/types';

export interface PlaceIndexItem { id: string; name: string; aliases: string[]; type: string; district?: string; href: string }

export const fold = (s: string) => s.normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase().trim();

function score(q: string, text: string): number {
  const f = fold(text);
  if (f === q) return 0;
  if (f.startsWith(q)) return 1;
  if (f.split(/[\s-]+/).some((w) => w.startsWith(q))) return 2;
  return -1;
}

export function matchPlaces(query: string, items: PlaceIndexItem[], limit = 8): SearchOption[] {
  const q = fold(query);
  if (!q) return [];
  const hits: { o: SearchOption; s: number }[] = [];
  for (const it of items) {
    let best = score(q, it.name);
    let matched: string | undefined;
    for (const a of it.aliases) {
      const s = score(q, a);
      if (s >= 0 && (best < 0 || s < best)) { best = s; matched = a; }
    }
    if (best >= 0) hits.push({ o: { id: it.id, name: it.name, matched, type: it.type, district: it.district, href: it.href }, s: best });
  }
  return hits.sort((a, b) => a.s - b.s || a.o.name.length - b.o.name.length || a.o.name.localeCompare(b.o.name))
    .slice(0, limit).map((h) => h.o);
}
