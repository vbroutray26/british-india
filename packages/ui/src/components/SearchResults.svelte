<script lang="ts">
  // FR-SRCH-04 / AC-SRCH-04: passage search results, each with its page, source and highlighted match.
  // Excerpts come from the search index with <mark> around matches; everything else in them is escaped.
  export interface SearchResult { title: string; href: string; excerpt: string; page?: string; source?: string }
  interface Props {
    label: string;
    query: string;
    results: SearchResult[];
    state: 'idle' | 'loading' | 'done';
    labels: { page: string; noResults: string; count: (n: number) => string; searching: string };
  }
  let { label, query, results, state, labels }: Props = $props();
  const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  const safe = (s: string) => esc(s).replace(/&lt;mark&gt;/g, '<mark>').replace(/&lt;\/mark&gt;/g, '</mark>');
  const status = $derived(state === 'loading' ? labels.searching : state === 'done' ? (results.length ? labels.count(results.length) : labels.noResults) : '');
</script>

<section class="results" aria-label={label}>
  <p class="status" role="status">{query && status}</p>
  {#if results.length}
    <ol>
      {#each results as r (r.href)}
        <li>
          <a href={r.href} class="title">{r.title}</a>
          <!-- eslint-disable-next-line svelte/no-at-html-tags -- escaped above; only <mark> survives -->
          <p class="excerpt" lang="en">{@html safe(r.excerpt)}</p>
          <p class="meta">
            {#if r.source}<span>{r.source}</span>{/if}
            {#if r.page}<span>{labels.page} {r.page}</span>{/if}
          </p>
        </li>
      {/each}
    </ol>
  {/if}
</section>

<style>
  .results { display: grid; gap: var(--space-3); }
  .status { margin: 0; color: var(--color-text-muted); font-size: var(--step--1); min-height: 1.4em; }
  ol { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-6); }
  li { padding-bottom: var(--space-4); border-bottom: 1px solid var(--color-rule); }
  .title { font: 600 var(--step-1) / 1.3 var(--font-sans); }
  .excerpt { margin: var(--space-1) 0; font-family: var(--font-serif); line-height: 1.6; }
  .excerpt :global(mark) { background: var(--color-highlight); color: inherit; padding: 0 0.1em; border-radius: 2px; }
  .meta { margin: 0; display: flex; flex-wrap: wrap; gap: var(--space-1) var(--space-4); font-size: var(--step--1); color: var(--color-text-muted); }
</style>
