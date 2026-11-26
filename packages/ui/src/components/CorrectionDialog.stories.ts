import type { Meta, StoryObj } from '@storybook/svelte-vite';
import Demo from '../stories/demos/CorrectionDemo.svelte';

const meta = { title: 'Interactive/Correction and share', component: Demo, tags: ['autodocs'] } satisfies Meta<typeof Demo>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: {} };
