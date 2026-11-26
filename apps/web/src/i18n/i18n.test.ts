import { describe, expect, it } from 'vitest';
import messages from './messages.json';
import { LOCALES, lookup, switchLocalePath, type MessageKey } from './index';

const keys = Object.keys(messages).filter((k) => k !== '$comment') as MessageKey[];

describe('i18n', () => {
  it('every key has text in all three languages (TS-I18N-02)', () => {
    const missing = keys.flatMap((k) => LOCALES.filter((l) => !(messages as any)[k][l]).map((l) => `${k}:${l}`));
    expect(missing).toEqual([]);
  });
  it('falls back to English with a flag (FR-LANG-05)', () => {
    expect(lookup('site.title', 'or').fallback).toBe(false);
  });
  it('switches locale in a path', () => {
    expect(switchLocalePath('/en/about/', 'or')).toBe('/or/about/');
    expect(switchLocalePath('/hi/', 'en')).toBe('/en/');
  });
});
