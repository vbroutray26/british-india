<script lang="ts">
  import Toast from '../../components/Toast.svelte';
  import Button from '../../components/Button.svelte';
  import type { ToastItem } from '../../components/types';
  let toasts: ToastItem[] = $state([]);
  let n = 0;
</script>

<Button text="Show toast" onclick={() => (toasts = [...toasts, { id: String(++n), text: 'Citation copied', tone: 'success' }])} />
<Toast {toasts} dismissLabel="Dismiss" ondismiss={(id) => (toasts = toasts.filter((t) => t.id !== id))} />
