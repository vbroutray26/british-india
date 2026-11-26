import type { Meta, StoryObj } from '@storybook/svelte-vite';
import Button from './Button.svelte';

const meta = {
  title: 'Primitives/Button',
  component: Button,
  tags: ['autodocs'],
  args: { text: 'Search', variant: 'secondary' },
  argTypes: {
    variant: { control: 'inline-radio', options: ['primary', 'secondary', 'ghost', 'danger'] },
    size: { control: 'inline-radio', options: ['md', 'sm'] },
  },
} satisfies Meta<typeof Button>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = { args: { variant: 'primary', text: 'Open passage', iconEnd: 'arrow-right' } };
export const Secondary: Story = {};
export const Ghost: Story = { args: { variant: 'ghost', text: 'Cite', icon: 'cite' } };
export const Danger: Story = { args: { variant: 'danger', text: 'Withdraw image' } };
export const IconOnly: Story = { args: { text: undefined, icon: 'share', label: 'Share' } };
export const Loading: Story = { args: { variant: 'primary', loading: true, loadingLabel: 'Loading', text: 'Asking' } };
export const Disabled: Story = { args: { disabled: true } };
export const Pressed: Story = { args: { text: 'Then', pressed: true } };
export const AsLink: Story = { args: { href: '#', text: 'View passage', iconEnd: 'arrow-right' } };
export const LongOdia: Story = { args: { text: 'ମୂଳ ପାଠ ଏବଂ ସ୍କାନ୍ ଦେଖନ୍ତୁ', variant: 'primary' } };
