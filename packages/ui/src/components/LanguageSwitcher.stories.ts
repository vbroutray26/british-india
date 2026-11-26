import type { Meta, StoryObj } from '@storybook/svelte-vite';
import LanguageSwitcher from './LanguageSwitcher.svelte';

const meta = {
  title: 'Shell/LanguageSwitcher',
  component: LanguageSwitcher,
  tags: ['autodocs'],
  args: { label: 'Language', current: 'en', items: [{ lang: 'en', name: 'English', href: '#' }, { lang: 'or', name: 'ଓଡ଼ିଆ', href: '#' }, { lang: 'hi', name: 'हिन्दी', href: '#' }] },
} satisfies Meta<typeof LanguageSwitcher>;
export default meta;
type Story = StoryObj<typeof meta>;

export const English: Story = {};
export const Odia: Story = { args: { current: 'or' } };
