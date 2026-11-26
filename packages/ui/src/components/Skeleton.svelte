<script lang="ts">
  // Loading placeholder that reserves space (NFR-PERF-03, CLS). Decorative: hidden from assistive tech.
  interface Props { variant?: 'text' | 'card' | 'block' | 'circle'; lines?: number }
  let { variant = 'text', lines = 3 }: Props = $props();
</script>

{#if variant === 'text'}
  <div class="skeleton text" aria-hidden="true">{#each Array(lines) as _, i (i)}<span class="line" class:last={i === lines - 1}></span>{/each}</div>
{:else}
  <div class="skeleton {variant}" aria-hidden="true"></div>
{/if}

<style>
  .skeleton { --sk: var(--color-surface); }
  .line, .card, .block, .circle {
    display: block; background: linear-gradient(90deg, var(--sk) 0%, var(--color-rule) 50%, var(--sk) 100%);
    background-size: 200% 100%; animation: shimmer 1.4s linear infinite; border-radius: var(--radius-control);
  }
  .text { display: grid; gap: var(--space-2); }
  .line { height: 0.9em; }
  .line.last { width: 60%; }
  .card { height: 160px; border-radius: var(--radius-card); }
  .block { height: 320px; }
  .circle { width: 48px; height: 48px; border-radius: 50%; }
  @keyframes shimmer { to { background-position: -200% 0; } }
</style>
