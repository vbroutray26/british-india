<script lang="ts">
  import AppShell from '../../components/AppShell.svelte';
  import Footer from '../../components/Footer.svelte';
  import HeaderDemo from './HeaderDemo.svelte';
  let { mode = 'then' as 'then' | 'now' } = $props();
</script>

<AppShell skipLabel="Skip to content" {mode}>
  {#snippet header()}<HeaderDemo />{/snippet}
  <div class="container reading"><h1 class="t-h1">Page content</h1><p class="t-lede">The shell provides the skip link, landmarks and the Then/Now mode for everything inside.</p></div>
  {#snippet footer()}
    <Footer navLabel="Footer" licence="Code MIT · Data CC BY 4.0 · Third-party media excluded" contact={{ text: 'Contact', href: '#' }}
      links={['About', 'Sources', 'Credits', 'Methods', 'Data', 'Corrections', 'Takedown', 'Cite'].map((t) => ({ text: t, href: '#' + t.toLowerCase() }))} />
  {/snippet}
</AppShell>
