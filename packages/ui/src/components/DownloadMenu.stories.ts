import type { Meta, StoryObj } from '@storybook/svelte-vite';
import DownloadMenu from './DownloadMenu.svelte';

const meta = {
  title: 'Data/DownloadMenu',
  component: DownloadMenu,
  tags: ['autodocs'],
  args: { label: 'Download data', items: [{ text: 'JSON', href: '#a.json', meta: '120 KB' }, { text: 'CSV', href: '#a.csv', meta: '48 KB' }, { text: 'GeoJSON', href: '#a.geojson', meta: '210 KB' }, { text: 'Data dictionary', href: '#dict' }] },
} satisfies Meta<typeof DownloadMenu>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
