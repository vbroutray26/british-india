<script lang="ts">
  import Icon from './Icon.svelte';
  import Button from './Button.svelte';
  // Polite live region; toasts never carry the only copy of important information.
  import type { ToastItem } from './types';
  interface Props { toasts: ToastItem[]; dismissLabel: string; ondismiss?: (id: string) => void }
  let { toasts, dismissLabel, ondismiss }: Props = $props();
</script>

<div class="region" role="status" aria-live="polite">
  {#each toasts as t (t.id)}
    <div class="toast {t.tone ?? 'info'}">
      <Icon name={t.tone === 'success' ? 'check' : t.tone === 'danger' ? 'error' : 'info'} />
      <span>{t.text}</span>
      <Button variant="ghost" size="sm" icon="close" label={dismissLabel} onclick={() => ondismiss?.(t.id)} />
    </div>
  {/each}
</div>

<style>
  .region { position: fixed; inset: auto var(--space-4) var(--space-4) auto; z-index: var(--z-toast); display: grid; gap: var(--space-2); max-width: min(420px, calc(100% - 2 * var(--space-4))); }
  .toast {
    display: flex; align-items: center; gap: var(--space-3); padding: var(--space-2) var(--space-2) var(--space-2) var(--space-4);
    background: var(--color-text); color: var(--color-bg); border-radius: var(--radius-card); box-shadow: var(--shadow-2);
    animation: in var(--dur-md) var(--ease-out);
  }
  .toast span { flex: 1; }
  .toast :global(.btn) { color: inherit; }
  @keyframes in { from { opacity: 0; transform: translateY(8px); } }
</style>
