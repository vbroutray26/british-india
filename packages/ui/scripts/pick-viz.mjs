// Search for 8 categorical chart colours per mode that satisfy the tests in contrast.test.mjs:
// >= 3:1 on the background, ΔE >= 20 pairwise (normal vision), and the first 6 at ΔE >= 10 under
// protanopia, deuteranopia and tritanopia. Seeds keep the palette on-brand.
// Usage: node scripts/pick-viz.mjs   (prints JSON to paste into tokens.json "viz")
const rgb = (hex) => hex.replace('#', '').match(/../g).map((h) => parseInt(h, 16) / 255);
const lin = (v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
const lum = (hex) => { const [r, g, b] = rgb(hex).map(lin); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
const M = {
  p: [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]],
  d: [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.01182, 0.04294, 0.968881]],
  t: [[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.3039]],
};
const toLab = ([r, g, b]) => {
  const X = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047, Y = 0.2126 * r + 0.7152 * g + 0.0722 * b, Z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883;
  const f = (v) => (v > 0.008856 ? Math.cbrt(v) : 7.787 * v + 16 / 116);
  return [116 * f(Y) - 16, 500 * (f(X) - f(Y)), 200 * (f(Y) - f(Z))];
};
const sim = (hex, m) => { const c = rgb(hex).map(lin); return m.map((r) => Math.min(1, Math.max(0, r[0] * c[0] + r[1] * c[1] + r[2] * c[2]))); };
const dE = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
const hsl = (h, s, l) => {
  const k = (n) => (n + h / 30) % 12, a = s * Math.min(l, 1 - l);
  const f = (n) => l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));
  return '#' + [f(0), f(8), f(4)].map((v) => Math.round(v * 255).toString(16).padStart(2, '0')).join('').toUpperCase();
};
const views = (hex) => [toLab(rgb(hex).map(lin)), toLab(sim(hex, M.p)), toLab(sim(hex, M.d)), toLab(sim(hex, M.t))];

// Target hues per slot (survey-map palette: red, blue, green, ochre, purple, teal, rose, slate).
const TARGETS = [12, 215, 100, 38, 275, 178, 335, 205];
const hueOf = (hex) => {
  const [r, g, b] = rgb(hex), mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
  if (!d) return 0;
  const h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return (h * 60 + 360) % 360;
};
const hueDist = (a, b) => Math.min(Math.abs(a - b), 360 - Math.abs(a - b));

function pick(bg, seeds, dark) {
  const cands = [];
  for (let h = 0; h < 360; h += 4) for (const s of [0.25, 0.35, 0.45, 0.55, 0.65, 0.75]) for (let l = dark ? 0.55 : 0.3; l <= (dark ? 0.82 : 0.52); l += 0.025) {
    const c = hsl(h, s, l);
    if (ratio(c, bg) >= 3.2) cands.push({ c, h, s });
  }
  const chosen = [];
  const ok = (c, i) => {
    const v = views(c);
    return chosen.every((o, j) => {
      const w = views(o);
      if (dE(v[0], w[0]) < 22) return false;
      if (i < 6 && j < 6) return [1, 2, 3].every((k) => dE(v[k], w[k]) >= 11);
      return true;
    });
  };
  for (const s of seeds) if (ok(s, chosen.length)) chosen.push(s);
  while (chosen.length < 8) {
    const target = TARGETS[chosen.length];
    const ranked = cands
      .map((x) => ({ ...x, cost: hueDist(x.h, target) / 30 + x.s * 1.5 }))
      .sort((a, b) => a.cost - b.cost);
    const hit = ranked.find((x) => ok(x.c, chosen.length));
    if (!hit) throw new Error(`no candidate for slot ${chosen.length + 1} on ${bg}`);
    chosen.push(hit.c);
  }
  return chosen;
}
const out = {
  then: pick('#EFE5CF', ['#A63A24', '#2B4A7A'], false),
  'then-dark': pick('#17130E', ['#E07A5F', '#8FA9D6'], true),
  now: pick('#FAFAF7', ['#0E7C86', '#D1495B'], false),
  'now-dark': pick('#0B1017', ['#3CC3CC', '#FF8A80'], true),
};
console.log(JSON.stringify(out, null, 2));
