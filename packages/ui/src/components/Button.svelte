<script lang="ts">
  import type { Snippet } from 'svelte';
  import type { HTMLButtonAttributes } from 'svelte/elements';
  import Icon from './Icon.svelte';
  import type { IconName } from './icons';

  interface Props extends Omit<HTMLButtonAttributes, 'children'> {
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
    size?: 'md' | 'sm';
    /** Renders a link styled as a button. */
    href?: string;
    icon?: IconName;
    iconEnd?: IconName;
    /** Visible text. Use `label` for icon-only buttons (becomes aria-label). */
    text?: string;
    label?: string;
    loading?: boolean;
    /** Announced while loading, e.g. "Loading" in the current language. */
    loadingLabel?: string;
    pressed?: boolean;
    children?: Snippet;
  }
  let {
    variant = 'secondary', size = 'md', href, icon, iconEnd, text, label, loading = false,
    loadingLabel, pressed, disabled, children, type = 'button', ...rest
  }: Props = $props();
  const iconOnly = $derived(!text && !children);
</script>

{#if href && !disabled}
  <a class="btn {variant} {size}" class:icon-only={iconOnly} {href} aria-label={iconOnly ? label : undefined}>
    {#if icon}<Icon name={icon} size={size === 'sm' ? 18 : 20} />{/if}
    {#if text}<span>{text}</span>{/if}{@render children?.()}
    {#if iconEnd}<Icon name={iconEnd} size={size === 'sm' ? 18 : 20} />{/if}
  </a>
{:else}
  <button
    class="btn {variant} {size}"
    class:icon-only={iconOnly}
    {type}
    disabled={disabled || loading}
    aria-busy={loading || undefined}
    aria-pressed={pressed}
    aria-label={iconOnly ? label : undefined}
    {...rest}
  >
    {#if loading}<span class="spinner" aria-hidden="true"></span>{#if loadingLabel}<span class="visually-hidden">{loadingLabel}</span>{/if}
    {:else if icon}<Icon name={icon} size={size === 'sm' ? 18 : 20} />{/if}
    {#if text}<span>{text}</span>{/if}{@render children?.()}
    {#if iconEnd}<Icon name={iconEnd} size={size === 'sm' ? 18 : 20} />{/if}
  </button>
{/if}

<style>
  .btn {
    display: inline-flex; align-items: center; justify-content: center; gap: var(--space-2);
    min-height: 44px; min-width: 44px; padding: 0 var(--space-4);
    font: 600 var(--step--1) / 1.2 var(--font-sans); text-decoration: none; cursor: pointer;
    border: 1.5px solid var(--color-text); border-radius: var(--radius-control);
    background: transparent; color: var(--color-text);
    transition: background-color var(--dur-xs) var(--ease-out), box-shadow var(--dur-xs) var(--ease-out), transform var(--dur-xs) var(--ease-out);
  }
  .btn.sm { min-height: 36px; padding: 0 var(--space-3); }
  .btn.icon-only { padding: 0; width: 44px; }
  .btn.sm.icon-only { width: 36px; }
  .primary { background: var(--color-accent); border-color: var(--color-accent); color: var(--color-on-accent); }
  .secondary:hover:not(:disabled), .ghost:hover:not(:disabled) { background: var(--color-surface); }
  .primary:hover:not(:disabled), .danger:hover:not(:disabled) { box-shadow: var(--shadow-2); }
  .btn:active:not(:disabled) { transform: translateY(1px); }
  .ghost { border-color: transparent; }
  .danger { border-color: var(--color-danger); color: var(--color-danger); }
  .btn[aria-pressed='true'] { background: var(--color-text); color: var(--color-bg); }
  .btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .spinner {
    width: 1em; height: 1em; border-radius: 50%;
    border: 2px solid currentColor; border-right-color: transparent;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  @media (forced-colors: active) { .btn { border-color: ButtonText; } }
</style>
