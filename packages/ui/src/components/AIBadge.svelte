<script lang="ts">
  import Badge from './Badge.svelte';
  // FR-PLACE-05 / FR-ASK-08: machine-written text is always labelled.
  interface Props { text: string; detail?: string }
  let { text, detail }: Props = $props();
</script>

<Badge {text} tone="ai" icon="ai" {detail} />
