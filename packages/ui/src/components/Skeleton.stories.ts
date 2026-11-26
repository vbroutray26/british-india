import type { Meta, StoryObj } from '@storybook/svelte-vite';
import Skeleton from './Skeleton.svelte';

const meta = {
  title: 'Primitives/Skeleton',
  component: Skeleton,
  tags: ['autodocs'],
  args: { variant: 'text', lines: 4 },
} satisfies Meta<typeof Skeleton>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Text: Story = {};
export const Card: Story = { args: { variant: 'card' } };
export const Block: Story = { args: { variant: 'block' } };
export const Circle: Story = { args: { variant: 'circle' } };
