<script lang="ts">
  import Icon from './Icon.svelte';
  import type { IconName } from './icons';
  // FR-HOME-08 / FR-DISC-02: floods, famine, cyclones, railways, ports, temples, trade.
  interface Props { icon: IconName; title: string; blurb: string; href: string; count?: string }
  let { icon, title, blurb, href, count }: Props = $props();
</script>

<article class="theme">
  <span class="ic" aria-hidden="true"><Icon name={icon} size={36} /></span>
  <h3><a {href}>{title}</a></h3>
  <p>{blurb}</p>
  {#if count}<p class="count">{count}</p>{/if}
</article>

<style>
  .theme {
    position: relative; display: grid; gap: var(--space-2); align-content: start; padding: var(--space-6);
    border: 1px solid var(--color-rule); border-radius: var(--radius-card); background: var(--color-surface);
    transition: transform var(--dur-sm) var(--ease-out), box-shadow var(--dur-sm) var(--ease-out);
  }
  .theme:hover { transform: translateY(-2px); box-shadow: var(--shadow-2); }
  .theme:has(a:focus-visible) { outline: 3px solid var(--color-focus); outline-offset: 2px; }
  .ic { color: var(--color-accent); }
  h3 { margin: 0; font-size: var(--step-2); }
  h3 a { color: var(--color-text); text-decoration: none; }
  h3 a::after { content: ''; position: absolute; inset: 0; }
  h3 a:focus-visible { outline: none; }
  p { margin: 0; color: var(--color-text-muted); }
  .count { font-size: var(--step--1); font-weight: 600; color: var(--color-text); }
</style>
