import type { Meta, StoryObj } from '@storybook/svelte-vite';
import SearchResults from './SearchResults.svelte';
import { L, SAMPLE_RESULTS } from '../stories/fixtures';

const meta = {
  title: 'Search/SearchResults',
  component: SearchResults,
  tags: ['autodocs'],
  args: { label: 'Passages', query: 'cyclone', state: 'done', results: SAMPLE_RESULTS, labels: L.results },
} satisfies Meta<typeof SearchResults>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
export const NoMatches: Story = { args: { query: 'zzz', results: [] } };
export const Searching: Story = { args: { state: 'loading', results: [] } };
