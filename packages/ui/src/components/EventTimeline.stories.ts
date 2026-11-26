import type { Meta, StoryObj } from '@storybook/svelte-vite';
import EventTimeline from './EventTimeline.svelte';

const meta = {
  title: 'Content/EventTimeline',
  component: EventTimeline,
  tags: ['autodocs'],
  args: { label: 'Events', events: [{ year: '18xx', icon: 'famine', title: 'Sample famine event', summary: 'Sample summary.', source: 'Sample source, p. 00', href: '#' }, { year: '18xx', icon: 'flood', title: 'Sample flood event', source: 'Sample source' }, { year: '18xx', icon: 'railway', title: 'Sample railway arrival' }] },
} satisfies Meta<typeof EventTimeline>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
