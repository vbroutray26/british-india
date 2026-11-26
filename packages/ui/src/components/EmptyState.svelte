<script lang="ts">
  import Icon from './Icon.svelte';
  import Button from './Button.svelte';
  import type { IconName } from './icons';
  // AC-PLACE-05: missing data says so plainly ("not recorded in these sources"); never blank or zero.
  interface Props { title: string; body?: string; icon?: IconName; action?: { text: string; href: string }; tone?: 'empty' | 'error' }
  let { title, body, icon = 'source', action, tone = 'empty' }: Props = $props();
</script>

<div class="state {tone}" role={tone === 'error' ? 'alert' : undefined}>
  <span class="mark"><Icon name={icon} size={32} /></span>
  <p class="title">{title}</p>
  {#if body}<p class="body">{body}</p>{/if}
  {#if action}<Button href={action.href} text={action.text} variant={tone === 'error' ? 'primary' : 'secondary'} />{/if}
</div>

<style>
  .state { display: grid; justify-items: center; text-align: center; gap: var(--space-2); padding: var(--space-8) var(--space-4); border: 1.5px dashed var(--color-rule); border-radius: var(--radius-card); }
  .state p { margin: 0; max-width: 46ch; }
  .mark { display: grid; place-items: center; width: 64px; height: 64px; border-radius: 50%; background: var(--color-surface); color: var(--color-text-muted); }
  .title { font-weight: 600; font-size: var(--step-1); }
  .body { color: var(--color-text-muted); }
  .error { border-color: var(--color-danger); }
  .error .mark { color: var(--color-danger); }
  .state :global(.btn) { margin-top: var(--space-2); }
</style>
