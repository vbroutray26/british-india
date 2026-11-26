import type { Meta, StoryObj } from '@storybook/svelte-vite';
import Footer from './Footer.svelte';

const meta = {
  title: 'Shell/Footer',
  component: Footer,
  tags: ['autodocs'],
  args: { navLabel: 'Footer', licence: 'Code MIT · Data CC BY 4.0 · Third-party media excluded', contact: { text: 'Contact', href: '#' }, links: ['About','Sources','Credits','Methods','Data','Corrections','Takedown','Cite'].map((t) => ({ text: t, href: '#' + t })) },
} satisfies Meta<typeof Footer>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
