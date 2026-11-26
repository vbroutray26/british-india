<script lang="ts">
  import Header from '../../components/Header.svelte';
  import SearchCombobox from '../../components/SearchCombobox.svelte';
  import { L, searchSample } from '../fixtures';
  let { lang = 'en' as 'en' | 'or' | 'hi' } = $props();
  const T = { en: 'Towns of British India', or: 'ବ୍ରିଟିଶ ଭାରତର ନଗର', hi: 'ब्रिटिश भारत के नगर' };
</script>

<Header homeHref="#" siteTitle={T[lang]} showTitle={lang !== 'en'} {lang} languageLabel="Language"
  languages={[{ lang: 'en', name: 'English', href: '#en' }, { lang: 'or', name: 'ଓଡ଼ିଆ', href: '#or' }, { lang: 'hi', name: 'हिन्दी', href: '#hi' }]}>
  {#snippet search()}<SearchCombobox label="Search places" placeholder="Search a town, river or temple" action="#" search={searchSample} labels={L.search} onselect={() => {}} />{/snippet}
</Header>
