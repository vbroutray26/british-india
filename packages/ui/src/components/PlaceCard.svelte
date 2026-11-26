<script lang="ts">
  import Icon from './Icon.svelte';
  // FR-SRCH-03: place type, district then and now, thumbnail. Ghost places are marked (FR-PLACE-15).
  interface Props {
    name: string;
    otherNames?: string;
    type: string;
    districtThen?: string;
    districtNow?: string;
    href: string;
    thumb?: { src: string; alt: string };
    ghost?: string;
    labels: { then: string; now: string };
  }
  let { name, otherNames, type, districtThen, districtNow, href, thumb, ghost, labels }: Props = $props();
</script>

<article class="card" class:ghost={!!ghost}>
  {#if thumb}<img src={thumb.src} alt={thumb.alt} width="96" height="96" loading="lazy" />{:else}<span class="ph" aria-hidden="true"><Icon name={ghost ? 'ghost' : 'map'} size={32} /></span>{/if}
  <div class="body">
    <h3><a {href}>{name}</a></h3>
    {#if otherNames}<p class="alt">{otherNames}</p>{/if}
    <p class="meta"><span class="type">{type}</span>{#if ghost}<span class="gh">{ghost}</span>{/if}</p>
    {#if districtThen || districtNow}
      <dl>
        {#if districtThen}<div><dt>{labels.then}</dt><dd>{districtThen}</dd></div>{/if}
        {#if districtNow}<div><dt>{labels.now}</dt><dd>{districtNow}</dd></div>{/if}
      </dl>
    {/if}
  </div>
</article>

<style>
  .card {
    position: relative; display: grid; grid-template-columns: 96px 1fr; gap: var(--space-4); padding: var(--space-3);
    border: 1px solid var(--color-rule); border-radius: var(--radius-card); background: var(--color-surface);
    transition: box-shadow var(--dur-sm) var(--ease-out), transform var(--dur-sm) var(--ease-out);
  }
  .card:hover { box-shadow: var(--shadow-2); transform: translateY(-1px); }
  .card:has(a:focus-visible) { outline: 3px solid var(--color-focus); outline-offset: 2px; }
  img, .ph { width: 96px; height: 96px; object-fit: cover; border-radius: var(--radius-control); }
  .ph { display: grid; place-items: center; background: var(--color-bg); color: var(--color-text-muted); }
  h3 { margin: 0; font-size: var(--step-1); }
  h3 a { color: var(--color-text); text-decoration: none; }
  h3 a::after { content: ''; position: absolute; inset: 0; } /* whole card is the link target */
  h3 a:focus-visible { outline: none; }
  p { margin: 0; }
  .alt { color: var(--color-text-muted); font-size: var(--step--1); }
  .meta { display: flex; gap: var(--space-2); flex-wrap: wrap; margin-top: var(--space-1); font-size: var(--step--1); }
  .type { font-weight: 600; }
  .gh { color: var(--color-warning); font-weight: 600; }
  .ghost { border-style: dashed; background: transparent; }
  dl { margin: var(--space-2) 0 0; display: flex; flex-wrap: wrap; gap: var(--space-1) var(--space-4); font-size: var(--step--1); }
  dl div { display: flex; gap: var(--space-1); }
  dt { color: var(--color-text-muted); }
  dd { margin: 0; }
</style>
