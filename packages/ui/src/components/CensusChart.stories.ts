import type { Meta, StoryObj } from '@storybook/svelte-vite';
import CensusChart from './CensusChart.svelte';
import { L, SAMPLE_PASSAGE, SAMPLE_CENSUS, SAMPLE_IMAGES, searchSample, placeholderImage } from '../stories/fixtures';

const meta = {
  title: 'Data/CensusChart',
  component: CensusChart,
  tags: ['autodocs'],
  args: { title: 'Sample census series', description: 'Sample data showing two boundary versions and one approximate estimate.', points: SAMPLE_CENSUS, selectedYear: 1901, labels: L.chart },
} satisfies Meta<typeof CensusChart>;
export default meta;
type Story = StoryObj<typeof meta>;

export const BoundaryAware: Story = {};
export const Hindi: Story = { args: { locale: 'hi-IN' } };
