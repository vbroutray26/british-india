import messages from './messages.json';

export const LOCALES = ['en', 'or', 'hi'] as const;
export type Locale = (typeof LOCALES)[number];
export const DEFAULT_LOCALE: Locale = 'en';

type Entry = Partial<Record<Locale, string>>;
const table = messages as unknown as Record<string, Entry>;
export type MessageKey = Exclude<keyof typeof messages, '$comment'>;

export function isLocale(x: unknown): x is Locale {
  return typeof x === 'string' && (LOCALES as readonly string[]).includes(x);
}

/** Returns the string and whether it fell back to English (FR-LANG-05). */
export function lookup(key: MessageKey, lang: Locale): { text: string; fallback: boolean } {
  const entry = table[key];
  if (!entry) throw new Error(`Missing i18n key: ${key}`);
  const own = entry[lang];
  if (own) return { text: own, fallback: false };
  const en = entry.en;
  if (!en) throw new Error(`Key ${key} has no English text`);
  return { text: en, fallback: true };
}

export function t(key: MessageKey, lang: Locale): string {
  return lookup(key, lang).text;
}

/** Same path in another locale, e.g. /en/about/ -> /or/about/ */
export function switchLocalePath(pathname: string, to: Locale): string {
  const parts = pathname.split('/');
  if (isLocale(parts[1])) parts[1] = to;
  else parts.splice(1, 0, to);
  return parts.join('/') || `/${to}/`;
}

export const INFO_PAGES = ['about', 'sources', 'credits', 'methods', 'data', 'corrections', 'takedown', 'cite', 'contact'] as const;
export type InfoPage = (typeof INFO_PAGES)[number];
