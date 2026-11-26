<script lang="ts">
  import Icon from './Icon.svelte';
  // FR-EDU-01/02: teacher note, source passages with questions, map, printable PDF, in three languages.
  interface Props {
    title: string; summary: string; href: string;
    contents: string[];
    downloads: { text: string; href: string; lang: string }[];
    labels: { includes: string; download: string };
  }
  let { title, summary, href, contents, downloads, labels }: Props = $props();
</script>

<article class="pack">
  <h3><a {href}>{title}</a></h3>
  <p>{summary}</p>
  <p class="lbl">{labels.includes}</p>
  <ul>{#each contents as c (c)}<li>{c}</li>{/each}</ul>
  <p class="lbl">{labels.download}</p>
  <ul class="dl">{#each downloads as d (d.href)}<li><a href={d.href} hreflang={d.lang} download><Icon name="download" size={18} /> {d.text}</a></li>{/each}</ul>
</article>

<style>
  .pack { padding: var(--space-6); border: 1px solid var(--color-rule); border-radius: var(--radius-card); background: var(--color-surface); box-shadow: var(--shadow-1); }
  h3 { margin: 0 0 var(--space-2); font-size: var(--step-2); }
  p { margin: 0 0 var(--space-3); }
  .lbl { font-size: var(--step--1); font-weight: 700; margin-bottom: var(--space-1); }
  ul { margin: 0 0 var(--space-4); padding-left: var(--space-6); }
  .dl { list-style: none; padding: 0; display: flex; flex-wrap: wrap; gap: var(--space-2); }
  .dl a { display: inline-flex; align-items: center; gap: var(--space-1); min-height: 44px; padding: 0 var(--space-3); border: 1px solid var(--color-rule); border-radius: var(--radius-control); text-decoration: none; }
</style>
