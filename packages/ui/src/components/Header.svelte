<script lang="ts">
  import type { Snippet } from 'svelte';
  import LanguageSwitcher from './LanguageSwitcher.svelte';
  import type { Lang } from './types';
  // Spec §11.5 header: logo · search · [EN | ଓଡ଼ | हि] · menu.
  interface Props {
    homeHref: string;
    siteTitle: string;
    /** Show the title as text beside the logo (Odia/Hindi pages: the logo artwork is English). */
    showTitle?: boolean;
    lang: Lang;
    languages: { lang: Lang; name: string; href: string }[];
    languageLabel: string;
    search?: Snippet;
    actions?: Snippet;
  }
  let { homeHref, siteTitle, showTitle = false, lang, languages, languageLabel, search, actions }: Props = $props();
</script>

<header class="header">
  <div class="bar">
    <a class="brand" href={homeHref}>
      <span class="mark" aria-hidden="true"></span>
      <span class={showTitle ? 'name' : 'visually-hidden'}>{siteTitle}</span>
    </a>
    {#if search}<div class="search">{@render search()}</div>{/if}
    <div class="end">
      <LanguageSwitcher label={languageLabel} current={lang} items={languages} />
      {@render actions?.()}
    </div>
  </div>
</header>

<style>
  .header { border-bottom: 1px solid var(--color-rule); background: var(--color-bg); }
  .bar {
    max-width: var(--layout-container); margin-inline: auto; padding: var(--space-2) var(--layout-gutter-sm);
    display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-3) var(--space-4); min-height: var(--layout-header-h);
  }
  .brand { display: inline-flex; align-items: center; gap: var(--space-3); color: var(--color-text); text-decoration: none; min-height: 44px; }
  .mark {
    display: block; height: 52px; aspect-ratio: 520 / 477; background-color: var(--color-text);
    -webkit-mask: url('/brand/logo-lite.svg') center / contain no-repeat; mask: url('/brand/logo-lite.svg') center / contain no-repeat;
  }
  .name { font-family: var(--font-display); font-size: var(--step-1); }
  .search { flex: 1 1 260px; max-width: 520px; }
  .end { margin-left: auto; display: flex; align-items: center; gap: var(--space-2); }
  @media (forced-colors: active) { .mark { forced-color-adjust: none; background-color: CanvasText; } }
</style>
