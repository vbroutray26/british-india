<script lang="ts">
  import Button from './Button.svelte';
  // FR-PLACE-13: share, cite, correct and listen in a consistent bar.
  interface Props {
    label: string;
    labels: { share: string; cite: string; correct: string; listen: string };
    onshare?: () => void; oncite?: () => void; oncorrect?: () => void; onlisten?: () => void;
    compact?: boolean;
  }
  let { label, labels, onshare, oncite, oncorrect, onlisten, compact = false }: Props = $props();
</script>

<div class="bar" role="toolbar" aria-label={label}>
  {#if onshare}<Button icon="share" text={compact ? undefined : labels.share} label={labels.share} onclick={onshare} />{/if}
  {#if oncite}<Button icon="cite" text={compact ? undefined : labels.cite} label={labels.cite} onclick={oncite} />{/if}
  {#if onlisten}<Button icon="volume" text={compact ? undefined : labels.listen} label={labels.listen} onclick={onlisten} />{/if}
  {#if oncorrect}<Button icon="flag" variant="ghost" text={compact ? undefined : labels.correct} label={labels.correct} onclick={oncorrect} />{/if}
</div>

<style>
  .bar { display: flex; flex-wrap: wrap; gap: var(--space-2); }
</style>
