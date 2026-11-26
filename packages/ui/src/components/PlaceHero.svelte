<script lang="ts">
  import type { Snippet } from 'svelte';
  import Breadcrumb from './Breadcrumb.svelte';
  import Callout from './Callout.svelte';
  // FR-PLACE-01/02/15 and the §11.5 wireframe header.
  interface Props {
    name: string;
    names?: { text: string; lang: string }[];
    oldSpellings?: string[];
    type: string;
    districtThen?: string;
    districtNow?: string;
    coords?: string;
    tagline?: string;
    breadcrumb?: { label: string; items: { text: string; href?: string }[] };
    ghost?: { title: string; body: string };
    labels: { oldSpellings: string; then: string; now: string };
    actions?: Snippet;
  }
  let { name, names = [], oldSpellings = [], type, districtThen, districtNow, coords, tagline, breadcrumb, ghost, labels, actions }: Props = $props();
</script>

<section class="hero">
  {#if breadcrumb}<Breadcrumb {...breadcrumb} />{/if}
  {#if ghost}<Callout kind="warning" title={ghost.title} body={ghost.body} />{/if}
  <h1>{name}</h1>
  {#if names.length}<p class="names">{#each names as n, i (n.lang)}<span lang={n.lang}>{n.text}</span>{#if i < names.length - 1}<span aria-hidden="true"> · </span>{/if}{/each}</p>{/if}
  <p class="facts">
    <span class="type">{type}</span>
    {#if districtThen}<span>{labels.then}: {districtThen}</span>{/if}
    {#if districtNow}<span>{labels.now}: {districtNow}</span>{/if}
    {#if coords}<span class="coords">{coords}</span>{/if}
  </p>
  {#if oldSpellings.length}<p class="old">{labels.oldSpellings}: {#each oldSpellings as s, i (s)}<i>{s}</i>{i < oldSpellings.length - 1 ? ', ' : ''}{/each}</p>{/if}
  {#if tagline}<p class="tagline">{tagline}</p>{/if}
  {#if actions}<div class="actions">{@render actions()}</div>{/if}
</section>

<style>
  .hero { display: grid; gap: var(--space-3); padding-block: var(--space-8) var(--space-6); }
  h1 { font-size: var(--step-6); margin: 0; line-height: 1; }
  p { margin: 0; }
  .names { font-size: var(--step-2); font-family: var(--font-display); color: var(--color-text-muted); }
  .facts { display: flex; flex-wrap: wrap; gap: var(--space-1) var(--space-4); font-size: var(--step--1); }
  .type { font-weight: 700; text-transform: capitalize; }
  .coords { font-family: var(--font-mono); color: var(--color-text-muted); }
  .old { font-size: var(--step--1); color: var(--color-text-muted); }
  .tagline { font-family: var(--font-serif); font-size: var(--step-1); max-width: 40ch; }
  .actions { margin-top: var(--space-2); }
</style>
