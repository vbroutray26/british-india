<script lang="ts">
  import type { Lang } from './types';
  // FR-HOME-10 / FR-LANG-02: always visible; links go to the same page in the other language.
  interface Props { label: string; current: Lang; items: { lang: Lang; name: string; href: string }[] }
  let { label, current, items }: Props = $props();
</script>

<nav aria-label={label} class="switch">
  <ul>
    {#each items as it (it.lang)}
      <li>
        <a href={it.href} hreflang={it.lang} lang={it.lang} aria-current={it.lang === current ? 'true' : undefined} class:sys={it.lang !== current}>{it.name}</a>
      </li>
    {/each}
  </ul>
</nav>

<style>
  ul { list-style: none; margin: 0; padding: 0; display: flex; gap: var(--space-1); }
  a {
    display: inline-flex; align-items: center; min-height: 44px; min-width: 44px; padding-inline: var(--space-3);
    border-radius: var(--radius-control); text-decoration: none; font-weight: 500;
  }
  a:hover { background: var(--color-surface); }
  a[aria-current] { color: var(--color-text); box-shadow: inset 0 0 0 1.5px var(--color-text); }
  /* Other-language names use device fonts so they don't pull in a whole script's web font (NFR-PERF-08). */
  .sys { font-family: system-ui, -apple-system, 'Segoe UI', 'Noto Sans Oriya', 'Noto Sans Devanagari', sans-serif; }
</style>
