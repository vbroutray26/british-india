import type { Meta, StoryObj } from '@storybook/svelte-vite';
import EmptyState from './EmptyState.svelte';

const meta = {
  title: 'Primitives/EmptyState',
  component: EmptyState,
  tags: ['autodocs'],
  args: { title: 'Not recorded in these sources', body: 'The 1908 gazetteer does not give a figure for this place.', icon: 'source' },
} satisfies Meta<typeof EmptyState>;
export default meta;
type Story = StoryObj<typeof meta>;

export const NoData: Story = {};
export const NoResults: Story = { args: { title: 'No places found', body: 'Try an old spelling, or search in Odia or Hindi.', icon: 'search', action: { text: 'Browse the map', href: '#' } } };
export const Offline: Story = { args: { title: 'You are offline', body: 'Pages you have visited are still available.', icon: 'globe' } };
