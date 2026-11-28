// TS-UI-01 / TS-A11Y-01: every component renders and has no serious/critical axe violations,
// plus behaviour tests for the rules the spec makes failing conditions.
import { fireEvent, render, screen, within } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import type { Component } from 'svelte';
import * as C from './index';
import { expectNoA11yViolations } from '../test/a11y';
import { L, SAMPLE_CENSUS, SAMPLE_IMAGES, SAMPLE_PASSAGE, SAMPLE_RESULTS, SAMPLE_SUMMARY, searchSample } from '../stories/fixtures';

const cases: [string, Component<any>, Record<string, unknown>][] = [
  ['Badge', C.Badge, { text: 'Reviewed', tone: 'reviewed', icon: 'reviewed' }],
  ['ReviewBadge', C.ReviewBadge, { status: 'accepted', labels: L.review }],
  ['AIBadge', C.AIBadge, { text: 'Written by AI' }],
  ['Callout', C.Callout, { kind: 'content-note', title: 'Content note', body: 'Body', link: { href: '#', text: 'How to read' } }],
  ['Tabs', C.Tabs, { label: 'Sections', items: [{ id: 'a', label: 'A', content: 'pa' }, { id: 'b', label: 'B', content: 'pb' }] }],
  ['Accordion', C.Accordion, { items: [{ id: 'a', title: 'Q', content: 'A' }] }],
  ['Skeleton', C.Skeleton, { variant: 'text' }],
  ['EmptyState', C.EmptyState, { title: 'Not recorded in these sources' }],
  ['ErrorState', C.ErrorState, { title: 'Search is unavailable', action: { text: 'Open the list', href: '#' } }],
  ['Breadcrumb', C.Breadcrumb, { label: 'Breadcrumb', items: [{ text: 'India', href: '#' }, { text: 'Puri' }] }],
  ['DataTable', C.DataTable, { caption: 'T', emptyText: 'Not recorded', columns: [{ key: 'year', label: 'Year' }, { key: 'value', label: 'Pop', numeric: true }], rows: SAMPLE_CENSUS, sortable: true }],
  ['LanguageSwitcher', C.LanguageSwitcher, { label: 'Language', current: 'or', items: [{ lang: 'en', name: 'English', href: '/en/' }, { lang: 'or', name: 'ଓଡ଼ିଆ', href: '/or/' }] }],
  ['ThenNowToggle', C.ThenNowToggle, { label: 'View', labels: { then: 'Then', now: 'Now' } }],
  ['Footer', C.Footer, { navLabel: 'Footer', licence: 'MIT', links: [{ text: 'About', href: '#a' }] }],
  ['FactCard', C.FactCard, { icon: 'population', label: 'Population', value: '1', year: '1908', source: 'S', passageHref: '#', review: 'accepted', labels: L.fact }],
  ['SourceQuote', C.SourceQuote, { text: SAMPLE_PASSAGE, highlight: { start: 0, end: 6 }, source: 'S', page: '1', citation: 'c', labels: L.quote }],
  ['CitationChip', C.CitationChip, { text: 'S, p. 1', href: '#', quote: 'q' }],
  ['GlossaryTerm', C.GlossaryTerm, { term: 'pargana', definition: 'A revenue sub-division.' }],
  ['PlaceCard', C.PlaceCard, { name: 'Puri', type: 'Town', href: '#', labels: { then: 'Then', now: 'Now' } }],
  ['PlaceHero', C.PlaceHero, { name: 'Puri', type: 'town', labels: { oldSpellings: 'Old spellings', then: 'Then', now: 'Now' } }],
  ['ActionBar', C.ActionBar, { label: 'Actions', labels: L.actions, onshare: () => {}, oncite: () => {} }],
  ['EventTimeline', C.EventTimeline, { label: 'Events', events: [{ year: '1866', icon: 'famine', title: 'Sample' }] }],
  ['ImageFigure', C.ImageFigure, { src: 'x.png', width: 10, height: 10, alt: 'Sample', credit: 'Credit', sourceHref: '#', sourceLabel: 'Source' }],
  ['ThemeCard', C.ThemeCard, { icon: 'flood', title: 'Floods', blurb: 'b', href: '#' }],
  ['TrailStep', C.TrailStep, { step: 1, total: 3, place: 'P', href: '#', narrative: 'n', labels: { step: 'Step', of: 'of', open: 'Open' } }],
  ['ClassroomPackCard', C.ClassroomPackCard, { title: 'T', summary: 's', href: '#', contents: ['a'], downloads: [{ text: 'PDF', href: '#p', lang: 'en' }], labels: { includes: 'Includes', download: 'Download' } }],
  ['DownloadMenu', C.DownloadMenu, { label: 'Download', items: [{ text: 'CSV', href: '#c' }] }],
  ['SearchCombobox', C.SearchCombobox, { label: 'Search places', placeholder: 'Search', action: '/en/search/', search: searchSample, labels: L.search }],
  ['TimeDial', C.TimeDial, { label: 'Year', years: [1872, 1908, 2011], value: 1908 }],
  ['AskPanel', C.AskPanel, { label: 'Ask', placeholder: 'q', onask: () => {}, labels: L.ask, samples: ['s'] }],
  ['AnswerBlock', C.AnswerBlock, { labels: L.answer, sentences: [{ text: 'S.', citations: [{ text: 'c', href: '#', quote: 'q' }] }] }],
  ['CensusChart', C.CensusChart, { title: 'Census', description: 'd', points: SAMPLE_CENSUS, labels: L.chart }],
  ['AudioPlayer', C.AudioPlayer, { src: '', title: 'Listen', lang: 'en', transcript: 't', labels: { transcript: 'Transcript' } }],
  ['MapListView', C.MapListView, { label: 'Places', emptyText: 'None', items: [{ name: 'Puri', type: 'town', icon: 'admin', href: '#' }] }],
  ['Gallery', C.Gallery, { label: 'Images', items: SAMPLE_IMAGES, labels: L.gallery }],
  ['Icon', C.Icon, { name: 'temple', label: 'Temple' }],
  ['PlaceSummary', C.PlaceSummary, { ...SAMPLE_SUMMARY, method: 'llm', review: 'unreviewed', labels: L.summary }],
  ['SearchResults', C.SearchResults, { label: 'Passages', query: 'cyclone', state: 'done', results: SAMPLE_RESULTS, labels: L.results }],
];

describe('every component renders accessibly', () => {
  it.each(cases)('%s', async (_name, Comp, props) => {
    const { container } = render(Comp, { props });
    expect(container.firstChild).toBeTruthy();
    await expectNoA11yViolations(container);
  });
});

describe('behaviour', () => {
  it('Tabs: arrow keys move selection with roving tabindex', async () => {
    render(C.Tabs, { label: 'S', items: [{ id: 'a', label: 'A', content: 'pa' }, { id: 'b', label: 'B', content: 'pb' }] });
    const [a, b] = screen.getAllByRole('tab');
    expect(a).toHaveAttribute('aria-selected', 'true');
    await fireEvent.keyDown(a, { key: 'ArrowRight' });
    expect(b).toHaveAttribute('aria-selected', 'true');
    expect(b).toHaveAttribute('tabindex', '0');
    expect(a).toHaveAttribute('tabindex', '-1');
    expect(screen.getByText('pb')).toBeVisible();
  });

  it('CensusChart: never joins points across boundary versions (AC-TIME-02)', () => {
    const { container } = render(C.CensusChart, { title: 'C', description: 'd', points: SAMPLE_CENSUS, labels: L.chart });
    const series = container.querySelectorAll('g.series');
    expect(series).toHaveLength(2); // two boundary versions
    const perSeriesSegs = [...series].map((g) => g.querySelectorAll('line.seg').length);
    expect(perSeriesSegs).toEqual([3, 2]); // 4 points → 3 links; 3 points → 2 links; none between series
    expect(container.querySelectorAll('g.pt.approx')).toHaveLength(1);
    expect(container.querySelectorAll('line.seg.approx')).toHaveLength(1);
  });

  it('CensusChart: includes a data table (NFR-A11Y-04)', () => {
    render(C.CensusChart, { title: 'Census', description: 'd', points: SAMPLE_CENSUS, labels: L.chart });
    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(screen.getAllByRole('row')).toHaveLength(SAMPLE_CENSUS.length + 1);
  });

  it('FactCard: missing value says "not recorded", never blank (AC-PLACE-05)', () => {
    render(C.FactCard, { icon: 'school', label: 'Schools', review: 'unreviewed', passageHref: '#', labels: L.fact });
    expect(screen.getByText(L.fact.notRecorded)).toBeInTheDocument();
    expect(screen.queryByText(L.fact.viewPassage)).not.toBeInTheDocument();
  });

  it('FactCard: machine-extracted facts carry the AI label (US-16)', () => {
    render(C.FactCard, { icon: 'crop', label: 'Crops', value: 'x', review: 'unreviewed', method: 'llm', labels: L.fact });
    expect(screen.getByText(L.fact.machineExtracted)).toBeInTheDocument();
    expect(screen.getByText(L.fact.unreviewed)).toBeInTheDocument();
  });

  it('SourceQuote: highlights exactly the quoted span (AC-PLACE-02)', () => {
    render(C.SourceQuote, { text: 'abcdefghij', highlight: { start: 2, end: 5 }, source: 'S', page: '1', labels: L.quote });
    expect(document.querySelector('mark')?.textContent).toBe('cde');
  });

  it('LanguageSwitcher: marks the current language and sets hreflang', () => {
    render(C.LanguageSwitcher, { label: 'Language', current: 'or', items: [{ lang: 'en', name: 'English', href: '/en/' }, { lang: 'or', name: 'ଓଡ଼ିଆ', href: '/or/' }] });
    expect(screen.getByRole('link', { name: 'ଓଡ଼ିଆ' })).toHaveAttribute('aria-current', 'true');
    expect(screen.getByRole('link', { name: 'English' })).toHaveAttribute('hreflang', 'en');
  });

  it('ThenNowToggle: is a radio group that reports changes', async () => {
    const onchange = vi.fn();
    render(C.ThenNowToggle, { label: 'View', labels: { then: 'Then', now: 'Now' }, onchange });
    await fireEvent.click(screen.getByRole('radio', { name: 'Now' }));
    expect(onchange).toHaveBeenCalledWith('now');
  });

  it('TimeDial: exposes the year as the slider value text (AC-TIME-01)', async () => {
    const onchange = vi.fn();
    render(C.TimeDial, { label: 'Year', years: [1872, 1908, 2011], value: 1872, onchange });
    const slider = screen.getByRole('slider', { name: 'Year' });
    expect(slider).toHaveAttribute('aria-valuetext', '1872');
    await fireEvent.input(slider, { target: { value: '2' } });
    expect(onchange).toHaveBeenCalledWith(2011);
    expect(slider).toHaveAttribute('aria-valuetext', '2011');
  });

  it('SearchCombobox: works as a plain form without JS and lists matches by alias (AC-SRCH-01)', async () => {
    vi.useFakeTimers();
    render(C.SearchCombobox, { label: 'Search places', placeholder: 'Search', action: '/en/search/', search: searchSample, labels: L.search, onselect: () => {} });
    const form = screen.getByRole('search');
    expect(form).toHaveAttribute('action', '/en/search/');
    const box = screen.getByRole('combobox');
    await fireEvent.input(box, { target: { value: 'Pooree' } });
    await vi.advanceTimersByTimeAsync(200);
    const list = screen.getByRole('listbox');
    expect(within(list).getAllByRole('option')[0]).toHaveTextContent('Puri');
    expect(within(list).getAllByRole('option')[0]).toHaveTextContent('Pooree');
    await fireEvent.keyDown(box, { key: 'ArrowDown' });
    expect(box).toHaveAttribute('aria-activedescendant');
    vi.useRealTimers();
  });

  it('CorrectionDialog: includes the item id and a hidden honeypot (FR-CORR-01/06)', () => {
    render(C.CorrectionDialog, { open: true, itemId: 'ft_x', contactEmail: 'a@b.c', onsubmit: async () => ({ ok: true }), labels: L.correction });
    const hidden = document.querySelector('input[name="item_id"]') as HTMLInputElement;
    expect(hidden.value).toBe('ft_x');
    const hp = document.querySelector('input[name="website"]') as HTMLInputElement;
    expect(hp).toHaveAttribute('tabindex', '-1');
    expect(hp.closest('[aria-hidden="true"]')).not.toBeNull();
  });

  it('AnswerBlock: shows the unanswerable message and nearest passages (AC-ASK-02)', () => {
    render(C.AnswerBlock, { labels: L.answer, unanswerable: true, nearest: [{ text: 'p', source: 'S', href: '#p' }] });
    expect(screen.getByText(L.answer.unanswerable)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'S' })).toBeInTheDocument();
    expect(screen.queryByText(L.answer.ai)).not.toBeInTheDocument();
  });

  it('DataTable: empty cells say "not recorded" and sorting sets aria-sort', async () => {
    render(C.DataTable, { caption: 'T', emptyText: 'Not recorded', sortable: true, columns: [{ key: 'a', label: 'A' }, { key: 'b', label: 'B' }], rows: [{ a: 'x', b: null }] });
    expect(screen.getByText('Not recorded')).toBeInTheDocument();
    await fireEvent.click(screen.getByRole('button', { name: /B/ }));
    expect(screen.getByRole('columnheader', { name: /B/ })).toHaveAttribute('aria-sort', 'ascending');
  });
});

describe('SearchResults (FR-SRCH-04, AC-SRCH-04)', () => {
  it('shows each result with its page, source and highlighted match', () => {
    render(C.SearchResults, { label: 'Passages', query: 'cyclone', state: 'done', results: SAMPLE_RESULTS, labels: L.results });
    const items = screen.getAllByRole('listitem');
    expect(items).toHaveLength(SAMPLE_RESULTS.length);
    expect(within(items[0]).getByText('cyclone', { selector: 'mark' })).toBeInTheDocument();
    expect(items[0]).toHaveTextContent('Page 21');
    expect(items[0]).toHaveTextContent('Sample source');
    expect(within(items[0]).getByRole('link')).toHaveAttribute('href', SAMPLE_RESULTS[0].href);
  });
  it('keeps only <mark> from an excerpt and escapes everything else', () => {
    const { container } = render(C.SearchResults, { label: 'P', query: 'x', state: 'done', labels: L.results,
      results: [{ title: 'T', href: '#', excerpt: '<img src=x onerror=alert(1)><mark>x</mark>', page: '1', source: 'S' }] });
    expect(container.querySelector('img')).toBeNull();
    expect(container.querySelector('mark')).toHaveTextContent('x');
  });
  it('says when nothing matched', () => {
    render(C.SearchResults, { label: 'P', query: 'zzz', state: 'done', results: [], labels: L.results });
    expect(screen.getByRole('status')).toHaveTextContent('No passages match');
  });
});

describe('FactCard text values', () => {
  it('sets names in reading type, figures in display type', () => {
    const { container } = render(C.FactCard, { icon: 'temple', label: 'Temples', value: 'Lingarāj; Rājarānī', valueKind: 'text', review: 'unreviewed', labels: L.fact });
    expect(container.querySelector('.value')).toHaveClass('text');
    const { container: c2 } = render(C.FactCard, { icon: 'population', label: 'Population', value: '49,334', review: 'unreviewed', labels: L.fact });
    expect(c2.querySelector('.value')).not.toHaveClass('text');
  });
});

describe('PlaceSummary', () => {
  it('labels machine-written summaries as AI and unreviewed (AC-PLACE-03)', () => {
    render(C.PlaceSummary, { ...SAMPLE_SUMMARY, method: 'llm', review: 'unreviewed', labels: L.summary });
    expect(screen.getByText('Written by AI from the passages below')).toBeInTheDocument();
    expect(screen.getByText('Not yet reviewed')).toBeInTheDocument();
  });
  it('shows no AI label on a summary a person wrote', () => {
    render(C.PlaceSummary, { ...SAMPLE_SUMMARY, method: 'manual', review: 'accepted', labels: L.summary });
    expect(screen.queryByText('Written by AI from the passages below')).toBeNull();
  });
  it('puts the long summary behind a disclosure, one paragraph each, marked with its own language', () => {
    const { container } = render(C.PlaceSummary, { ...SAMPLE_SUMMARY, method: 'llm', review: 'unreviewed', lang: 'en', labels: { ...L.summary, note: 'In English' } });
    expect(container.querySelectorAll('details p')).toHaveLength(2);
    expect(container.querySelector('[lang="en"]')).toHaveTextContent('Jatnī');
    expect(screen.getByText('In English')).toBeInTheDocument();
  });
});
