<script lang="ts">
  import Dialog from './Dialog.svelte';
  import Button from './Button.svelte';
  import type { GalleryItem } from './types';
  // FR-MEDIA-08: keyboard (← →) and swipe; caption and credit always shown.
  interface Props {
    open?: boolean;
    items: GalleryItem[];
    index?: number;
    labels: { close: string; prev: string; next: string; source: string; counter: (i: number, n: number) => string };
  }
  let { open = $bindable(false), items, index = $bindable(0), labels }: Props = $props();
  const item = $derived(items[index]);
  let startX: number | null = null;
  const go = (d: number) => (index = (index + d + items.length) % items.length);
  function onkeydown(e: KeyboardEvent) {
    if (e.key === 'ArrowRight') { e.preventDefault(); go(1); }
    if (e.key === 'ArrowLeft') { e.preventDefault(); go(-1); }
  }
</script>

<Dialog bind:open title={item?.caption ?? labels.counter(index + 1, items.length)} closeLabel={labels.close} size="lg">
  {#if item}
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div class="stage" {onkeydown}
      onpointerdown={(e) => (startX = e.clientX)}
      onpointerup={(e) => { if (startX !== null && Math.abs(e.clientX - startX) > 40) go(e.clientX < startX ? 1 : -1); startX = null; }}>
      <img src={item.full} alt={item.alt} width={item.width} height={item.height} />
    </div>
    <p class="credit">{#if item.date}{item.date} · {/if}{item.credit} · <a href={item.sourceHref} rel="noopener">{labels.source}</a></p>
  {/if}
  {#snippet footer()}
    <span class="count" aria-live="polite">{labels.counter(index + 1, items.length)}</span>
    <Button icon="chevron-left" label={labels.prev} onclick={() => go(-1)} />
    <Button icon="chevron-right" label={labels.next} onclick={() => go(1)} />
  {/snippet}
</Dialog>
<svelte:window onkeydown={(e) => open && onkeydown(e)} />

<style>
  .stage { display: grid; place-items: center; background: var(--color-surface); border-radius: var(--radius-control); touch-action: pan-y; }
  img { max-width: 100%; max-height: 65vh; width: auto; height: auto; object-fit: contain; }
  .credit { margin: var(--space-3) 0 0; font-size: var(--step--1); color: var(--color-text-muted); }
  .count { margin-right: auto; align-self: center; font-size: var(--step--1); color: var(--color-text-muted); }
</style>
