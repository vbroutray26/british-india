// D-17: each language's stacks cover its script, and list no other Indic script (NFR-PERF-08).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const t = JSON.parse(readFileSync(new URL('../tokens.json', import.meta.url), 'utf8'));
const css = readFileSync(new URL('../src/fonts.css', import.meta.url), 'utf8');
const ODIA = ['Noto Serif Oriya Variable', 'Anek Odia'];
const DEVA = ['Rozha One', 'Anek Devanagari'];

const expect = {
  en: { display: 'Gloock', sans: 'Urbanist Variable', serif: 'Newsreader Variable', forbid: [...ODIA, ...DEVA] },
  or: { display: 'Noto Serif Oriya Variable', sans: 'Anek Odia', serif: 'Noto Serif Oriya Variable', forbid: DEVA },
  hi: { display: 'Rozha One', sans: 'Anek Devanagari', serif: 'Rozha One', forbid: ODIA },
};
for (const [lang, e] of Object.entries(expect)) {
  for (const role of ['display', 'sans', 'serif']) {
    test(`${lang} ${role} stack includes ${e[role]}`, () => assert.ok(t.font[lang][role].includes(`'${e[role]}'`)));
    test(`${lang} ${role} stack has no other-script fonts`, () => {
      for (const f of e.forbid) assert.ok(!t.font[lang][role].includes(`'${f}'`), f);
    });
  }
}
test('every face in the stacks is self-hosted in fonts.css', () => {
  for (const p of ['gloock', 'rozha-one', 'noto-serif-oriya', 'urbanist', 'anek-devanagari', 'anek-odia', 'newsreader']) {
    assert.ok(css.includes(`/${p}/`), p);
  }
});
