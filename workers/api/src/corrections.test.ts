import { describe, expect, it } from 'vitest';
import { parseCorrection } from './corrections';

const base = { item_id: 'ft_x', what_is_wrong: 'Wrong year', suggested_fix: '1866' };

describe('parseCorrection', () => {
  it('accepts a minimal valid correction', () => {
    expect(parseCorrection(base)).toMatchObject({ ok: true });
  });
  it('treats a filled honeypot as spam (AC-CORR-03)', () => {
    expect(parseCorrection({ ...base, website: 'http://spam' })).toEqual({ ok: 'spam' });
  });
  it('requires item_id and what_is_wrong', () => {
    expect(parseCorrection({ suggested_fix: 'x' })).toMatchObject({ ok: false, status: 400 });
  });
  it('rejects oversize fields (TS-SEC-04)', () => {
    expect(parseCorrection({ ...base, what_is_wrong: 'x'.repeat(5000) })).toMatchObject({ ok: false, status: 413 });
  });
  it('rejects malformed email but allows none', () => {
    expect(parseCorrection({ ...base, email: 'nope' })).toMatchObject({ ok: false });
    expect(parseCorrection(base)).toMatchObject({ ok: true });
  });
});
