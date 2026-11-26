<script lang="ts">
  import CorrectionDialog from '../../components/CorrectionDialog.svelte';
  import ShareDialog from '../../components/ShareDialog.svelte';
  import ActionBar from '../../components/ActionBar.svelte';
  import { L, placeholderImage } from '../fixtures';
  let correct = $state(false);
  let share = $state(false);
  const onsubmit = async () => { await new Promise((r) => setTimeout(r, 600)); return { ok: true }; };
</script>

<ActionBar label="Page actions" labels={L.actions} onshare={() => (share = true)} oncite={() => {}} oncorrect={() => (correct = true)} onlisten={() => {}} />
<CorrectionDialog bind:open={correct} itemId="ft_sample_flood_1866" contactEmail="corrections@example.org" {onsubmit} labels={L.correction} />
<ShareDialog bind:open={share} url="https://example.org/en/place/puri-sample" title="Puri — Towns of British India" image={{ src: placeholderImage(1200, 630, 'Share card preview'), alt: 'Share card preview' }} labels={L.share} />
