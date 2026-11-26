// tokens.json -> dist/tokens.css (spec §11.2: tokens are the single source of truth).
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
export const tokens = JSON.parse(readFileSync(join(root, 'tokens.json'), 'utf8'));
const t = tokens;
const clean = (o) => Object.fromEntries(Object.entries(o).filter(([k]) => !k.startsWith('$')));

export function resolve(ref, palettes) {
  const [group, key] = ref.split('.');
  const v = palettes[group]?.[key];
  if (!v) throw new Error(`Unresolved token reference: ${ref}`);
  return v;
}
const vars = (prefix, obj) => Object.entries(clean(obj)).filter(([, v]) => typeof v === 'string').map(([k, v]) => `  --${prefix}-${k}: ${v};`);
const darkPalettes = { then: t.color['then-dark'], now: t.color['now-dark'] };

/** All mode-dependent custom properties for one mode ('then' | 'now'), light or dark. */
export function modeVars(mode, dark = false) {
  const palettes = dark ? darkPalettes : t.color;
  const vizKey = dark ? `${mode}-dark` : mode;
  return [
    ...Object.entries(t.semantic[mode]).map(([k, ref]) => `  --color-${k}: ${resolve(ref, palettes)};`),
    ...t.viz[vizKey].map((c, i) => `  --viz-${i + 1}: ${c};`),
    ...t.viz.sequential[mode].map((c, i) => `  --viz-seq-${i + 1}: ${c};`),
    ...t.viz.diverging[mode].map((c, i) => `  --viz-div-${i + 1}: ${c};`),
    ...vars('shadow', t.shadow[mode]),
    `  --radius-control: ${t.radius[mode].control};`,
    `  --radius-card: ${t.radius[mode].card};`,
  ];
}

function css() {
  const D = ':root:not([data-theme="light"])';
  return [
    '/* Generated from tokens.json — do not edit by hand. */',
    ':root {',
    ...Object.entries(t.color).flatMap(([g, o]) => vars(g, o)),
    ...vars('space', t.space), ...vars('radius', t.radius), ...vars('layout', t.layout), ...vars('tracking', t.tracking),
    ...vars('font', t.font.en), `  --font-mono: ${t.font.mono};`,
    ...vars('step', t.step), ...vars('leading', t.leading), ...vars('dur', t.duration),
    ...vars('ease', t.ease), ...vars('z', t.z),
    ...modeVars('then'),
    '}',
    '[data-mode="now"] {', ...modeVars('now'), '}',
    '[data-mode="then"] {', ...modeVars('then'), '}',
    ':lang(or) {', ...vars('font', t.font.or), '}',
    ':lang(hi) {', ...vars('font', t.font.hi), '}',
    '@media (prefers-color-scheme: dark) {',
    `  ${D} {`, ...modeVars('then', true), '  }',
    `  ${D} [data-mode="now"], ${D}[data-mode="now"] {`, ...modeVars('now', true), '  }',
    `  ${D} [data-mode="then"] {`, ...modeVars('then', true), '  }',
    '}',
    '[data-theme="dark"], [data-theme="dark"] [data-mode="then"] {', ...modeVars('then', true), '}',
    '[data-theme="dark"] [data-mode="now"], [data-theme="dark"][data-mode="now"] {', ...modeVars('now', true), '}',
    '@media (prefers-reduced-motion: reduce) {',
    '  :root { ' + Object.keys(t.duration).map((k) => `--dur-${k}: 0ms;`).join(' ') + ' }',
    '}',
    '',
  ].join('\n');
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  mkdirSync(join(root, 'dist'), { recursive: true });
  const out = css();
  writeFileSync(join(root, 'dist/tokens.css'), out);
  writeFileSync(join(root, 'dist/tokens.json'), JSON.stringify(tokens));
  console.log(`tokens.css written (${out.split('\n').length} lines)`);
}
