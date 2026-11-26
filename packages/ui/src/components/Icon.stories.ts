import type { Meta, StoryObj } from '@storybook/svelte-vite';
import Icon from './Icon.svelte';
import IconGallery from './IconGallery.svelte';
import { ICON_NAMES } from './icons';

const meta = {
  title: 'Foundations/Icons',
  component: Icon,
  tags: ['autodocs'],
  args: { name: 'temple', size: 24 },
  argTypes: { name: { control: 'select', options: ICON_NAMES } },
} satisfies Meta<typeof Icon>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Single: Story = {};
export const Labelled: Story = { args: { name: 'reviewed', label: 'Reviewed' } };
export const Gallery: StoryObj = { render: () => ({ Component: IconGallery }) };
