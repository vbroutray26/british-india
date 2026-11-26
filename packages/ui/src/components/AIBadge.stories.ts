import type { Meta, StoryObj } from '@storybook/svelte-vite';
import AIBadge from './AIBadge.svelte';

const meta = {
  title: 'Content/AIBadge',
  component: AIBadge,
  tags: ['autodocs'],
  args: { text: 'Written by AI from the passages below' },
} satisfies Meta<typeof AIBadge>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
export const Odia: Story = { args: { text: 'ତଳ ଅଂଶରୁ AI ଦ୍ୱାରା ଲିଖିତ' } };
