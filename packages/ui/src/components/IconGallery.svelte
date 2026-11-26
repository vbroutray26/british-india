<script lang="ts">
  import Icon from './Icon.svelte';
  import { ICON_NAMES } from './icons';
</script>

<ul class="gallery">
  {#each ICON_NAMES as name (name)}
    <li><Icon {name} size={32} /><code>{name}</code></li>
  {/each}
</ul>

<style>
  .gallery { list-style: none; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(112px, 1fr)); gap: var(--space-2); }
  li { display: grid; justify-items: center; gap: var(--space-2); padding: var(--space-4) var(--space-2); border: 1px solid var(--color-rule); border-radius: var(--radius-card); }
  code { font: var(--step--1) var(--font-mono); color: var(--color-text-muted); }
</style>
