// Label sets the design-system components take as props (every visible string comes from messages.json).
import { t, type Locale, type MessageKey } from './index';

export const typeLabel = (type: string, lang: Locale) => {
  const key = `type.${type}` as MessageKey;
  try {
    return t(key, lang);
  } catch {
    return type;
  }
};

export const factLabels = (lang: Locale) => ({
  viewPassage: t('fact.viewPassage', lang),
  reviewed: t('review.reviewed', lang),
  unreviewed: t('review.unreviewed', lang),
  notRecorded: t('fact.notRecorded', lang),
  machineExtracted: t('fact.machine', lang),
  approximate: t('fact.approximate', lang),
  correct: t('fact.correct', lang),
});

export const quoteLabels = (lang: Locale) => ({
  page: t('quote.page', lang),
  copyCitation: t('quote.copyCitation', lang),
  copied: t('quote.copied', lang),
  permalink: t('quote.permalink', lang),
  viewScan: t('quote.viewScan', lang),
});

export const summaryLabels = (lang: Locale, summaryLang: string) => ({
  heading: t('summary.heading', lang),
  ai: t('ai.label', lang),
  longer: t('summary.longer', lang),
  reviewed: t('review.reviewed', lang),
  unreviewed: t('review.unreviewed', lang),
  note: summaryLang !== lang ? t('summary.englishOnly', lang) : undefined,
});

export const heroLabels = (lang: Locale) => ({
  oldSpellings: t('place.oldSpellings', lang),
  then: t('place.then', lang),
  now: t('place.now', lang),
});

export const unitLabel = (unit: string | undefined, lang: Locale) =>
  unit === 'sq_miles' ? t('unit.sq_miles', lang) : unit === 'acres' ? t('unit.acres', lang) : undefined;

export type FactIcon = 'population' | 'area' | 'crop' | 'trade' | 'port' | 'railway' | 'canal' | 'road' | 'flood'
  | 'famine' | 'cyclone' | 'epidemic' | 'temple' | 'monument' | 'festival' | 'school' | 'hospital' | 'admin'
  | 'person' | 'language';
export const FACT_ICON: Record<string, FactIcon> = {
  population: 'population', area: 'area', crop: 'crop', industry: 'trade', trade_item: 'trade', market_or_fair: 'trade',
  port: 'port', railway: 'railway', canal: 'canal', road: 'road', flood: 'flood', famine: 'famine', cyclone: 'cyclone',
  epidemic: 'epidemic', temple: 'temple', monument: 'monument', festival: 'festival', school: 'school',
  hospital: 'hospital', admin_change: 'admin', notable_person: 'person', language: 'language',
};
/** Fact types extracted from the text (DP-06), in the order the place page shows them (FR-PLACE-03). */
export const LIST_TYPES = ['crop', 'trade_item', 'industry', 'market_or_fair', 'festival', 'temple', 'monument', 'flood',
  'famine', 'cyclone', 'epidemic', 'railway', 'road', 'canal', 'port', 'school', 'hospital', 'admin_change',
  'notable_person', 'language'];
export const factTypeLabel = (type: string, lang: Locale) => {
  try {
    return t(`fact.${type}` as MessageKey, lang);
  } catch {
    return type;
  }
};
