import type { Meta, StoryObj } from '@storybook/svelte-vite';
import Tabs from './Tabs.svelte';

const meta = {
  title: 'Primitives/Tabs',
  component: Tabs,
  tags: ['autodocs'],
  args: { label: 'Sections', items: [{ id: 'a', label: 'Summary', content: 'Summary panel' }, { id: 'b', label: 'Original text', content: 'Original text panel' }, { id: 'c', label: 'Census', content: 'Census panel' }] },
} satisfies Meta<typeof Tabs>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
