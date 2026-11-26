<script lang="ts">
  // Spec §11.1 signature interaction: archival evidence in Then, modern data in Now.
  // Native radios: keyboard (arrows) and screen readers work without extra ARIA.
  interface Props {
    value?: 'then' | 'now';
    label: string;
    labels: { then: string; now: string };
    onchange?: (v: 'then' | 'now') => void;
  }
  let { value = $bindable('then'), label, labels, onchange }: Props = $props();
  const name = $props.id();
</script>

<fieldset class="toggle">
  <legend class="visually-hidden">{label}</legend>
  {#each ['then', 'now'] as const as v (v)}
    <label class:on={value === v}>
      <input type="radio" {name} value={v} checked={value === v} onchange={() => { value = v; onchange?.(v); }} />
      <span>{labels[v]}</span>
    </label>
  {/each}
  <span class="thumb" class:right={value === 'now'} aria-hidden="true"></span>
</fieldset>

<style>
  .toggle {
    position: relative; display: inline-grid; grid-template-columns: 1fr 1fr; margin: 0; padding: 3px; min-width: 0;
    border: 1.5px solid var(--color-text); border-radius: var(--radius-pill);
  }
  label { position: relative; z-index: 1; display: grid; place-items: center; min-height: 40px; padding: 0 var(--space-4); cursor: pointer; font-weight: 600; border-radius: var(--radius-pill); transition: color var(--dur-sm) var(--ease-out); }
  label.on { color: var(--color-bg); }
  input { position: absolute; opacity: 0; inset: 0; margin: 0; cursor: pointer; }
  label:has(input:focus-visible) { outline: 3px solid var(--color-focus); outline-offset: 2px; }
  .thumb {
    position: absolute; top: 3px; bottom: 3px; left: 3px; width: calc(50% - 3px);
    background: var(--color-text); border-radius: var(--radius-pill);
    transition: transform var(--dur-md) var(--ease-out);
  }
  .thumb.right { transform: translateX(100%); }
  @media (forced-colors: active) { label.on { outline: 2px solid Highlight; } .thumb { display: none; } }
</style>
