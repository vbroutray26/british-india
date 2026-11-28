<script lang="ts">
  import AIBadge from './AIBadge.svelte';
  import ReviewBadge from './ReviewBadge.svelte';
  // FR-PLACE-05 / AC-PLACE-03: a plain-language summary in three lengths. Machine-written text always carries
  // the AI label until a person has reviewed it; `lang` marks the summary's own language when it differs
  // from the page's (summaries are English until translated, DP-11).
  interface Props {
    oneLine: string;
    short: string;
    long?: string;
    method: 'llm' | 'manual';
    review: 'accepted' | 'edited' | 'unreviewed' | 'rejected';
    lang?: string;
    labels: { heading: string; ai: string; longer: string; reviewed: string; unreviewed: string; note?: string };
  }
  let { oneLine, short, long, method, review, lang, labels }: Props = $props();
  const paras = $derived((long ?? '').split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean));
  const showLong = $derived(paras.length > 0 && (long ?? '').trim() !== short.trim());
</script>

<section class="summary" class:ai={method === 'llm'} aria-label={labels.heading}>
  <div class="badges">
    {#if method === 'llm'}<AIBadge text={labels.ai} />{/if}
    <ReviewBadge status={review} labels={{ reviewed: labels.reviewed, unreviewed: labels.unreviewed }} />
  </div>
  <div {lang}>
    <p class="lead">{oneLine}</p>
    <p class="short">{short}</p>
    {#if showLong}
      <details>
        <summary>{labels.longer}</summary>
        {#each paras as p, i (i)}<p>{p}</p>{/each}
      </details>
    {/if}
  </div>
  {#if labels.note}<p class="note">{labels.note}</p>{/if}
</section>

<style>
  .summary { display: grid; gap: var(--space-3); max-width: var(--layout-reading); padding: var(--space-6); border: 1px solid var(--color-rule); border-radius: var(--radius-card); background: var(--color-surface); }
  .summary.ai { border-left: 4px solid var(--color-ai); }
  .badges { display: flex; flex-wrap: wrap; gap: var(--space-2); }
  p { margin: 0; line-height: 1.65; }
  .lead { font-size: var(--step-1); font-weight: 600; }
  details { margin-top: var(--space-3); }
  details p + p { margin-top: var(--space-3); }
  summary { cursor: pointer; min-height: 44px; display: flex; align-items: center; font-weight: 600; }
  .note { color: var(--color-text-muted); font-size: var(--step--1); }
</style>
