<script lang="ts">
  import type { Snippet } from 'svelte';
  import Button from './Button.svelte';
  import Callout from './Callout.svelte';
  // FR-ASK-01/05/06: question box with sample questions; degrades to passages-only mode with a notice.
  interface Props {
    label: string;
    placeholder: string;
    samples?: string[];
    status?: 'idle' | 'loading' | 'answered' | 'passages-only' | 'error';
    notice?: string;
    onask: (q: string) => void;
    labels: { ask: string; asking: string; tryOne: string; scope?: string };
    answer?: Snippet;
  }
  let { label, placeholder, samples = [], status = 'idle', notice, onask, labels, answer }: Props = $props();
  const id = $props.id();
  let q = $state('');
  function submit(e: Event) { e.preventDefault(); if (q.trim()) onask(q.trim()); }
</script>

<section class="ask" aria-labelledby="{id}-h">
  <form onsubmit={submit}>
    <label id="{id}-h" for="{id}-q" class="lbl">{label}</label>
    {#if labels.scope}<p class="scope">{labels.scope}</p>{/if}
    <div class="row">
      <textarea id="{id}-q" rows="2" maxlength="500" {placeholder} bind:value={q}
        onkeydown={(e) => { if (e.key === 'Enter' && !e.shiftKey) submit(e); }}></textarea>
      <Button type="submit" variant="primary" icon="ai" text={status === 'loading' ? labels.asking : labels.ask} loading={status === 'loading'} loadingLabel={labels.asking} />
    </div>
  </form>
  {#if samples.length}
    <div class="samples">
      <span class="t">{labels.tryOne}</span>
      {#each samples as s (s)}<button type="button" class="sample" onclick={() => { q = s; onask(s); }}>{s}</button>{/each}
    </div>
  {/if}
  {#if notice && (status === 'passages-only' || status === 'error')}
    <Callout kind={status === 'error' ? 'warning' : 'info'} body={notice} />
  {/if}
  <div aria-live="polite" aria-busy={status === 'loading'}>{@render answer?.()}</div>
</section>

<style>
  .ask { display: grid; gap: var(--space-4); }
  .lbl { display: block; font-family: var(--font-display); font-size: var(--step-2); margin-bottom: var(--space-1); }
  .scope { margin: 0 0 var(--space-3); color: var(--color-text-muted); font-size: var(--step--1); }
  .row { display: flex; gap: var(--space-2); align-items: stretch; flex-wrap: wrap; }
  textarea {
    flex: 1 1 280px; min-height: 56px; padding: var(--space-3) var(--space-4); resize: vertical;
    background: var(--color-bg); border: 1.5px solid var(--color-text); border-radius: var(--radius-card);
  }
  textarea:focus-visible { outline: 3px solid var(--color-focus); outline-offset: 2px; }
  .samples { display: flex; flex-wrap: wrap; gap: var(--space-2); align-items: center; }
  .t { font-size: var(--step--1); color: var(--color-text-muted); }
  .sample {
    min-height: 40px; padding: 0 var(--space-3); border: 1px dashed var(--color-text-muted); border-radius: var(--radius-pill);
    background: transparent; cursor: pointer; font-size: var(--step--1); text-align: left;
  }
  .sample:hover { border-style: solid; background: var(--color-surface); }
</style>
