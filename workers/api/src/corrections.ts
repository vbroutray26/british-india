// FR-CORR-01..07. No account; honeypot + optional Turnstile; size limits.
export interface Correction {
  item_id: string;
  what_is_wrong: string;
  suggested_fix: string;
  source?: string;
  email?: string;
  lang?: string;
}

export const LIMITS = { item_id: 200, what_is_wrong: 4000, suggested_fix: 4000, source: 1000, email: 254 } as const;
export const MAX_BODY_BYTES = 16_384;

export type ParseResult =
  | { ok: true; value: Correction }
  | { ok: false; status: 400 | 413; error: string }
  | { ok: 'spam' };

const str = (v: unknown) => (typeof v === 'string' ? v.trim() : '');

export function parseCorrection(body: Record<string, unknown>): ParseResult {
  // Honeypot: bots fill the hidden "website" field. Reject silently (AC-CORR-03).
  if (str(body.website)) return { ok: 'spam' };
  const value: Correction = {
    item_id: str(body.item_id),
    what_is_wrong: str(body.what_is_wrong),
    suggested_fix: str(body.suggested_fix),
    source: str(body.source) || undefined,
    email: str(body.email) || undefined,
    lang: ['en', 'or', 'hi'].includes(str(body.lang)) ? str(body.lang) : 'en',
  };
  if (!value.item_id || !value.what_is_wrong) return { ok: false, status: 400, error: 'item_id and what_is_wrong are required' };
  for (const [k, max] of Object.entries(LIMITS)) {
    const v = value[k as keyof Correction];
    if (v && v.length > max) return { ok: false, status: 413, error: `${k} too long` };
  }
  if (value.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.email)) return { ok: false, status: 400, error: 'invalid email' };
  return { ok: true, value };
}
