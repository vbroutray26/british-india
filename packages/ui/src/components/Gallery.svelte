<script lang="ts">
  import Lightbox from './Lightbox.svelte';
  import type { GalleryItem } from './types';
  // FR-PLACE-08 / FR-MEDIA-01: per-place gallery; every thumbnail carries its credit (FR-MEDIA-04).
  interface Props {
    label: string;
    items: GalleryItem[];
    labels: { open: string; close: string; prev: string; next: string; source: string; counter: (i: number, n: number) => string };
  }
  let { label, items, labels }: Props = $props();
  let open = $state(false);
  let index = $state(0);
</script>

<section aria-label={label}>
  <ul class="grid">
    {#each items as it, i (it.id)}
      <li>
        <button type="button" onclick={() => { index = i; open = true; }} aria-label="{labels.open}: {it.alt}">
          <img src={it.thumb} alt="" width="320" height="240" loading="lazy" decoding="async" />
        </button>
        <p class="credit">{it.credit}</p>
      </li>
    {/each}
  </ul>
</section>
<Lightbox bind:open bind:index {items} {labels} />

<style>
  .grid { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: var(--space-4); }
  button { display: block; width: 100%; padding: 0; border: 0; background: var(--color-surface); cursor: zoom-in; border-radius: var(--radius-control); overflow: hidden; }
  button:focus-visible { outline: 3px solid var(--color-focus); outline-offset: 2px; }
  img { display: block; width: 100%; aspect-ratio: 4 / 3; object-fit: cover; transition: transform var(--dur-md) var(--ease-out); }
  button:hover img { transform: scale(1.03); }
  .credit { margin: var(--space-1) 0 0; font-size: var(--step--1); color: var(--color-text-muted); }
</style>
