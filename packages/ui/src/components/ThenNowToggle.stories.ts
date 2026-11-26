import type { Meta, StoryObj } from '@storybook/svelte-vite';
import ThenNowToggle from './ThenNowToggle.svelte';

const meta = {
  title: 'Shell/ThenNowToggle',
  component: ThenNowToggle,
  tags: ['autodocs'],
  args: { label: 'View', labels: { then: 'Then', now: 'Now' }, value: 'then' },
} satisfies Meta<typeof ThenNowToggle>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Then: Story = {};
export const Now: Story = { args: { value: 'now' } };
export const Odia: Story = { args: { labels: { then: 'ଅତୀତ', now: 'ବର୍ତ୍ତମାନ' } } };
