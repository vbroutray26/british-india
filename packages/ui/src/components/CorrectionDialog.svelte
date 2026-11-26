<script lang="ts">
  import Dialog from './Dialog.svelte';
  import Button from './Button.svelte';
  // FR-CORR-01..07, AC-CORR-01/02: prefilled with the item ID; no account; honeypot; acknowledgement promise.
  interface Props {
    open?: boolean;
    itemId: string;
    itemLabel?: string;
    contactEmail: string;
    onsubmit: (data: Record<string, string>) => Promise<{ ok: boolean }>;
    labels: {
      title: string; intro: string; close: string; item: string; whatWrong: string; suggestedFix: string;
      source: string; email: string; emailHint: string; optional: string; submit: string; sending: string;
      thanks: string; error: string; orEmail: string; cancel: string;
    };
  }
  let { open = $bindable(false), itemId, itemLabel, contactEmail, onsubmit, labels }: Props = $props();
  const id = $props.id();
  let state: 'form' | 'sending' | 'done' | 'error' = $state('form');

  async function submit(e: SubmitEvent) {
    e.preventDefault();
    const form = e.currentTarget as HTMLFormElement;
    const data = Object.fromEntries(new FormData(form)) as Record<string, string>;
    state = 'sending';
    try { state = (await onsubmit(data)).ok ? 'done' : 'error'; } catch { state = 'error'; }
  }
</script>

<Dialog bind:open title={labels.title} closeLabel={labels.close} description={state === 'done' ? undefined : labels.intro} onclose={() => (state = 'form')}>
  {#if state === 'done'}
    <p role="status" class="ok">{labels.thanks}</p>
  {:else}
    <form id="{id}-f" onsubmit={submit}>
      <input type="hidden" name="item_id" value={itemId} />
      <p class="item">{labels.item}: <code>{itemLabel ?? itemId}</code></p>
      <div class="field">
        <label for="{id}-w">{labels.whatWrong}</label>
        <textarea id="{id}-w" name="what_is_wrong" required maxlength="4000" rows="3"></textarea>
      </div>
      <div class="field">
        <label for="{id}-s">{labels.suggestedFix} <span class="opt">({labels.optional})</span></label>
        <textarea id="{id}-s" name="suggested_fix" maxlength="4000" rows="2"></textarea>
      </div>
      <div class="field">
        <label for="{id}-src">{labels.source} <span class="opt">({labels.optional})</span></label>
        <input id="{id}-src" name="source" maxlength="1000" />
      </div>
      <div class="field">
        <label for="{id}-e">{labels.email} <span class="opt">({labels.optional})</span></label>
        <input id="{id}-e" name="email" type="email" maxlength="254" autocomplete="email" aria-describedby="{id}-eh" />
        <p id="{id}-eh" class="hint">{labels.emailHint}</p>
      </div>
      <!-- Honeypot: humans never see or fill this (AC-CORR-03). -->
      <div class="hp" aria-hidden="true"><label>Website <input name="website" tabindex="-1" autocomplete="off" /></label></div>
      {#if state === 'error'}<p class="err" role="alert">{labels.error}</p>{/if}
      <p class="alt">{labels.orEmail} <a href="mailto:{contactEmail}?subject={encodeURIComponent(itemId)}">{contactEmail}</a></p>
    </form>
  {/if}
  {#snippet footer()}
    {#if state === 'done'}<Button variant="primary" text={labels.close} onclick={() => (open = false)} />
    {:else}
      <Button variant="ghost" text={labels.cancel} onclick={() => (open = false)} />
      <Button variant="primary" type="submit" form="{id}-f" text={state === 'sending' ? labels.sending : labels.submit} loading={state === 'sending'} loadingLabel={labels.sending} />
    {/if}
  {/snippet}
</Dialog>

<style>
  form { display: grid; gap: var(--space-4); }
  .item { margin: 0; font-size: var(--step--1); color: var(--color-text-muted); }
  .field { display: grid; gap: var(--space-1); }
  label { font-weight: 600; }
  .opt { font-weight: 400; color: var(--color-text-muted); }
  textarea, input:not([type='hidden']) {
    width: 100%; min-height: 44px; padding: var(--space-2) var(--space-3);
    background: var(--color-bg); border: 1.5px solid var(--color-text-muted); border-radius: var(--radius-control);
  }
  textarea:focus-visible, input:focus-visible { outline: 3px solid var(--color-focus); outline-offset: 1px; border-color: var(--color-text); }
  .hint { margin: 0; font-size: var(--step--1); color: var(--color-text-muted); }
  .hp { position: absolute; left: -9999px; width: 1px; height: 1px; overflow: hidden; }
  .err { margin: 0; color: var(--color-danger); font-weight: 600; }
  .ok { font-size: var(--step-1); }
  .alt { margin: 0; font-size: var(--step--1); color: var(--color-text-muted); }
</style>
