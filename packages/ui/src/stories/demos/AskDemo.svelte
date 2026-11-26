<script lang="ts">
  import AskPanel from '../../components/AskPanel.svelte';
  import AnswerBlock from '../../components/AnswerBlock.svelte';
  import { L } from '../fixtures';
  let { mode = 'answer' as 'answer' | 'unanswerable' | 'passages-only' } = $props();
  let status: 'idle' | 'loading' | 'answered' | 'passages-only' = $state('idle');
  function onask() {
    status = 'loading';
    setTimeout(() => (status = mode === 'passages-only' ? 'passages-only' : 'answered'), 700);
  }
</script>

<AskPanel label="Ask the Gazetteer" placeholder="e.g. When did the railway reach Puri?" samples={['When did the railway reach Puri?', 'What crops were grown near Chilika?']}
  {status} notice="Today's AI answers are used up. Showing the most relevant passages instead." {onask} labels={L.ask}>
  {#snippet answer()}
    {#if status === 'answered' || status === 'passages-only'}
      <AnswerBlock labels={L.answer} reportHref="#" unanswerable={mode !== 'answer'}
        sentences={mode === 'answer' ? [{ text: 'Sample answer sentence written only from the cited passage.', citations: [{ text: 'Sample 1908, p. 00', href: '#', quote: 'sample supporting quote' }] }] : []}
        nearest={[{ text: 'Sample nearest passage text.', source: 'Sample source, p. 00', href: '#' }]} />
    {/if}
  {/snippet}
</AskPanel>
