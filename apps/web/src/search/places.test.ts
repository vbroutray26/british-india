import { describe, expect, it } from 'vitest';
import { fold, matchPlaces, type PlaceIndexItem } from './places';

const items: PlaceIndexItem[] = [
  { id: 'pl_puri-0741', name: 'Purī', aliases: ['Pooree', 'Jagannāth'], type: 'Town', district: 'Purī', href: '/en/places/puri-0741/' },
  { id: 'pl_puri-district-080c', name: 'Purī', aliases: [], type: 'District', href: '/en/places/puri-district-080c/' },
  { id: 'pl_banpur-1111', name: 'Bānpur', aliases: [], type: 'Village', district: 'Purī', href: '/en/places/banpur-1111/' },
  { id: 'pl_khurda-75c6', name: 'Khurdā', aliases: [], type: 'Town', district: 'Purī', href: '/en/places/khurda-75c6/' },
  { id: 'pl_khurda-subdivision-40c0', name: 'Khurdā subdivision', aliases: [], type: 'Subdivision', district: 'Purī', href: '/en/places/khurda-subdivision-40c0/' },
];

describe('place search (FR-SRCH-01/02)', () => {
  it('folds diacritics and case', () => {
    expect(fold('Bānpur')).toBe('banpur');
    expect(fold('KHURDĀ')).toBe('khurda');
  });
  it('finds a place typed without diacritics', () => {
    expect(matchPlaces('banp', items).map((o) => o.id)).toEqual(['pl_banpur-1111']);
  });
  it('resolves an old spelling and shows the alias it matched (AC-SRCH-01)', () => {
    const [first] = matchPlaces('Pooree', items);
    expect(first.id).toBe('pl_puri-0741');
    expect(first.matched).toBe('Pooree');
  });
  it('ranks names that start with the query above names that merely contain it', () => {
    expect(matchPlaces('khurda', items).map((o) => o.name)).toEqual(['Khurdā', 'Khurdā subdivision']);
  });
  it('matches a later word of a name', () => {
    expect(matchPlaces('subdiv', items).map((o) => o.id)).toEqual(['pl_khurda-subdivision-40c0']);
  });
  it('returns nothing for an empty query and caps the list', () => {
    expect(matchPlaces('  ', items)).toEqual([]);
    expect(matchPlaces('p', items)).toHaveLength(2);
    expect(matchPlaces('p', items, 1)).toHaveLength(1);
  });
});
