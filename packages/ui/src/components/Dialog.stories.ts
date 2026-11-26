import type { Meta, StoryObj } from '@storybook/svelte-vite';
import Demo from '../stories/demos/DialogDemo.svelte';

const meta = { title: 'Primitives/Dialog', component: Demo, tags: ['autodocs'] } satisfies Meta<typeof Demo>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: {} };
