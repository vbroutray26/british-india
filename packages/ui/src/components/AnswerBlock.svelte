<script lang="ts">
  import AIBadge from './AIBadge.svelte';
  import Button from './Button.svelte';
  import CitationChip from './CitationChip.svelte';
  // FR-ASK-02..04, 08, 09; AC-ASK-01/02: every sentence carries a verified citation, or the answer says it couldn't find it.
  interface Citation { text: string; href: string; quote: string }
  interface Passage { text: string; source: string; href: string }
  interface Props {
    sentences?: { text: string; citations: Citation[] }[];
    unanswerable?: boolean;
    nearest?: Passage[];
    labels: { ai: string; unanswerable: string; nearest: string; helpful: string; notHelpful: string; report: string; thanks: string };
    reportHref?: string;
    onfeedback?: (v: 'up' | 'down') => void;
  }
  let { sentences = [], unanswerable = false, nearest = [], labels, reportHref, onfeedback }: Props = $props();
  let voted: 'up' | 'down' | null = $state(null);
  function vote(v: 'up' | 'down') { voted = v; onfeedback?.(v); }
</script>

<article class="answer">
  {#if unanswerable || !sentences.length}
    <p class="none">{labels.unanswerable}</p>
  {:else}
    <AIBadge text={labels.ai} />
    <p class="text">
      {#each sentences as s, i (i)}{s.text}{#each s.citations as c (c.href)}<CitationChip text={c.text} href={c.href} quote={c.quote} />{/each}{' '}{/each}
    </p>
  {/if}
  {#if nearest.length}
    <h3>{labels.nearest}</h3>
    <ol class="nearest">
      {#each nearest as p (p.href)}<li><a href={p.href}>{p.source}</a><blockquote>{p.text}</blockquote></li>{/each}
    </ol>
  {/if}
  <footer>
    {#if voted}<span role="status">{labels.thanks}</span>
    {:else}
      <Button size="sm" variant="ghost" icon="check" text={labels.helpful} onclick={() => vote('up')} />
      <Button size="sm" variant="ghost" icon="close" text={labels.notHelpful} onclick={() => vote('down')} />
    {/if}
    {#if reportHref}<a href={reportHref} class="report">{labels.report}</a>{/if}
  </footer>
</article>

<style>
  .answer { display: grid; gap: var(--space-3); padding: var(--space-6); border: 1px solid var(--color-rule); border-left: 4px solid var(--color-ai); border-radius: var(--radius-card); background: var(--color-surface); }
  .answer > :global(.badge) { justify-self: start; }
  .text { margin: 0; font-size: var(--step-1); line-height: 1.7; }
  .none { margin: 0; font-size: var(--step-1); font-weight: 600; }
  h3 { margin: var(--space-2) 0 0; font: 600 var(--step--1) var(--font-sans); }
  .nearest { margin: 0; padding-left: var(--space-6); display: grid; gap: var(--space-3); }
  blockquote { margin: var(--space-1) 0 0; font-family: var(--font-serif); color: var(--color-text-muted); }
  footer { display: flex; flex-wrap: wrap; gap: var(--space-2); align-items: center; border-top: 1px solid var(--color-rule); padding-top: var(--space-3); font-size: var(--step--1); }
  .report { margin-left: auto; color: var(--color-text-muted); }
</style>
