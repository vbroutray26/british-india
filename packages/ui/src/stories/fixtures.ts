// Story fixtures. English labels mirror apps/web i18n keys. ALL DATA HERE IS ILLUSTRATIVE SAMPLE DATA,
// not taken from any source (CLAUDE.md: never invent source data in the product). Labelled "Sample" where shown.
import type { CensusPoint, GalleryItem, SearchOption } from '../components/types';

export const L = {
  fact: { viewPassage: 'View passage', reviewed: 'Reviewed', unreviewed: 'Not yet reviewed', notRecorded: 'Not recorded in these sources', machineExtracted: 'Machine-extracted', approximate: 'Approximate', correct: 'Suggest a correction' },
  quote: { page: 'p.', copyCitation: 'Copy citation', copied: 'Copied', permalink: 'Permalink', viewScan: 'View scan' },
  review: { reviewed: 'Reviewed', unreviewed: 'Not yet reviewed' },
  summary: { heading: 'Summary', ai: 'Written by AI from the passages below', longer: 'Read the longer summary', reviewed: 'Reviewed', unreviewed: 'Not yet reviewed' },
  actions: { share: 'Share', cite: 'Cite', correct: 'Correct', listen: 'Listen' },
  results: { page: 'Page', noResults: 'No passages match', count: (n: number) => `${n} passages`, searching: 'Searching…' },
  search: { submit: 'Search', noResults: 'No places found', results: (n: number) => `${n} places found`, matched: 'Matched' },
  ask: { ask: 'Ask', asking: 'Searching the records…', tryOne: 'Try:', scope: 'Answers come only from the gazetteers, with page references.' },
  answer: { ai: 'Written by AI from the passages cited', unanswerable: "I couldn't find this in the records", nearest: 'Closest passages', helpful: 'Helpful', notHelpful: 'Not helpful', report: 'Report a problem', thanks: 'Thank you for the feedback' },
  correction: { title: 'Suggest a correction', intro: 'Tell us what is wrong. A person reads every message and replies within 7 days.', close: 'Close', item: 'Item', whatWrong: 'What is wrong?', suggestedFix: 'Suggested fix', source: 'Source', email: 'Email', emailHint: 'Only used to reply to you. Never shared.', optional: 'optional', submit: 'Send', sending: 'Sending…', thanks: 'Thank you. We will look at this within 7 days.', error: 'Sorry, that did not send. Please try again or email us.', orEmail: 'Or email', cancel: 'Cancel' },
  share: { title: 'Share this place', close: 'Close', copy: 'Copy link', copied: 'Copied', whatsapp: 'WhatsApp', more: 'More options', link: 'Link' },
  chart: { population: 'Population', year: 'Year', unit: 'Unit', boundary: 'Boundary version', source: 'Source', approximate: 'approximate', showTable: 'Show as table', notRecorded: 'Not recorded', boundaryChange: 'Boundary changed' },
  gallery: { open: 'Open image', close: 'Close', prev: 'Previous image', next: 'Next image', source: 'Source', counter: (i: number, n: number) => `${i} of ${n}` },
};

export const SAMPLE_PASSAGE =
  'Sample passage — placeholder text standing in for an exact quotation from a gazetteer entry. The highlighted words show where the supporting quote for a fact would sit, with its page reference below.';

export const SAMPLE_OPTIONS: SearchOption[] = [
  { id: '1', name: 'Puri', matched: 'Pooree', type: 'Town', district: 'Puri district', href: '#puri' },
  { id: '2', name: 'Puri district', type: 'District', href: '#puri-district' },
  { id: '3', name: 'Chilika Lake', matched: 'Chilka', type: 'Lake', district: 'Puri / Ganjam', href: '#chilika' },
  { id: '4', name: 'Konark', matched: 'Kanarak', type: 'Temple', district: 'Puri district', href: '#konark' },
  { id: '5', name: 'Khurda', matched: 'Khordha', type: 'Town', district: 'Puri district', href: '#khurda' },
];
export const searchSample = (q: string) =>
  SAMPLE_OPTIONS.filter((o) => `${o.name} ${o.matched ?? ''}`.toLowerCase().includes(q.toLowerCase()));

/** Sample series to exercise the chart's rules: two boundary versions and one approximate point. Not real data. */
export const SAMPLE_CENSUS: CensusPoint[] = [
  { year: 1872, value: 770000, unit: 'Sample district', boundary: 'Sample boundary A', source: 'Sample' },
  { year: 1881, value: 888000, unit: 'Sample district', boundary: 'Sample boundary A', source: 'Sample' },
  { year: 1891, value: 944000, unit: 'Sample district', boundary: 'Sample boundary A', source: 'Sample' },
  { year: 1901, value: 1017000, unit: 'Sample district', boundary: 'Sample boundary A', source: 'Sample' },
  { year: 1911, value: 1023000, unit: 'Sample district (redrawn)', boundary: 'Sample boundary B', source: 'Sample' },
  { year: 1921, value: 951000, unit: 'Sample district (redrawn)', boundary: 'Sample boundary B', source: 'Sample' },
  { year: 1931, value: 1040000, unit: 'Sample district (redrawn)', boundary: 'Sample boundary B', approximate: true, source: 'Sample crosswalk' },
];

const ph = (w: number, h: number, label: string) =>
  'data:image/svg+xml;utf8,' + encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}"><rect width="${w}" height="${h}" fill="#E6D9BC"/><path d="M0 ${h * 0.7} L${w * 0.3} ${h * 0.45} L${w * 0.55} ${h * 0.62} L${w} ${h * 0.35} V${h} H0Z" fill="#B8A988"/><text x="50%" y="50%" text-anchor="middle" font-family="sans-serif" font-size="${h / 10}" fill="#5E513F">${label}</text></svg>`);
export const SAMPLE_IMAGES: GalleryItem[] = [1, 2, 3, 4].map((n) => ({
  id: `s${n}`, thumb: ph(320, 240, `Sample ${n}`), full: ph(1200, 800, `Sample image ${n}`), width: 1200, height: 800,
  alt: `Sample placeholder image ${n}`, caption: `Sample caption ${n}`, date: 'c. 1900', credit: 'Sample credit line', sourceHref: '#',
}));
export const placeholderImage = ph;

/** Passage search results as the search page passes them (excerpts from Pagefind carry <mark>). */
export const SAMPLE_RESULTS = [
  { title: 'Sample section', href: '#ps_1', excerpt: 'the damage was aggravated by a <mark>cyclone</mark> in the', page: '21', source: 'Sample source' },
  { title: 'Sample entry', href: '#ps_2', excerpt: 'a <mark>cyclone</mark> swept the coast', page: '164', source: 'Sample source' },
];

/** DP-08's summary of Jatnī (omalley-puri-1908), as published. */
export const SAMPLE_SUMMARY = {
  oneLine: 'The 1908 gazetteer records that Jatnī became important after being tapped by the Bengal-Nagpur Railway.',
  short: 'The 1908 gazetteer records that the village of Jatnī contains the railway junction known as Khurda Road Station. It has risen to importance since it was tapped by the Bengal-Nagpur Railway.',
  long: 'The 1908 gazetteer records that Jatnī is a village containing the railway junction known as Khurda Road Station.\n\nThe place has risen to importance since it was tapped by the Bengal-Nagpur Railway.',
};
