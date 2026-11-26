<script lang="ts">
  // FR-TEXT-04, AC-TEXT-02: tap or hover an archaic word for its definition in the current language.
  // A disclosure button (not hover-only) so it works on touch and keyboard.
  interface Props { term: string; definition: string; moreHref?: string; moreLabel?: string }
  let { term, definition, moreHref, moreLabel }: Props = $props();
  const id = $props.id();
  let open = $state(false);
  let root: HTMLElement | undefined = $state();
  $effect(() => {
    if (!open) return;
    const close = (e: Event) => { if (!root?.contains(e.target as Node)) open = false; };
    document.addEventListener('pointerdown', close);
    return () => document.removeEventListener('pointerdown', close);
  });
</script>

<span class="term" bind:this={root}>
  <button type="button" aria-expanded={open} aria-controls={id} onclick={() => (open = !open)} onkeydown={(e) => e.key === 'Escape' && (open = false)}>{term}</button>
  <span {id} class="pop" role="note" hidden={!open}>
    <strong>{term}</strong> — {definition}
    {#if moreHref}<a href={moreHref}>{moreLabel}</a>{/if}
  </span>
</span>

<style>
  .term { position: relative; display: inline; }
  button {
    all: unset; cursor: help; border-bottom: 1.5px dotted var(--color-link); color: inherit;
  }
  button:focus-visible { outline: 3px solid var(--color-focus); outline-offset: 2px; }
  .pop {
    position: absolute; left: 0; top: calc(100% + 6px); z-index: var(--z-popover); width: min(320px, 80vw);
    padding: var(--space-3); background: var(--color-bg); color: var(--color-text);
    border: 1px solid var(--color-rule); border-radius: var(--radius-card); box-shadow: var(--shadow-2);
    font: var(--step--1) / 1.5 var(--font-sans);
  }
  .pop a { display: block; margin-top: var(--space-2); }
</style>
