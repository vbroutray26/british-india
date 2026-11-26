<script lang="ts">
  // FR-TIME-01, AC-TIME-01: move across the years available for this place; the year is announced.
  // A native range input mapped to the list of years: keyboard, touch and screen readers work by default.
  interface Props {
    years: number[];
    value?: number;
    label: string;
    /** Marks a year as modern data ("Now") so it is visually distinct. */
    nowYear?: number;
    onchange?: (year: number) => void;
  }
  let { years, value = $bindable(years[0]), label, nowYear, onchange }: Props = $props();
  const id = $props.id();
  const index = $derived(Math.max(0, years.indexOf(value)));
  function set(i: number) { value = years[i]; onchange?.(value); }
</script>

<div class="dial">
  <div class="top">
    <label for="{id}-r">{label}</label>
    <output for="{id}-r" class="year" class:now={value === nowYear} aria-live="polite">{value}</output>
  </div>
  <input
    id="{id}-r" type="range" min="0" max={years.length - 1} step="1" value={index}
    aria-valuetext={String(value)} list="{id}-ticks"
    oninput={(e) => set(+(e.currentTarget as HTMLInputElement).value)}
  />
  <datalist id="{id}-ticks">{#each years as _, i (i)}<option value={i}></option>{/each}</datalist>
  <ol class="ticks" aria-hidden="true">
    {#each years as y, i (y)}
      <li class:on={i === index} class:now={y === nowYear}><button type="button" tabindex="-1" onclick={() => set(i)}>{y}</button></li>
    {/each}
  </ol>
</div>

<style>
  .dial { display: grid; gap: var(--space-2); }
  .top { display: flex; justify-content: space-between; align-items: baseline; }
  label { font-weight: 600; font-size: var(--step--1); }
  .year { font-family: var(--font-display); font-size: var(--step-3); line-height: 1; font-variant-numeric: lining-nums; }
  .year.now { color: var(--color-accent); }
  input { width: 100%; height: 44px; margin: 0; accent-color: var(--color-accent); cursor: pointer; background: transparent; }
  input:focus-visible { outline: 3px solid var(--color-focus); outline-offset: 2px; }
  .ticks { list-style: none; margin: 0; padding: 0; display: flex; justify-content: space-between; font-size: var(--step--1); color: var(--color-text-muted); font-variant-numeric: tabular-nums; }
  .ticks button { all: unset; cursor: pointer; padding: var(--space-1); }
  .ticks .on { color: var(--color-text); font-weight: 700; }
  .ticks .now { font-style: italic; }
</style>
