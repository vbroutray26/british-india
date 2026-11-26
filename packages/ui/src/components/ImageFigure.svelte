<script lang="ts">
  // FR-MEDIA-03/04/10, §11.6: responsive image with caption, date, credit and Source link always visible.
  // Evidence images are never recoloured; the "then" duotone is for decorative use only.
  interface Props {
    src: string;
    srcset?: string;
    sizes?: string;
    width: number;
    height: number;
    alt: string;
    caption?: string;
    date?: string;
    credit: string;
    sourceHref: string;
    sourceLabel: string;
    use?: 'evidence' | 'decorative';
    priority?: boolean;
  }
  let { src, srcset, sizes, width, height, alt, caption, date, credit, sourceHref, sourceLabel, use = 'evidence', priority = false }: Props = $props();
</script>

<figure class="fig {use}">
  <img {src} {srcset} {sizes} {width} {height} {alt} loading={priority ? 'eager' : 'lazy'} decoding="async" fetchpriority={priority ? 'high' : undefined} />
  <figcaption>
    {#if caption}<span class="cap">{caption}{#if date} ({date}){/if}</span>{/if}
    <span class="credit">{credit} · <a href={sourceHref} rel="noopener">{sourceLabel}</a></span>
  </figcaption>
</figure>

<style>
  .fig { margin: 0; }
  img { display: block; width: 100%; height: auto; background: var(--color-surface); }
  .decorative img { filter: grayscale(1) sepia(0.35) contrast(1.05); mix-blend-mode: multiply; }
  figcaption { display: grid; gap: var(--space-1); margin-top: var(--space-2); font-size: var(--step--1); }
  .credit { color: var(--color-text-muted); }
</style>
