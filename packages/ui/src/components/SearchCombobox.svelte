<script lang="ts">
  import Icon from './Icon.svelte';
  // FR-SRCH-01..03, AC-SRCH-01: WAI-ARIA 1.2 combobox with list autocomplete.
  // Without JavaScript it is a plain GET form to the search page (FR-HOME-12).
  import type { SearchOption } from './types';
  interface Props {
    label: string;
    placeholder: string;
    action: string;
    name?: string;
    search: (q: string) => Promise<SearchOption[]> | SearchOption[];
    labels: { submit: string; noResults: string; results: (n: number) => string; matched: string };
    onselect?: (o: SearchOption) => void;
    size?: 'md' | 'lg';
  }
  let { label, placeholder, action, name = 'q', search, labels, onselect, size = 'md' }: Props = $props();
  const id = $props.id();
  let q = $state('');
  let options: SearchOption[] = $state([]);
  let open = $state(false);
  let active = $state(-1);
  let status = $state('');
  let timer: ReturnType<typeof setTimeout> | undefined;
  let seq = 0;

  function oninput() {
    clearTimeout(timer);
    const query = q.trim();
    if (!query) { options = []; open = false; status = ''; return; }
    timer = setTimeout(async () => {
      const mine = ++seq;
      const res = await search(query);
      if (mine !== seq) return; // a newer query superseded this one
      options = res; active = -1; open = true;
      status = res.length ? labels.results(res.length) : labels.noResults;
    }, 120);
  }
  function choose(o: SearchOption) {
    open = false;
    q = o.name;
    if (onselect) onselect(o); else window.location.assign(o.href);
  }
  function onkeydown(e: KeyboardEvent) {
    if (e.key === 'ArrowDown') { e.preventDefault(); if (!open && options.length) open = true; active = Math.min(active + 1, options.length - 1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); active = Math.max(active - 1, -1); }
    else if (e.key === 'Enter' && open && active >= 0) { e.preventDefault(); choose(options[active]); }
    else if (e.key === 'Escape') { if (open) { e.preventDefault(); open = false; active = -1; } else q = ''; }
  }
</script>

<form class="search {size}" role="search" {action} method="get" onsubmit={(e) => { if (open && active >= 0) { e.preventDefault(); choose(options[active]); } }}>
  <label for="{id}-input" class="visually-hidden">{label}</label>
  <div class="field">
    <Icon name="search" />
    <input
      id="{id}-input" {name} type="search" autocomplete="off" spellcheck="false" {placeholder}
      role="combobox" aria-autocomplete="list" aria-expanded={open} aria-controls="{id}-list"
      aria-activedescendant={open && active >= 0 ? `${id}-opt-${active}` : undefined}
      bind:value={q} {oninput} {onkeydown} onblur={() => setTimeout(() => (open = false), 150)}
    />
    <button type="submit" class="go" aria-label={labels.submit}><Icon name="arrow-right" /></button>
  </div>
  <ul id="{id}-list" role="listbox" aria-label={label} hidden={!open || !options.length}>
    {#each options as o, i (o.id)}
      <li id="{id}-opt-{i}" role="option" aria-selected={i === active} onpointerdown={(e) => { e.preventDefault(); choose(o); }} onmousemove={() => (active = i)}>
        <span class="name">{o.name}</span>
        {#if o.matched && o.matched !== o.name}<span class="matched">{labels.matched}: <i>{o.matched}</i></span>{/if}
        <span class="meta">{o.type}{#if o.district} · {o.district}{/if}</span>
      </li>
    {/each}
  </ul>
  <p class="visually-hidden" role="status" aria-live="polite">{status}</p>
</form>

<style>
  .search { position: relative; }
  .field {
    display: flex; align-items: center; gap: var(--space-2); padding-left: var(--space-4);
    background: var(--color-bg); border: 1.5px solid var(--color-text); border-radius: var(--radius-pill);
    box-shadow: var(--shadow-1);
  }
  .field:focus-within { outline: 3px solid var(--color-focus); outline-offset: 2px; }
  input { flex: 1; min-width: 0; min-height: 48px; border: 0; background: transparent; outline: none; font-size: var(--step-0); }
  input::-webkit-search-cancel-button { display: none; }
  .lg input { min-height: 60px; font-size: var(--step-1); }
  .go { display: grid; place-items: center; width: 44px; height: 44px; margin: 2px; border: 0; border-radius: 50%; background: var(--color-accent); color: var(--color-on-accent); cursor: pointer; }
  .lg .go { width: 54px; height: 54px; }
  .go:focus-visible { outline: 3px solid var(--color-focus); outline-offset: 2px; }
  ul {
    position: absolute; left: 0; right: 0; top: calc(100% + 6px); z-index: var(--z-popover); margin: 0; padding: var(--space-1);
    list-style: none; background: var(--color-bg); border: 1px solid var(--color-rule); border-radius: var(--radius-card); box-shadow: var(--shadow-3);
    max-height: min(60vh, 420px); overflow-y: auto;
  }
  li { display: grid; gap: 2px; padding: var(--space-2) var(--space-3); border-radius: var(--radius-control); cursor: pointer; }
  li[aria-selected='true'] { background: var(--color-surface); box-shadow: inset 3px 0 0 var(--color-accent); }
  .name { font-weight: 600; }
  .matched, .meta { font-size: var(--step--1); color: var(--color-text-muted); }
</style>
