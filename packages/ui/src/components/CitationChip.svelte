<script lang="ts">
  import Tooltip from './Tooltip.svelte';
  // FR-ASK-02/03: each AI sentence links to its passage; hovering shows the supporting quote.
  interface Props { text: string; href: string; quote?: string }
  let { text, href, quote }: Props = $props();
</script>

{#if quote}
  <Tooltip text={`“${quote}”`}><a class="chip" {href}>{text}</a></Tooltip>
{:else}
  <a class="chip" {href}>{text}</a>
{/if}

<style>
  .chip {
    display: inline-flex; align-items: center; min-height: 28px; padding: 0 var(--space-2); margin: 0 2px;
    font: 600 var(--step--1) / 1 var(--font-sans); text-decoration: none; vertical-align: 0.1em;
    color: var(--color-link); border: 1px solid currentColor; border-radius: var(--radius-pill);
  }
  .chip:hover { background: var(--color-surface); }
</style>
