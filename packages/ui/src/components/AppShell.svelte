<script lang="ts">
  import type { Snippet } from 'svelte';
  // Page frame: skip link, header, main landmark, footer. Mode sets Then/Now tokens for the subtree.
  interface Props { skipLabel: string; mode?: 'then' | 'now'; header: Snippet; children: Snippet; footer: Snippet }
  let { skipLabel, mode = 'then', header, children, footer }: Props = $props();
</script>

<div class="shell" data-mode={mode}>
  <a class="skip-link" href="#main">{skipLabel}</a>
  {@render header()}
  <main id="main" tabindex="-1">{@render children()}</main>
  {@render footer()}
</div>

<style>
  .shell { min-height: 100vh; display: flex; flex-direction: column; }
  main { flex: 1; outline: none; }
</style>
