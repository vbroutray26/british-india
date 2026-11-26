import type { Meta, StoryObj } from '@storybook/svelte-vite';
import ThemeCard from './ThemeCard.svelte';

const meta = {
  title: 'Content/ThemeCard',
  component: ThemeCard,
  tags: ['autodocs'],
  args: { icon: 'flood', title: 'Floods', blurb: 'Rivers, embankments and the years the water came.', href: '#', count: '00 places' },
} satisfies Meta<typeof ThemeCard>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Floods: Story = {};
export const Railways: Story = { args: { icon: 'railway', title: 'Railways', blurb: 'When the line arrived and what it changed.' } };
