<script lang="ts">
  import Badge from './Badge.svelte';
  // US-16 / FR-PLACE-04: every fact shows whether a human reviewed it. Shape + text, never colour alone.
  interface Props {
    status: 'accepted' | 'edited' | 'unreviewed' | 'rejected';
    labels: { reviewed: string; unreviewed: string };
    reviewer?: string;
    date?: string;
  }
  let { status, labels, reviewer, date }: Props = $props();
  const ok = $derived(status === 'accepted' || status === 'edited');
  const detail = $derived(ok && (reviewer || date) ? [reviewer, date].filter(Boolean).join(', ') : undefined);
</script>

<Badge text={ok ? labels.reviewed : labels.unreviewed} tone={ok ? 'reviewed' : 'pending'} icon={ok ? 'reviewed' : 'pending'} {detail} />
