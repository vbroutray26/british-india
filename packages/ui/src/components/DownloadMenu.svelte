<script lang="ts">
  import Icon from './Icon.svelte';
  // FR-DATA-01: JSON, CSV, GeoJSON downloads with a data dictionary. Native <details>: no JS required.
  interface Props { label: string; items: { text: string; href: string; meta?: string }[] }
  let { label, items }: Props = $props();
</script>

<details class="menu">
  <summary><Icon name="download" size={20} /><span>{label}</span><Icon name="chevron-down" size={18} /></summary>
  <ul>
    {#each items as it (it.href)}
      <li><a href={it.href} download><span>{it.text}</span>{#if it.meta}<span class="meta">{it.meta}</span>{/if}</a></li>
    {/each}
  </ul>
</details>

<style>
  .menu { position: relative; display: inline-block; }
  summary {
    display: inline-flex; align-items: center; gap: var(--space-2); min-height: 44px; padding: 0 var(--space-4);
    border: 1.5px solid var(--color-text); border-radius: var(--radius-control); cursor: pointer; list-style: none; font-weight: 600;
  }
  summary::-webkit-details-marker { display: none; }
  ul {
    position: absolute; z-index: var(--z-popover); right: 0; top: calc(100% + 4px); min-width: 240px; margin: 0; padding: var(--space-1);
    list-style: none; background: var(--color-bg); border: 1px solid var(--color-rule); border-radius: var(--radius-card); box-shadow: var(--shadow-2);
  }
  a { display: flex; justify-content: space-between; gap: var(--space-4); align-items: center; min-height: 44px; padding: 0 var(--space-3); border-radius: var(--radius-control); text-decoration: none; color: var(--color-text); }
  a:hover { background: var(--color-surface); }
  .meta { color: var(--color-text-muted); font-size: var(--step--1); font-family: var(--font-mono); }
</style>
