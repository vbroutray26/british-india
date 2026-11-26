import type { Meta, StoryObj } from '@storybook/svelte-vite';
import Demo from '../stories/demos/TooltipDemo.svelte';

const meta = { title: 'Primitives/Tooltip', component: Demo, tags: ['autodocs'] } satisfies Meta<typeof Demo>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: {} };
