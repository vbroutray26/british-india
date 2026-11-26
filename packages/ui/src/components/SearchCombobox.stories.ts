import type { Meta, StoryObj } from '@storybook/svelte-vite';
import SearchCombobox from './SearchCombobox.svelte';
import { L, SAMPLE_PASSAGE, SAMPLE_CENSUS, SAMPLE_IMAGES, searchSample, placeholderImage } from '../stories/fixtures';

const meta = {
  title: 'Interactive/SearchCombobox',
  component: SearchCombobox,
  tags: ['autodocs'],
  args: { label: 'Search places', placeholder: 'Search a town, river or temple', action: '#', search: searchSample, labels: L.search, onselect: () => {} },
} satisfies Meta<typeof SearchCombobox>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
export const Large: Story = { args: { size: 'lg' } };
export const Hindi: Story = { args: { placeholder: 'कस्बा, नदी या मंदिर खोजें' } };
