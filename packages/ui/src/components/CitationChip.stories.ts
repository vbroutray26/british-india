import type { Meta, StoryObj } from '@storybook/svelte-vite';
import CitationChip from './CitationChip.svelte';

const meta = {
  title: 'Content/CitationChip',
  component: CitationChip,
  tags: ['autodocs'],
  args: { text: 'Sample 1908, p. 00', href: '#', quote: 'sample supporting quote' },
} satisfies Meta<typeof CitationChip>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
