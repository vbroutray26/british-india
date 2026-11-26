<script lang="ts" generics="T extends { id: string; title: string; content?: string }">
  import type { Snippet } from 'svelte';
  import Icon from './Icon.svelte';
  // Native <details>: works without JavaScript and with every screen reader.
  interface Props { items: T[]; panel?: Snippet<[T]>; open?: string[] }
  let { items, panel, open = [] }: Props = $props();
</script>

<div class="accordion">
  {#each items as item (item.id)}
    <details open={open.includes(item.id)}>
      <summary><span>{item.title}</span><Icon name="chevron-down" size={20} /></summary>
      <div class="body">{#if panel}{@render panel(item)}{:else}{item.content}{/if}</div>
    </details>
  {/each}
</div>

<style>
  details { border-bottom: 1px solid var(--color-rule); }
  summary {
    display: flex; justify-content: space-between; align-items: center; gap: var(--space-4);
    min-height: 48px; cursor: pointer; list-style: none; font-weight: 600;
  }
  summary::-webkit-details-marker { display: none; }
  summary :global(.icon) { transition: transform var(--dur-sm) var(--ease-out); }
  details[open] summary :global(.icon) { transform: rotate(180deg); }
  .body { padding: 0 0 var(--space-4); }
</style>
