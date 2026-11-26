<script lang="ts">
  import type { Snippet } from 'svelte';
  import Button from './Button.svelte';
  // Native modal <dialog>: focus trap, Escape and inert background come from the browser (NFR-A11Y-02).
  interface Props {
    open?: boolean;
    title: string;
    closeLabel: string;
    description?: string;
    size?: 'sm' | 'md' | 'lg';
    children?: Snippet;
    footer?: Snippet;
    onclose?: () => void;
  }
  let { open = $bindable(false), title, closeLabel, description, size = 'md', children, footer, onclose }: Props = $props();
  const id = $props.id();
  let el: HTMLDialogElement | undefined = $state();
  let returnTo: Element | null = null;

  $effect(() => {
    if (!el) return;
    if (open && !el.open) { returnTo = document.activeElement; el.showModal?.(); }
    if (!open && el.open) el.close();
  });
  function handleClose() {
    open = false;
    onclose?.();
    (returnTo as HTMLElement | null)?.focus?.();
  }
</script>

<dialog bind:this={el} class={size} aria-labelledby="{id}-t" aria-describedby={description ? `${id}-d` : undefined} onclose={handleClose}
  onclick={(e) => e.target === el && el?.close()}>
  <div class="inner">
    <header>
      <h2 id="{id}-t">{title}</h2>
      <Button variant="ghost" icon="close" label={closeLabel} onclick={() => el?.close()} />
    </header>
    {#if description}<p id="{id}-d" class="desc">{description}</p>{/if}
    <div class="body">{@render children?.()}</div>
    {#if footer}<footer>{@render footer()}</footer>{/if}
  </div>
</dialog>

<style>
  dialog {
    width: min(100% - 2 * var(--space-4), 560px); max-height: min(90vh, 900px); padding: 0;
    border: 1px solid var(--color-rule); border-radius: var(--radius-card);
    background: var(--color-bg); color: var(--color-text); box-shadow: var(--shadow-3);
  }
  dialog.sm { width: min(100% - 2 * var(--space-4), 400px); }
  dialog.lg { width: min(100% - 2 * var(--space-4), 880px); }
  dialog::backdrop { background: rgb(0 0 0 / 0.45); }
  dialog[open] { animation: rise var(--dur-md) var(--ease-out); }
  @keyframes rise { from { opacity: 0; transform: translateY(12px); } }
  .inner { padding: var(--space-6); }
  header { display: flex; justify-content: space-between; align-items: start; gap: var(--space-4); }
  h2 { font-size: var(--step-2); margin: 0; padding-top: var(--space-2); }
  .desc { color: var(--color-text-muted); margin-top: var(--space-2); }
  .body { margin-top: var(--space-4); }
  footer { display: flex; justify-content: flex-end; flex-wrap: wrap; gap: var(--space-2); margin-top: var(--space-6); }
</style>
