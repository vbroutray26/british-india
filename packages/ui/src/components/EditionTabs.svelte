<script lang="ts">
  import type { Snippet } from 'svelte';
  import Tabs from './Tabs.svelte';
  // FR-TIME-02 / FR-PLACE-06: one tab per edition (Hunter 1870s, O'Malley 1908, Imperial…).
  interface Edition { id: string; label: string; year: string; source: string }
  interface Props { label: string; editions: Edition[]; selected?: string; panel: Snippet<[Edition]> }
  let { label, editions, selected = $bindable(editions[0]?.id), panel }: Props = $props();
  const items = $derived(editions.map((e) => ({ ...e, label: `${e.label} · ${e.year}` })));
</script>

<Tabs {label} {items} bind:selected panel={panel as any} />
