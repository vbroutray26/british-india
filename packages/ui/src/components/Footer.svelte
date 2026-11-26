<script lang="ts">
  // FR-HOME-13: About, Sources, Credits, Methods, Data, Corrections, Takedown, Cite.
  interface Props {
    navLabel: string;
    links: { text: string; href: string }[];
    licence: string;
    contact?: { text: string; href: string };
  }
  let { navLabel, links, licence, contact }: Props = $props();
</script>

<footer class="footer">
  <div class="inner">
    <span class="mark" aria-hidden="true"></span>
    <nav aria-label={navLabel}>
      <ul>{#each links as l (l.href)}<li><a href={l.href}>{l.text}</a></li>{/each}</ul>
    </nav>
    <p class="licence">{licence}{#if contact} · <a href={contact.href}>{contact.text}</a>{/if}</p>
  </div>
</footer>

<style>
  .footer { margin-top: var(--space-24); border-top: 1px solid var(--color-rule); color: var(--color-text-muted); font-size: var(--step--1); }
  .inner { max-width: var(--layout-container); margin-inline: auto; padding: var(--space-8) var(--layout-gutter-sm); display: grid; gap: var(--space-4); }
  .mark {
    display: block; height: 72px; aspect-ratio: 520 / 477; background-color: var(--color-text-muted);
    -webkit-mask: url('/brand/logo-lite.svg') left center / contain no-repeat; mask: url('/brand/logo-lite.svg') left center / contain no-repeat;
  }
  ul { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 0 var(--space-2); }
  a { display: inline-flex; align-items: center; min-height: 44px; padding-inline: var(--space-1); }
  .licence { margin: 0; }
</style>
