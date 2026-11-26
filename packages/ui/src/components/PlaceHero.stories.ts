import type { Meta, StoryObj } from '@storybook/svelte-vite';
import PlaceHero from './PlaceHero.svelte';

const meta = {
  title: 'Content/PlaceHero',
  component: PlaceHero,
  tags: ['autodocs'],
  args: { name: 'Puri', names: [{ text: 'ପୁରୀ', lang: 'or' }, { text: 'पुरी', lang: 'hi' }], oldSpellings: ['Pooree', 'Jagannáth'], type: 'town', districtThen: 'Puri', districtNow: 'Puri', coords: '19°48′N 85°49′E', tagline: 'Sample tagline (reviewed, ≤ 120 characters).', breadcrumb: { label: 'Breadcrumb', items: [{ text: 'India', href: '#' }, { text: 'Odisha', href: '#' }, { text: 'Puri' }] }, labels: { oldSpellings: 'Old spellings', then: 'Then', now: 'Now' } },
} satisfies Meta<typeof PlaceHero>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
export const Ghost: Story = { args: { name: 'Sample lost village', names: [], oldSpellings: [], tagline: undefined, ghost: { title: 'No longer exists', body: 'Best-known location from the 1908 heading coordinates.' } } };
