import { describe, expect, it } from 'vitest';
import {
  ancestors, citation, distinctFigures, entriesFor, facts, factsFor, formatCoords, formatNumber, nameOf, passage,
  passagesOf, place, placeBySlug, places, slugOf, sortPlaces, sourceOfFact, sources,
} from './curated';

describe('curated bundle (D-40)', () => {
  it('loads every file', () => {
    expect(places.length).toBeGreaterThan(0);
    expect(facts.length).toBeGreaterThan(0);
    expect(sources.map((s) => s.source_id)).toContain('omalley-puri-1908');
  });

  it('every fact resolves to its place, passage and source (AC-PLACE-01)', () => {
    for (const f of facts) {
      expect(place(f.place_id), f.fact_id).toBeDefined();
      const p = passage(f.evidence[0].passage_id);
      expect(p?.text.slice(f.evidence[0].char_start, f.evidence[0].char_end)).toBe(f.evidence[0].quote);
      expect(sourceOfFact(f)).toBeDefined();
    }
  });

  it('slugs round-trip and keep the immutable id', () => {
    for (const p of places) expect(placeBySlug(slugOf(p.place_id))).toBe(p);
    expect(slugOf('pl_puri-0741')).toBe('puri-0741');
  });

  it('lists the district first', () => {
    expect(sortPlaces(places)[0].type).toBe('district');
  });

  it('gives each place its entries and each entry its passages in order', () => {
    const puri = places.find((p) => p.type === 'town' && nameOf(p) === 'Purī')!;
    const es = entriesFor(puri.place_id);
    expect(es.length).toBe(1);
    const ps = passagesOf(es[0].entry_id);
    expect(ps.map((p) => p.char_start)).toEqual([...ps.map((p) => p.char_start)].sort((a, b) => a - b));
  });

  it('orders a place’s figures newest first and folds repeats', () => {
    const district = places.find((p) => p.type === 'district')!;
    const pop = factsFor(district.place_id).filter((f) => f.type === 'population');
    expect(pop.map((f) => f.as_of_year)).toEqual([...pop.map((f) => f.as_of_year)].sort((a, b) => (b ?? 0) - (a ?? 0)));
    const folded = distinctFigures(pop);
    const years = folded.map((x) => x.fact.as_of_year);
    expect(new Set(years).size).toBe(years.length);
    expect(folded.reduce((n, x) => n + 1 + x.also.length, 0)).toBe(pop.length);
  });

  it('builds breadcrumbs up to the district', () => {
    const bhub = places.find((p) => nameOf(p) === 'Bhubaneswar')!;
    expect(ancestors(bhub).map((p) => p.type)).toEqual(['district', 'subdivision']);
  });
});

describe('formatting', () => {
  it('uses Indian grouping and the language’s digits', () => {
    expect(formatNumber(1017284, 'en')).toBe('10,17,284');
    expect(formatNumber(49334, 'hi')).toMatch(/49,334|४९,३३४/);
    expect(formatNumber(49334, 'or')).toMatch(/49,334|୪୯,୩୩୪/);
  });
  it('prints coordinates as degrees and minutes', () => {
    expect(formatCoords([85.8167, 19.8])).toBe('19° 48′ N, 85° 49′ E');
  });
  it('cites author, title, year and page', () => {
    expect(citation({ source_id: 's', title: 'Bengal District Gazetteers: Puri', author: "L. S. S. O'Malley", year: 1908,
      credit_line: '', rights_basis: 'public-domain' }, '233')).toBe("L. S. S. O'Malley, Bengal District Gazetteers: Puri (1908), p. 233.");
  });
});
