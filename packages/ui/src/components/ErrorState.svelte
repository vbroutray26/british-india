<script lang="ts">
  import EmptyState from './EmptyState.svelte';
  // NFR-REL-01: failures degrade to a clear message plus a working alternative (e.g. keyword search).
  interface Props { title: string; body?: string; action?: { text: string; href: string } }
  let { title, body, action }: Props = $props();
</script>

<EmptyState {title} {body} {action} icon="warning" tone="error" />
