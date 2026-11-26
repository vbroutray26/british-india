<script lang="ts">
  import Dialog from '../../components/Dialog.svelte';
  import Button from '../../components/Button.svelte';
  let open = $state(false);
</script>

<Button variant="primary" text="Open dialog" onclick={() => (open = true)} />
<Dialog bind:open title="How to read this record" closeLabel="Close" description="A short explainer, reachable from every place page.">
  <p>The gazetteers were written by colonial officials for administration and revenue. Read them as evidence of what officials recorded, not as plain truth.</p>
  {#snippet footer()}<Button variant="primary" text="Got it" onclick={() => (open = false)} />{/snippet}
</Dialog>
