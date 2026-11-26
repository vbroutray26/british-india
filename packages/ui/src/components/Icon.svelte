<script lang="ts">
  import { ICONS, type IconName } from './icons';
  interface Props {
    name: IconName;
    /** Pixel size; defaults to 24 (spec §11.2 icon grid). */
    size?: number;
    /** Accessible name. Omit for decorative icons next to visible text. */
    label?: string;
  }
  let { name, size = 24, label }: Props = $props();
</script>

<svg
  class="icon"
  width={size}
  height={size}
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="1.5"
  stroke-linecap="round"
  stroke-linejoin="round"
  role={label ? 'img' : undefined}
  aria-label={label}
  aria-hidden={label ? undefined : 'true'}
  focusable="false"
>{@html ICONS[name]}</svg>

<style>
  .icon { flex: none; display: inline-block; vertical-align: middle; }
</style>
