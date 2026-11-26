// Spec §11.2 / NFR-A11Y-01: text >= 4.5:1, UI and chart marks >= 3:1, in all four modes.
// Spec §11.2: categorical chart colours stay distinguishable under common colour-vision deficiencies.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const t = JSON.parse(readFileSync(new URL('../tokens.json', import.meta.url), 'utf8'));

const rgb = (hex) => hex.replace('#', '').match(/../g).map((h) => parseInt(h, 16) / 255);
const lin = (v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
const lum = (hex) => { const [r, g, b] = rgb(hex).map(lin); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
export const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };

const MODES = [['then', 'then'], ['then-dark', 'then'], ['now', 'now'], ['now-dark', 'now']];
const sem = (palette, mode, key) => {
  const [, k] = t.semantic[mode][key].split('.');
  return t.color[palette][k];
};

for (const [palette, mode] of MODES) {
  const bg = sem(palette, mode, 'bg');
  const surface = sem(palette, mode, 'surface');
  for (const key of ['text', 'text-muted', 'link', 'danger', 'warning', 'success', 'review-pending', 'ai']) {
    for (const [name, back] of [['bg', bg], ['surface', surface]]) {
      test(`${palette}: ${key} on ${name} >= 4.5:1`, () => {
        const r = ratio(sem(palette, mode, key), back);
        assert.ok(r >= 4.5, `${r.toFixed(2)}:1`);
      });
    }
  }
  test(`${palette}: on-accent text on accent >= 4.5:1`, () => {
    const r = ratio(sem(palette, mode, 'on-accent'), sem(palette, mode, 'accent'));
    assert.ok(r >= 4.5, `${r.toFixed(2)}:1`);
  });
  for (const key of ['focus']) { // logo-accent is exempt: logos are excluded from WCAG 1.4.11
    test(`${palette}: ${key} on bg >= 3:1 (UI)`, () => {
      const r = ratio(sem(palette, mode, key), bg);
      assert.ok(r >= 3, `${r.toFixed(2)}:1`);
    });
  }
  t.viz[palette].forEach((c, i) => {
    test(`${palette}: viz-${i + 1} ${c} on bg >= 3:1`, () => {
      const r = ratio(c, bg);
      assert.ok(r >= 3, `${r.toFixed(2)}:1`);
    });
  });
}

// --- Colour-vision deficiency check (Machado et al. 2009, severity 1.0) in CIELAB.
const CVD = {
  protanopia: [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]],
  deuteranopia: [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.01182, 0.04294, 0.968881]],
  tritanopia: [[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.3039]],
};
const toLab = ([r, g, b]) => {
  const X = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047, Y = 0.2126 * r + 0.7152 * g + 0.0722 * b, Z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883;
  const f = (v) => (v > 0.008856 ? Math.cbrt(v) : 7.787 * v + 16 / 116);
  return [116 * f(Y) - 16, 500 * (f(X) - f(Y)), 200 * (f(Y) - f(Z))];
};
const simulate = (hex, m) => { const c = rgb(hex).map(lin); return m.map((row) => Math.min(1, Math.max(0, row[0] * c[0] + row[1] * c[1] + row[2] * c[2]))); };
const dE = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
const MIN_DE = 10; // perceptibly different at chart-mark sizes

for (const palette of ['then', 'then-dark', 'now', 'now-dark']) {
  const colours = t.viz[palette];
  test(`${palette}: categorical colours distinct with normal vision (ΔE >= 20)`, () => {
    for (let i = 0; i < colours.length; i++) for (let j = i + 1; j < colours.length; j++) {
      const d = dE(toLab(rgb(colours[i]).map(lin)), toLab(rgb(colours[j]).map(lin)));
      assert.ok(d >= 20, `viz-${i + 1} vs viz-${j + 1}: ΔE ${d.toFixed(1)}`);
    }
  });
  for (const [name, m] of Object.entries(CVD)) {
    test(`${palette}: first 6 categorical colours distinct under ${name} (ΔE >= ${MIN_DE})`, () => {
      const six = colours.slice(0, 6);
      for (let i = 0; i < six.length; i++) for (let j = i + 1; j < six.length; j++) {
        const d = dE(toLab(simulate(six[i], m)), toLab(simulate(six[j], m)));
        assert.ok(d >= MIN_DE, `viz-${i + 1} vs viz-${j + 1}: ΔE ${d.toFixed(1)}`);
      }
    });
  }
}
