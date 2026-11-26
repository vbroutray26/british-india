import type { Meta, StoryObj } from '@storybook/svelte-vite';
import Badge from './Badge.svelte';

const meta = {
  title: 'Primitives/Badge',
  component: Badge,
  tags: ['autodocs'],
  args: { text: 'Reviewed', tone: 'reviewed', icon: 'reviewed' },
} satisfies Meta<typeof Badge>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Reviewed: Story = {};
export const Pending: Story = { args: { text: 'Not yet reviewed', tone: 'pending', icon: 'pending' } };
export const AI: Story = { args: { text: 'Written by AI', tone: 'ai', icon: 'ai' } };
export const Warning: Story = { args: { text: 'Approximate', tone: 'warning', icon: 'warning' } };
export const Neutral: Story = { args: { text: 'Ghost place', icon: 'ghost', tone: 'neutral' } };
