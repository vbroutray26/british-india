<script lang="ts">
  import Icon from './Icon.svelte';
  import ReviewBadge from './ReviewBadge.svelte';
  import AIBadge from './AIBadge.svelte';
  import type { IconName } from './icons';
  import type { ReviewStatus } from './types';
  // FR-PLACE-03/04, AC-PLACE-01/05: value, year, source, "view passage", review badge; missing data is explicit.
  interface Props {
    icon: IconName;
    label: string;
    /** Formatted value, e.g. "49,334" or "Rice, sugar-cane". Omit when the sources do not record it. */
    value?: string;
    unit?: string;
    /** e.g. "1908" */
    year?: string;
    source?: string;
    passageHref?: string;
    review: ReviewStatus;
    method?: 'rule' | 'llm' | 'manual';
    approximate?: boolean;
    /** 'text' for names (temples, crops, festivals): set in reading type rather than the display figure style. */
    valueKind?: 'number' | 'text';
    correctHref?: string;
    labels: {
      viewPassage: string; reviewed: string; unreviewed: string; notRecorded: string;
      machineExtracted: string; approximate: string; correct: string;
    };
  }
  let { icon, label, value, unit, year, source, passageHref, review, method, approximate = false, valueKind = 'number', correctHref, labels }: Props = $props();
</script>

<article class="fact" class:missing={!value}>
  <header>
    <span class="ic"><Icon name={icon} /></span>
    <h3>{label}</h3>
  </header>
  {#if value}
    <p class="value" class:text={valueKind === 'text'}>{value}{#if unit}<span class="unit">{unit}</span>{/if}</p>
    {#if approximate}<p class="approx">≈ {labels.approximate}</p>{/if}
    <p class="meta">
      {#if year}<span class="year">{year}</span>{/if}
      {#if source}<span>{source}</span>{/if}
    </p>
  {:else}
    <p class="none">{labels.notRecorded}</p>
  {/if}
  <footer>
    <div class="badges">
      <ReviewBadge status={review} labels={{ reviewed: labels.reviewed, unreviewed: labels.unreviewed }} />
      {#if method === 'llm'}<AIBadge text={labels.machineExtracted} />{/if}
    </div>
    <div class="links">
      {#if value && passageHref}<a href={passageHref}>{labels.viewPassage}</a>{/if}
      {#if correctHref}<a href={correctHref} class="correct">{labels.correct}</a>{/if}
    </div>
  </footer>
</article>

<style>
  .fact {
    display: grid; gap: var(--space-2); align-content: start; padding: var(--space-4);
    background: var(--color-surface); border: 1px solid var(--color-rule); border-radius: var(--radius-card); box-shadow: var(--shadow-1);
  }
  .fact p { margin: 0; }
  header { display: flex; align-items: center; gap: var(--space-2); color: var(--color-text-muted); }
  h3 { margin: 0; font: 600 var(--step--1) / 1.3 var(--font-sans); letter-spacing: var(--tracking-label); text-transform: uppercase; }
  :global(:lang(or)) h3, :global(:lang(hi)) h3 { text-transform: none; letter-spacing: 0; }
  .value { font-family: var(--font-display); font-size: var(--step-3); line-height: 1.1; font-variant-numeric: lining-nums; overflow-wrap: anywhere; }
  .value.text { font-family: var(--font-serif); font-size: var(--step-1); line-height: 1.4; }
  .unit { margin-left: 0.35em; font-family: var(--font-sans); font-size: var(--step-0); color: var(--color-text-muted); }
  .approx { font-size: var(--step--1); color: var(--color-warning); font-weight: 600; }
  .meta { display: flex; flex-wrap: wrap; gap: var(--space-1) var(--space-3); font-size: var(--step--1); color: var(--color-text-muted); }
  .year { font-weight: 700; color: var(--color-text); font-variant-numeric: tabular-nums; }
  .none { color: var(--color-text-muted); font-style: italic; }
  :global(:lang(or)) .none, :global(:lang(hi)) .none { font-style: normal; }
  .missing { background: transparent; border-style: dashed; box-shadow: none; }
  footer { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: var(--space-2); margin-top: var(--space-2); }
  .badges, .links { display: flex; flex-wrap: wrap; gap: var(--space-2); align-items: center; }
  .links a { display: inline-flex; align-items: center; min-height: 44px; font-size: var(--step--1); font-weight: 600; }
  .correct { color: var(--color-text-muted); }
</style>
