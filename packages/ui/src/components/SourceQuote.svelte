<script lang="ts">
  import Button from './Button.svelte';
  // FR-TEXT-01/05, AC-PLACE-02: the passage with the exact quote highlighted, its source, and citation tools.
  interface Props {
    text: string;
    /** Character offsets of the supporting quote inside `text`. */
    highlight?: { start: number; end: number };
    source: string;
    edition?: string;
    page: string;
    permalink?: string;
    scanHref?: string;
    citation?: string;
    lang?: string;
    labels: { page: string; copyCitation: string; copied: string; permalink: string; viewScan: string };
  }
  let { text, highlight, source, edition, page, permalink, scanHref, citation, lang = 'en', labels }: Props = $props();
  let copied = $state(false);
  const parts = $derived(
    highlight && highlight.end > highlight.start
      ? [text.slice(0, highlight.start), text.slice(highlight.start, highlight.end), text.slice(highlight.end)]
      : [text, '', ''],
  );
  async function copy() {
    if (!citation) return;
    await navigator.clipboard?.writeText(citation);
    copied = true;
    setTimeout(() => (copied = false), 2500);
  }
</script>

<figure class="quote">
  <blockquote {lang}>
    <p>{parts[0]}{#if parts[1]}<mark>{parts[1]}</mark>{/if}{parts[2]}</p>
  </blockquote>
  <figcaption>
    <span class="src"><cite>{source}</cite>{#if edition} ({edition}){/if}, {labels.page} {page}</span>
    <span class="actions">
      {#if citation}<Button size="sm" variant="ghost" icon={copied ? 'check' : 'copy'} text={copied ? labels.copied : labels.copyCitation} onclick={copy} />{/if}
      {#if permalink}<Button size="sm" variant="ghost" icon="external" text={labels.permalink} href={permalink} />{/if}
      {#if scanHref}<Button size="sm" variant="ghost" icon="scan" text={labels.viewScan} href={scanHref} />{/if}
    </span>
    <span class="visually-hidden" role="status">{copied ? labels.copied : ''}</span>
  </figcaption>
</figure>

<style>
  .quote { margin: 0; }
  blockquote {
    margin: 0; padding: var(--space-2) 0 var(--space-2) var(--space-4); border-left: 3px solid var(--color-logo-accent);
    font-family: var(--font-serif); font-size: var(--step-0); line-height: 1.7;
  }
  blockquote p { margin: 0; }
  mark { background: var(--color-highlight); color: inherit; padding: 0 2px; border-radius: 2px; box-decoration-break: clone; -webkit-box-decoration-break: clone; }
  figcaption { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: var(--space-2); margin-top: var(--space-3); font-size: var(--step--1); color: var(--color-text-muted); }
  cite { font-style: italic; color: var(--color-text); }
  .actions { display: flex; flex-wrap: wrap; gap: var(--space-1); }
</style>
