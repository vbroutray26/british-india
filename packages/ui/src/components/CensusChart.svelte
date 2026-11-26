<script lang="ts">
  import DataTable from './DataTable.svelte';
  import type { CensusPoint, Column } from './types';
  // FR-TIME-03/04, AC-TIME-02/03: each point labelled with unit and boundary version; incompatible versions are
  // never joined by a line; approximate (crosswalk) points are hollow and dashed. Includes a data table (NFR-A11Y-04).
  interface Props {
    title: string;
    description: string;
    points: CensusPoint[];
    selectedYear?: number;
    locale?: string;
    labels: { population: string; year: string; unit: string; boundary: string; source: string; approximate: string; showTable: string; notRecorded: string; boundaryChange: string };
  }
  let { title, description, points, selectedYear, locale = 'en-IN', labels }: Props = $props();
  const id = $props.id();
  const W = 640, H = 300, M = { t: 24, r: 16, b: 36, l: 64 };
  const fmt = $derived(new Intl.NumberFormat(locale));
  const sorted = $derived([...points].sort((a, b) => a.year - b.year));
  const groups = $derived.by(() => {
    const order: string[] = [];
    for (const p of sorted) if (!order.includes(p.boundary)) order.push(p.boundary);
    return order.map((b, i) => ({ boundary: b, i, pts: sorted.filter((p) => p.boundary === b) }));
  });
  const x0 = $derived(Math.min(...sorted.map((p) => p.year))), x1 = $derived(Math.max(...sorted.map((p) => p.year)));
  const yMax = $derived(niceMax(Math.max(...sorted.map((p) => p.value))));
  const x = (yr: number) => M.l + ((yr - x0) / Math.max(1, x1 - x0)) * (W - M.l - M.r);
  const y = (v: number) => H - M.b - (v / yMax) * (H - M.t - M.b);
  const yTicks = $derived([0, 0.25, 0.5, 0.75, 1].map((f) => f * yMax));
  const xTicks = $derived(sorted.map((p) => p.year).filter((v, i, a) => a.indexOf(v) === i));
  function niceMax(v: number) {
    const p = 10 ** Math.floor(Math.log10(v || 1));
    return [1, 2, 2.5, 5, 10].map((m) => m * p).find((n) => n >= v * 1.05) ?? 10 * p;
  }
  const compact = (v: number) => new Intl.NumberFormat(locale, { notation: 'compact', maximumFractionDigits: 1 }).format(v);
  // Segments: connect only consecutive exact points; approximate links are dashed.
  const segs = (pts: CensusPoint[]) => pts.slice(1).map((p, k) => ({ a: pts[k], b: p, approx: !!(pts[k].approximate || p.approximate) }));
  const SHAPES = ['circle', 'square', 'diamond', 'triangle'];
  // Where one boundary version ends and the next begins: a labelled break, so the gap is explained.
  const breaks = $derived(groups.slice(1).map((g, k) => (groups[k].pts.at(-1)!.year + g.pts[0].year) / 2));
  const columns: Column<CensusPoint>[] = $derived([
    { key: 'year' as const, label: labels.year },
    { key: 'value' as const, label: labels.population, numeric: true, format: (v: unknown, r: CensusPoint) => fmt.format(v as number) + (r.approximate ? ` (${labels.approximate})` : '') },
    { key: 'unit' as const, label: labels.unit },
    { key: 'boundary' as const, label: labels.boundary },
    { key: 'source' as const, label: labels.source },
  ]);
</script>

<figure class="chart" aria-labelledby="{id}-t">
  <figcaption id="{id}-t" class="title">{title}</figcaption>
  <svg class="plot" viewBox="0 0 {W} {H}" role="img" aria-labelledby="{id}-st {id}-sd" preserveAspectRatio="xMidYMid meet">
    <title id="{id}-st">{title}</title>
    <desc id="{id}-sd">{description}</desc>
    {#each yTicks as t (t)}
      <line class="grid" x1={M.l} x2={W - M.r} y1={y(t)} y2={y(t)} />
      <text class="tick" x={M.l - 8} y={y(t)} dy="0.32em" text-anchor="end">{compact(t)}</text>
    {/each}
    {#each xTicks as yr (yr)}<text class="tick" x={x(yr)} y={H - M.b + 20} text-anchor="middle">{yr}</text>{/each}
    {#if selectedYear !== undefined && selectedYear >= x0 && selectedYear <= x1}
      <line class="sel" x1={x(selectedYear)} x2={x(selectedYear)} y1={M.t} y2={H - M.b} />
    {/if}
    {#each breaks as b (b)}
      <line class="brk" x1={x(b)} x2={x(b)} y1={M.t} y2={H - M.b} />
      <text class="brk-l" x={x(b)} y={M.t} dy="-4" text-anchor="middle">{labels.boundaryChange}</text>
    {/each}
    {#each groups as g (g.boundary)}
      <g class="series s{(g.i % 8) + 1}">
        {#each segs(g.pts) as s, k (k)}
          <line class="seg" class:approx={s.approx} x1={x(s.a.year)} y1={y(s.a.value)} x2={x(s.b.year)} y2={y(s.b.value)} />
        {/each}
        {#each g.pts as p (p.year)}
          {@const cx = x(p.year)}
          {@const cy = y(p.value)}
          {@const shape = SHAPES[g.i % SHAPES.length]}
          <g class="pt" class:approx={p.approximate} class:on={p.year === selectedYear}>
            {#if shape === 'circle'}<circle {cx} {cy} r="5" />
            {:else if shape === 'square'}<rect x={cx - 4.5} y={cy - 4.5} width="9" height="9" />
            {:else if shape === 'diamond'}<path d="M{cx} {cy - 6}l6 6-6 6-6-6z" />
            {:else}<path d="M{cx} {cy - 6}l6 10.4h-12z" />{/if}
            <title>{p.year}: {fmt.format(p.value)} — {p.unit}{p.approximate ? ` (${labels.approximate})` : ''}</title>
          </g>
        {/each}
      </g>
    {/each}
  </svg>
  <ul class="legend">
    {#each groups as g (g.boundary)}
      <li class="s{(g.i % 8) + 1}"><svg width="28" height="14" aria-hidden="true"><line x1="0" x2="28" y1="7" y2="7" /><circle cx="14" cy="7" r="4" /></svg>{g.boundary}</li>
    {/each}
    {#if sorted.some((p) => p.approximate)}<li class="ap"><svg width="28" height="14" aria-hidden="true"><line x1="0" x2="28" y1="7" y2="7" /><circle cx="14" cy="7" r="4" /></svg>{labels.approximate}</li>{/if}
  </ul>
  <details class="tbl">
    <summary>{labels.showTable}</summary>
    <DataTable caption={title} {columns} rows={sorted} emptyText={labels.notRecorded} />
  </details>
</figure>

<style>
  .chart { margin: 0; display: grid; gap: var(--space-3); }
  .title { font-family: var(--font-display); font-size: var(--step-2); }
  .plot { width: 100%; height: auto; overflow: visible; }
  .grid { stroke: var(--color-rule); stroke-width: 1; }
  .tick { fill: var(--color-text-muted); font: 12px var(--font-sans); font-variant-numeric: tabular-nums; }
  .sel { stroke: var(--color-text); stroke-width: 1.5; stroke-dasharray: 3 3; }
  .brk { stroke: var(--color-warning); stroke-width: 1.5; stroke-dasharray: 1 4; stroke-linecap: round; }
  .brk-l { fill: var(--color-warning); font: 600 11px var(--font-sans); }
  .seg { stroke-width: 2.5; fill: none; }
  .seg.approx { stroke-dasharray: 6 5; }
  .pt :is(circle, rect, path) { stroke-width: 2; }
  .pt.approx :is(circle, rect, path) { fill: var(--color-bg) !important; stroke-dasharray: 2 2; }
  .pt.on :is(circle, rect, path) { stroke-width: 4; }
  .s1 { --c: var(--viz-1); } .s2 { --c: var(--viz-2); } .s3 { --c: var(--viz-3); } .s4 { --c: var(--viz-4); }
  .s5 { --c: var(--viz-5); } .s6 { --c: var(--viz-6); } .s7 { --c: var(--viz-7); } .s8 { --c: var(--viz-8); }
  .series .seg, .series .pt :is(circle, rect, path) { stroke: var(--c); }
  .series .pt :is(circle, rect, path) { fill: var(--c); }
  .legend { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: var(--space-2) var(--space-4); font-size: var(--step--1); }
  .legend li { display: inline-flex; align-items: center; gap: var(--space-2); flex: none; max-width: 100%; }
  .legend svg { flex: none; }
  .legend line { stroke: var(--c, var(--color-text-muted)); stroke-width: 2.5; }
  .legend circle { fill: var(--c, var(--color-bg)); stroke: var(--c, var(--color-text-muted)); stroke-width: 2; }
  .legend .ap line { stroke-dasharray: 5 4; }
  .legend .ap circle { fill: var(--color-bg); stroke-dasharray: 2 2; }
  .tbl summary { cursor: pointer; font-weight: 600; min-height: 44px; display: flex; align-items: center; }
  .tbl :global(.scroll) { margin-top: var(--space-2); }
</style>
