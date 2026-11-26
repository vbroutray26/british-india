<script lang="ts" generics="T extends { id: string; label: string; content?: string }">
  import type { Snippet } from 'svelte';
  // WAI-ARIA tabs with automatic activation and roving tabindex. Used by EditionTabs (FR-TIME-02).
  interface Props {
    items: T[];
    label: string;
    selected?: string;
    panel?: Snippet<[T]>;
    onchange?: (id: string) => void;
  }
  let { items, label, selected = $bindable(items[0]?.id), panel, onchange }: Props = $props();
  const uid = $props.id();
  let tabEls: HTMLButtonElement[] = $state([]);

  function select(i: number, focus = true) {
    const item = items[(i + items.length) % items.length];
    selected = item.id;
    onchange?.(item.id);
    if (focus) tabEls[(i + items.length) % items.length]?.focus();
  }
  function onkeydown(e: KeyboardEvent, i: number) {
    const map: Record<string, number> = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: items.length - 1 };
    if (e.key in map) { e.preventDefault(); select(map[e.key]); }
  }
</script>

<div class="tabs">
  <div role="tablist" aria-label={label} class="list">
    {#each items as item, i (item.id)}
      <button
        bind:this={tabEls[i]}
        role="tab" type="button" id="{uid}-tab-{item.id}"
        aria-selected={selected === item.id} aria-controls="{uid}-panel-{item.id}"
        tabindex={selected === item.id ? 0 : -1}
        onclick={() => select(i, false)} onkeydown={(e) => onkeydown(e, i)}
      >{item.label}</button>
    {/each}
  </div>
  {#each items as item (item.id)}
    <div role="tabpanel" id="{uid}-panel-{item.id}" aria-labelledby="{uid}-tab-{item.id}" hidden={selected !== item.id} tabindex="0" class="panel">
      {#if panel}{@render panel(item)}{:else}{item.content}{/if}
    </div>
  {/each}
</div>

<style>
  .list { display: flex; gap: var(--space-1); border-bottom: 1px solid var(--color-rule); overflow-x: auto; }
  [role='tab'] {
    min-height: 44px; padding: 0 var(--space-4); border: 0; background: none; cursor: pointer;
    font: 500 var(--step--1) var(--font-sans); color: var(--color-text-muted); white-space: nowrap;
    border-bottom: 3px solid transparent; margin-bottom: -1px;
  }
  [role='tab'][aria-selected='true'] { color: var(--color-text); border-bottom-color: var(--color-accent); font-weight: 700; }
  [role='tab']:hover { color: var(--color-text); }
  .panel { padding: var(--space-4) 0; }
</style>
