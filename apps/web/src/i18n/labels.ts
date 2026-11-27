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

export const heroLabels = (lang: Locale) => ({
  oldSpellings: t('place.oldSpellings', lang),
  then: t('place.then', lang),
  now: t('place.now', lang),
});

export const unitLabel = (unit: string | undefined, lang: Locale) =>
  unit === 'sq_miles' ? t('unit.sq_miles', lang) : unit === 'acres' ? t('unit.acres', lang) : undefined;

export const FACT_ICON: Record<string, 'population' | 'area'> = { population: 'population', area: 'area' };
export const factTypeLabel = (type: string, lang: Locale) =>
  type === 'population' ? t('fact.population', lang) : type === 'area' ? t('fact.area', lang) : type;
