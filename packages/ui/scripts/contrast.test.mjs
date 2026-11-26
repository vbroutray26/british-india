// Spec §11.2: verify text/background pairs (>= 4.5:1 body, >= 3:1 UI/large).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const t = JSON.parse(readFileSync(new URL('../tokens.json', import.meta.url), 'utf8'));

function lum(hex) {
  const c = hex.replace('#', '').match(/../g).map((h) => parseInt(h, 16) / 255)
    .map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
}
export function ratio(a, b) {
  const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
}

const pairs = [
  // [palette, fg, bg, min]
  ['then', 'ink', 'paper', 4.5], ['then', 'ink-muted', 'paper', 4.5], ['then', 'red', 'paper', 4.5],
  ['then', 'ink', 'paper-2', 4.5], ['then', 'blue', 'paper', 3],
  ['then-dark', 'ink', 'paper', 4.5], ['then-dark', 'ink-muted', 'paper', 4.5], ['then-dark', 'red', 'paper', 4.5],
  ['now', 'ink', 'bg', 4.5], ['now', 'ink-muted', 'bg', 4.5], ['now', 'accent', 'bg', 4.5], ['now', 'accent-2', 'bg', 3],
  ['now-dark', 'ink', 'bg', 4.5], ['now-dark', 'ink-muted', 'bg', 4.5], ['now-dark', 'accent', 'bg', 4.5],
];

for (const [p, fg, bg, min] of pairs) {
  test(`${p}: ${fg} on ${bg} >= ${min}:1`, () => {
    const r = ratio(t.color[p][fg], t.color[p][bg]);
    assert.ok(r >= min, `${r.toFixed(2)}:1`);
  });
}
