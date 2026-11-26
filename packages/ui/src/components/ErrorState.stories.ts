import type { Meta, StoryObj } from '@storybook/svelte-vite';
import ErrorState from './ErrorState.svelte';

const meta = {
  title: 'Primitives/ErrorState',
  component: ErrorState,
  tags: ['autodocs'],
  args: { title: 'Search is unavailable', body: 'You can still browse places from the map or the list.', action: { text: 'Open the list', href: '#' } },
} satisfies Meta<typeof ErrorState>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
