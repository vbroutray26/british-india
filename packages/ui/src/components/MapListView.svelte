<script lang="ts">
  import Icon from './Icon.svelte';
  import type { IconName } from './icons';
  // FR-MAP-09, AC-MAP-03: every map has a list of its visible items — for screen readers and slow connections.
  // The interactive MapLibre map itself arrives in M4 and renders beside this list.
  interface Item { name: string; type: string; icon: IconName; href: string; note?: string }
  interface Props { label: string; items: Item[]; emptyText: string }
  let { label, items, emptyText }: Props = $props();
  // Plain loop instead of Object.groupBy (Chrome 117+), for older Android phones (G-06).
  const grouped = $derived.by(() => {
    const m = new Map<string, Item[]>();
    for (const it of items) m.set(it.type, [...(m.get(it.type) ?? []), it]);
    return [...m.entries()];
  });
</script>

<section class="list" aria-label={label}>
  {#if !items.length}<p class="empty">{emptyText}</p>{/if}
  {#each grouped as [type, group] (type)}
    <h3>{type} <span class="n">({group.length})</span></h3>
    <ul>
      {#each group as it (it.href)}
        <li><Icon name={it.icon} size={18} /><a href={it.href}>{it.name}</a>{#if it.note}<span class="note">{it.note}</span>{/if}</li>
      {/each}
    </ul>
  {/each}
</section>

<style>
  h3 { font: 600 var(--step--1) var(--font-sans); margin: var(--space-4) 0 var(--space-1); text-transform: capitalize; }
  .n { color: var(--color-text-muted); font-weight: 400; }
  ul { list-style: none; margin: 0; padding: 0; }
  li { display: flex; align-items: center; gap: var(--space-2); min-height: 44px; border-bottom: 1px solid var(--color-rule); }
  .note { margin-left: auto; font-size: var(--step--1); color: var(--color-text-muted); }
  .empty { color: var(--color-text-muted); }
</style>
