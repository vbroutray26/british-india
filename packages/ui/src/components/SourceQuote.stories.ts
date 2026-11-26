import type { Meta, StoryObj } from '@storybook/svelte-vite';
import SourceQuote from './SourceQuote.svelte';
import { L, SAMPLE_PASSAGE, SAMPLE_CENSUS, SAMPLE_IMAGES, searchSample, placeholderImage } from '../stories/fixtures';

const meta = {
  title: 'Content/SourceQuote',
  component: SourceQuote,
  tags: ['autodocs'],
  args: { text: SAMPLE_PASSAGE, highlight: { start: 62, end: 106 }, source: 'Sample source', edition: '1908', page: '00', permalink: '#', scanHref: '#', citation: 'Sample citation string', labels: L.quote },
} satisfies Meta<typeof SourceQuote>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
export const NoHighlight: Story = { args: { highlight: undefined } };
