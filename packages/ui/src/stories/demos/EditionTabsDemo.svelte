<script lang="ts">
  import EditionTabs from '../../components/EditionTabs.svelte';
  import SourceQuote from '../../components/SourceQuote.svelte';
  import { L, SAMPLE_PASSAGE } from '../fixtures';
  const editions = [
    { id: 'hunter', label: 'Hunter', year: '1877', source: 'Sample source A' },
    { id: 'omalley', label: "O'Malley", year: '1908', source: 'Sample source B' },
    { id: 'igi', label: 'Imperial Gazetteer', year: '1908', source: 'Sample source C' },
  ];
</script>

<EditionTabs label="Editions" {editions}>
  {#snippet panel(e)}
    <SourceQuote text={SAMPLE_PASSAGE} highlight={{ start: 62, end: 106 }} source={e.source} edition={e.year} page="00" labels={L.quote} citation="Sample citation" permalink="#" scanHref="#" />
  {/snippet}
</EditionTabs>
