<script lang="ts" generics="R extends object">
  // NFR-A11Y-04: every chart has a data table. Scrolls horizontally inside a focusable region on small screens.
  import type { Column } from './types';
  interface Props {
    caption: string;
    columns: Column<R>[];
    rows: R[];
    sortable?: boolean;
    /** Shown in empty cells; spec: "not recorded", never blank or zero. */
    emptyText: string;
  }
  let { caption, columns, rows, sortable = false, emptyText }: Props = $props();
  let sortKey: string | null = $state(null);
  let dir: 'ascending' | 'descending' = $state('ascending');
  const sorted = $derived.by(() => {
    if (!sortKey) return rows;
    const k = sortKey;
    return [...rows].sort((a, b) => {
      const x = (a as Record<string, unknown>)[k], y = (b as Record<string, unknown>)[k];
      const c = typeof x === 'number' && typeof y === 'number' ? x - y : String(x ?? '').localeCompare(String(y ?? ''));
      return dir === 'ascending' ? c : -c;
    });
  });
  function sortBy(k: string) {
    if (sortKey === k) dir = dir === 'ascending' ? 'descending' : 'ascending';
    else { sortKey = k; dir = 'ascending'; }
  }
  const show = (c: Column<R>, r: R) => {
    const v = (r as Record<string, unknown>)[c.key];
    if (v === null || v === undefined || v === '') return null;
    return c.format ? c.format(v, r) : String(v);
  };
</script>

<!-- Scrollable regions must be keyboard-focusable (WCAG 2.1.1, axe scrollable-region-focusable). -->
<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
<div class="scroll" role="region" aria-label={caption} tabindex="0">
  <table>
    <caption>{caption}</caption>
    <thead>
      <tr>
        {#each columns as c (c.key)}
          <th scope="col" class:num={c.numeric} aria-sort={sortable && sortKey === c.key ? dir : undefined}>
            {#if sortable}
              <button type="button" onclick={() => sortBy(c.key)}>{c.label}<span aria-hidden="true" class="arrow">{sortKey === c.key ? (dir === 'ascending' ? '▲' : '▼') : '↕'}</span></button>
            {:else}{c.label}{/if}
          </th>
        {/each}
      </tr>
    </thead>
    <tbody>
      {#each sorted as r, i (i)}
        <tr>
          {#each columns as c, j (c.key)}
            {@const v = show(c, r)}
            {#if j === 0}<th scope="row" class:num={c.numeric}>{v ?? emptyText}</th>
            {:else}<td class:num={c.numeric} class:empty={v === null}>{v ?? emptyText}</td>{/if}
          {/each}
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<style>
  .scroll { overflow-x: auto; border: 1px solid var(--color-rule); border-radius: var(--radius-card); }
  table { width: 100%; border-collapse: collapse; font-size: var(--step--1); }
  caption { text-align: left; padding: var(--space-3) var(--space-4); font-weight: 600; caption-side: top; }
  th, td { padding: var(--space-2) var(--space-4); text-align: left; border-top: 1px solid var(--color-rule); }
  thead th { position: sticky; top: 0; background: var(--color-surface); font-weight: 600; white-space: nowrap; }
  tbody th { font-weight: 500; }
  .num { text-align: right; font-variant-numeric: tabular-nums; }
  .empty { color: var(--color-text-muted); font-style: italic; }
  :global(:lang(or)) .empty, :global(:lang(hi)) .empty { font-style: normal; }
  thead button { all: unset; cursor: pointer; display: inline-flex; gap: var(--space-1); align-items: center; min-height: 32px; }
  thead button:focus-visible { outline: 3px solid var(--color-focus); outline-offset: 2px; }
  .arrow { font-size: 0.75em; color: var(--color-text-muted); }
</style>
