<script lang="ts">
  import Icon from './Icon.svelte';
  // FR-LANG-07, AC-LANG-04: pre-generated narration with a transcript; never autoplays. Native controls for accessibility.
  interface Props { src: string; title: string; lang: string; transcript: string; duration?: string; labels: { transcript: string; aiVoice?: string } }
  let { src, title, lang, transcript, duration, labels }: Props = $props();
</script>

<section class="audio" aria-label={title}>
  <p class="head"><Icon name="volume" size={20} /><span>{title}</span>{#if duration}<span class="dur">{duration}</span>{/if}</p>
  <audio controls preload="none" {src} {lang}></audio>
  {#if labels.aiVoice}<p class="ai">{labels.aiVoice}</p>{/if}
  <details>
    <summary>{labels.transcript}</summary>
    <p {lang}>{transcript}</p>
  </details>
</section>

<style>
  .audio { display: grid; gap: var(--space-2); padding: var(--space-4); border: 1px solid var(--color-rule); border-radius: var(--radius-card); background: var(--color-surface); }
  .head { display: flex; align-items: center; gap: var(--space-2); margin: 0; font-weight: 600; }
  .dur { margin-left: auto; font-weight: 400; color: var(--color-text-muted); font-variant-numeric: tabular-nums; }
  audio { width: 100%; }
  .ai { margin: 0; font-size: var(--step--1); color: var(--color-ai); }
  summary { cursor: pointer; min-height: 44px; display: flex; align-items: center; font-weight: 600; }
  details p { margin: 0; }
</style>
