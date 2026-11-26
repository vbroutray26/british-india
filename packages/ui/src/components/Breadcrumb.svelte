<script lang="ts">
  interface Props { label: string; items: { text: string; href?: string }[] }
  let { label, items }: Props = $props();
</script>

<nav aria-label={label}>
  <ol>
    {#each items as item, i (i)}
      <li>
        {#if item.href && i < items.length - 1}<a href={item.href}>{item.text}</a>
        {:else}<span aria-current={i === items.length - 1 ? 'page' : undefined}>{item.text}</span>{/if}
      </li>
    {/each}
  </ol>
</nav>

<style>
  ol { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: var(--space-1) var(--space-2); font-size: var(--step--1); color: var(--color-text-muted); }
  li:not(:last-child)::after { content: '›'; margin-left: var(--space-2); }
  a { color: inherit; }
  [aria-current] { color: var(--color-text); font-weight: 600; }
</style>
