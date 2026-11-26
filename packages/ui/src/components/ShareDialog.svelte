<script lang="ts">
  import Dialog from './Dialog.svelte';
  import Button from './Button.svelte';
  // FR-SHARE-04/05: Web Share where available, copy-link fallback, WhatsApp, and the share-card preview.
  interface Props {
    open?: boolean;
    url: string;
    title: string;
    text?: string;
    image?: { src: string; alt: string };
    labels: { title: string; close: string; copy: string; copied: string; whatsapp: string; more: string; link: string };
  }
  let { open = $bindable(false), url, title, text = '', image, labels }: Props = $props();
  const id = $props.id();
  let copied = $state(false);
  const canShare = typeof navigator !== 'undefined' && 'share' in navigator;
  async function copy() { await navigator.clipboard?.writeText(url); copied = true; setTimeout(() => (copied = false), 2500); }
  const wa = $derived(`https://wa.me/?text=${encodeURIComponent(`${title} — ${url}`)}`);
</script>

<Dialog bind:open title={labels.title} closeLabel={labels.close}>
  {#if image}<img class="card" src={image.src} alt={image.alt} width="1200" height="630" />{/if}
  <label for="{id}-u" class="lbl">{labels.link}</label>
  <div class="row">
    <input id="{id}-u" readonly value={url} onfocus={(e) => (e.currentTarget as HTMLInputElement).select()} />
    <Button variant="primary" icon={copied ? 'check' : 'copy'} text={copied ? labels.copied : labels.copy} onclick={copy} />
  </div>
  <span class="visually-hidden" role="status">{copied ? labels.copied : ''}</span>
  <div class="row">
    <Button href={wa} icon="share" text={labels.whatsapp} />
    {#if canShare}<Button icon="external" text={labels.more} onclick={() => navigator.share({ title, text, url })} />{/if}
  </div>
</Dialog>

<style>
  .card { width: 100%; height: auto; border: 1px solid var(--color-rule); border-radius: var(--radius-control); margin-bottom: var(--space-4); }
  .lbl { display: block; font-weight: 600; margin-bottom: var(--space-1); }
  .row { display: flex; gap: var(--space-2); flex-wrap: wrap; margin-bottom: var(--space-3); }
  input { flex: 1 1 220px; min-height: 44px; padding: 0 var(--space-3); font-family: var(--font-mono); font-size: var(--step--1); background: var(--color-surface); border: 1px solid var(--color-rule); border-radius: var(--radius-control); }
</style>
