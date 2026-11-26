<script lang="ts">
  import type { Snippet } from 'svelte';
  import Icon from './Icon.svelte';
  import type { IconName } from './icons';
  // FR-CRIT-02/03/04: critical notes, content notes and "silences" are visually distinct from source text.
  interface Props {
    kind?: 'critical' | 'content-note' | 'silence' | 'info' | 'warning';
    title?: string;
    body?: string;
    /** Author, date, sources line (AC-CRIT-02). */
    meta?: string;
    link?: { href: string; text: string };
    children?: Snippet;
  }
  let { kind = 'info', title, body, meta, link, children }: Props = $props();
  const ICON: Record<string, IconName> = { critical: 'cite', 'content-note': 'warning', silence: 'ghost', info: 'info', warning: 'warning' };
</script>

<aside class="callout {kind}" aria-label={title}>
  <div class="icon"><Icon name={ICON[kind]} /></div>
  <div class="content">
    {#if title}<p class="title">{title}</p>{/if}
    {#if body}<p class="body">{body}</p>{/if}
    {@render children?.()}
    {#if meta}<p class="meta">{meta}</p>{/if}
    {#if link}<p class="link"><a href={link.href}>{link.text}</a></p>{/if}
  </div>
</aside>

<style>
  .callout {
    display: grid; grid-template-columns: auto 1fr; gap: var(--space-3);
    padding: var(--space-4); border-radius: var(--radius-card);
    background: var(--color-surface); border-left: 4px solid var(--color-text-muted);
  }
  .callout p { margin: 0; }
  .content > * + * { margin-top: var(--space-2); }
  .title { font-weight: 600; }
  .meta { font-size: var(--step--1); color: var(--color-text-muted); }
  .icon { color: var(--color-text-muted); padding-top: 2px; }
  .critical { border-left-color: var(--color-ai); }
  .critical .icon { color: var(--color-ai); }
  .content-note { border-left-color: var(--color-warning); }
  .content-note .icon { color: var(--color-warning); }
  .warning { border-left-color: var(--color-warning); }
  .silence {
    background: transparent; border: 1.5px dashed var(--color-rule); border-left: 4px dashed var(--color-text-muted);
    color: var(--color-text-muted);
  }
  .silence .body { font-style: italic; }
  :global(:lang(or)) .silence .body, :global(:lang(hi)) .silence .body { font-style: normal; }
</style>
