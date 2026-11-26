<script lang="ts">
  import Icon from './Icon.svelte';
  import type { IconName } from './icons';
  // FR-PLACE-09: floods, famines, cyclones, administrative changes, railway arrival — as an ordered list.
  interface Event { year: string; icon: IconName; title: string; summary?: string; href?: string; source?: string }
  interface Props { label: string; events: Event[] }
  let { label, events }: Props = $props();
</script>

<ol class="timeline" aria-label={label}>
  {#each events as e, i (i)}
    <li>
      <span class="year">{e.year}</span>
      <span class="dot" aria-hidden="true"><Icon name={e.icon} size={18} /></span>
      <div class="body">
        <p class="title">{#if e.href}<a href={e.href}>{e.title}</a>{:else}{e.title}{/if}</p>
        {#if e.summary}<p class="summary">{e.summary}</p>{/if}
        {#if e.source}<p class="source">{e.source}</p>{/if}
      </div>
    </li>
  {/each}
</ol>

<style>
  .timeline { list-style: none; margin: 0; padding: 0; position: relative; }
  li { display: grid; grid-template-columns: 4.5rem 32px 1fr; gap: var(--space-3); padding-bottom: var(--space-6); position: relative; }
  li:not(:last-child)::before { content: ''; position: absolute; left: calc(4.5rem + var(--space-3) + 15px); top: 32px; bottom: 0; width: 2px; background: var(--color-rule); }
  .year { font-family: var(--font-display); font-size: var(--step-1); text-align: right; font-variant-numeric: lining-nums; line-height: 32px; }
  .dot { display: grid; place-items: center; width: 32px; height: 32px; border-radius: 50%; background: var(--color-surface); border: 1.5px solid var(--color-text); }
  p { margin: 0; }
  .title { font-weight: 600; line-height: 32px; }
  .summary { color: var(--color-text); }
  .source { font-size: var(--step--1); color: var(--color-text-muted); margin-top: var(--space-1); }
</style>
