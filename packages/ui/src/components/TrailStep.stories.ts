import type { Meta, StoryObj } from '@storybook/svelte-vite';
import TrailStep from './TrailStep.svelte';

const meta = {
  title: 'Content/TrailStep',
  component: TrailStep,
  tags: ['autodocs'],
  args: { step: 1, total: 6, place: 'Sample place', href: '#', narrative: 'Sample narrative for the first stop on a trail.', labels: { step: 'Step', of: 'of', open: 'Open' } },
} satisfies Meta<typeof TrailStep>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
