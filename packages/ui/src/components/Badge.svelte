<script lang="ts">
  import Icon from './Icon.svelte';
  import type { IconName } from './icons';
  interface Props {
    text: string;
    tone?: 'neutral' | 'ai' | 'reviewed' | 'pending' | 'danger' | 'warning' | 'success';
    icon?: IconName;
    /** Extra detail exposed on hover and to assistive tech, e.g. "Reviewed by owner, 20 Dec 2026". */
    detail?: string;
  }
  let { text, tone = 'neutral', icon, detail }: Props = $props();
</script>

<span class="badge {tone}" title={detail}>
  {#if icon}<Icon name={icon} size={16} />{/if}
  <span>{text}</span>
  {#if detail}<span class="visually-hidden">: {detail}</span>{/if}
</span>

<style>
  .badge {
    display: inline-flex; align-items: center; gap: var(--space-1); padding: 2px var(--space-2);
    font: 600 var(--step--1) / 1.4 var(--font-sans); border: 1px solid currentColor;
    border-radius: var(--radius-control); color: var(--color-text-muted); white-space: nowrap;
  }
  .ai { color: var(--color-ai); border-style: dashed; }
  .reviewed, .success { color: var(--color-review-ok); }
  .pending { color: var(--color-review-pending); border-style: dotted; }
  .danger { color: var(--color-danger); }
  .warning { color: var(--color-warning); }
</style>
