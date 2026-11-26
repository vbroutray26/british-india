// tokens.json -> dist/tokens.css (spec §11.2: tokens are the single source of truth)
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const t = JSON.parse(readFileSync(join(root, 'tokens.json'), 'utf8'));

export function resolve(ref, palette) {
  const [group, key] = ref.split('.');
  const v = palette[group]?.[key];
  if (!v) throw new Error(`Unresolved token reference: ${ref}`);
  return v;
}

function vars(prefix, obj) {
  return Object.entries(obj).map(([k, v]) => `  --${prefix}-${k}: ${v};`);
}

function semantic(mode, palette) {
  return Object.entries(t.semantic[mode]).map(([k, ref]) => `  --color-${k}: ${resolve(ref, palette)};`);
}

const dark = { then: t.color['then-dark'], now: t.color['now-dark'] };
const lines = [
  '/* Generated from tokens.json — do not edit by hand. */',
  ':root {',
  ...Object.entries(t.color).flatMap(([g, o]) => vars(g, o)),
  ...vars('space', t.space), ...vars('radius', t.radius), ...vars('font', t.font.en), `  --font-mono: ${t.font.mono};`,
  ...vars('step', t.step), ...vars('leading', t.leading), ...vars('dur', t.duration),
  ...vars('ease', t.ease), ...vars('z', t.z),
  ...semantic('then', t.color),
  '}',
  '[data-mode="now"] {', ...semantic('now', t.color), '}',
  ':lang(or) {', ...vars('font', t.font.or), '}',
  ':lang(hi) {', ...vars('font', t.font.hi), '}',
  '@media (prefers-color-scheme: dark) {',
  '  :root:not([data-theme="light"]) {', ...semantic('then', dark), '  }',
  '  :root:not([data-theme="light"]) [data-mode="now"], :root:not([data-theme="light"])[data-mode="now"] {', ...semantic('now', dark), '  }',
  '}',
  '[data-theme="dark"] {', ...semantic('then', dark), '}',
  '[data-theme="dark"] [data-mode="now"], [data-theme="dark"][data-mode="now"] {', ...semantic('now', dark), '}',
  '@media (prefers-reduced-motion: reduce) {',
  '  :root { ' + Object.keys(t.duration).map((k) => `--dur-${k}: 0ms;`).join(' ') + ' }',
  '}',
  '',
];
mkdirSync(join(root, 'dist'), { recursive: true });
writeFileSync(join(root, 'dist/tokens.css'), lines.join('\n'));
console.log(`tokens.css written (${lines.length} lines)`);
