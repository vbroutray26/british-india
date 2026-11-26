<script lang="ts">
  // FR-DISC-03: curated sequences of places with a narrative.
  interface Props { step: number; total: number; place: string; href: string; narrative: string; labels: { step: string; of: string; open: string } }
  let { step, total, place, href, narrative, labels }: Props = $props();
</script>

<article class="step">
  <p class="n"><span aria-hidden="true">{String(step).padStart(2, '0')}</span><span class="visually-hidden">{labels.step} {step} {labels.of} {total}</span></p>
  <div>
    <h3>{place}</h3>
    <p>{narrative}</p>
    <a {href}>{labels.open} {place}</a>
  </div>
</article>

<style>
  .step { display: grid; grid-template-columns: auto 1fr; gap: var(--space-4); padding: var(--space-4) 0; border-top: 1px solid var(--color-rule); }
  .n { margin: 0; font-family: var(--font-display); font-size: var(--step-4); line-height: 1; color: var(--color-accent); font-variant-numeric: lining-nums; }
  h3 { margin: 0 0 var(--space-2); font-size: var(--step-2); }
  p { margin: 0 0 var(--space-2); }
  a { font-weight: 600; }
</style>
