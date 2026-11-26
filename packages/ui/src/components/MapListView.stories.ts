import type { Meta, StoryObj } from '@storybook/svelte-vite';
import MapListView from './MapListView.svelte';

const meta = {
  title: 'Data/MapListView',
  component: MapListView,
  tags: ['autodocs'],
  args: { label: 'Places on this map', emptyText: 'Nothing on the map here', items: [{ name: 'Puri', type: 'town', icon: 'admin', href: '#' }, { name: 'Konark', type: 'temple', icon: 'temple', href: '#' }, { name: 'Sample lost village', type: 'village', icon: 'ghost', href: '#', note: 'Ghost place' }] },
} satisfies Meta<typeof MapListView>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
export const Empty: Story = { args: { items: [] } };
