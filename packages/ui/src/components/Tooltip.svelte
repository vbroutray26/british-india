<script lang="ts">
  import type { Snippet } from 'svelte';
  // Supplementary text on hover/focus; Escape dismisses (WCAG 1.4.13). Never the only home of essential info.
  interface Props { text: string; children: Snippet; placement?: 'top' | 'bottom' }
  let { text, children, placement = 'top' }: Props = $props();
  const id = $props.id();
  let open = $state(false);
</script>

<span
  class="wrap"
  role="presentation"
  onmouseenter={() => (open = true)} onmouseleave={() => (open = false)}
  onfocusin={() => (open = true)} onfocusout={() => (open = false)}
  onkeydown={(e) => e.key === 'Escape' && (open = false)}
  aria-describedby={id}
>
  {@render children()}
  <span role="tooltip" {id} class="tip {placement}" class:open>{text}</span>
</span>

<style>
  .wrap { position: relative; display: inline-flex; }
  .tip {
    position: absolute; left: 50%; z-index: var(--z-popover); width: max-content; max-width: 260px;
    padding: var(--space-2) var(--space-3); border-radius: var(--radius-control);
    background: var(--color-text); color: var(--color-bg); font: var(--step--1) / 1.4 var(--font-sans);
    opacity: 0; pointer-events: none; transform: translate(-50%, 4px);
    transition: opacity var(--dur-xs) var(--ease-out), transform var(--dur-xs) var(--ease-out);
  }
  .tip.top { bottom: calc(100% + 8px); }
  .tip.bottom { top: calc(100% + 8px); }
  .tip.open { opacity: 1; transform: translate(-50%, 0); }
</style>
