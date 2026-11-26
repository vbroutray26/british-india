import type { Meta, StoryObj } from '@storybook/svelte-vite';
import TimeDial from './TimeDial.svelte';

const meta = {
  title: 'Interactive/TimeDial',
  component: TimeDial,
  tags: ['autodocs'],
  args: { label: 'Year', years: [1872, 1881, 1891, 1901, 1908, 1911, 1921, 1931, 2011], value: 1908, nowYear: 2011 },
} satisfies Meta<typeof TimeDial>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
export const Now: Story = { args: { value: 2011 } };
