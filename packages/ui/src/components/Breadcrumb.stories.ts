import type { Meta, StoryObj } from '@storybook/svelte-vite';
import Breadcrumb from './Breadcrumb.svelte';

const meta = {
  title: 'Primitives/Breadcrumb',
  component: Breadcrumb,
  tags: ['autodocs'],
  args: { label: 'Breadcrumb', items: [{ text: 'India', href: '#' }, { text: 'Odisha', href: '#' }, { text: 'Puri district', href: '#' }, { text: 'Puri' }] },
} satisfies Meta<typeof Breadcrumb>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
