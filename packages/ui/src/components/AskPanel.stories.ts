import type { Meta, StoryObj } from '@storybook/svelte-vite';
import Demo from '../stories/demos/AskDemo.svelte';

const meta = { title: 'Interactive/AskPanel', component: Demo, tags: ['autodocs'] } satisfies Meta<typeof Demo>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Answered: Story = { args: { mode: 'answer' } };
export const Unanswerable: Story = { args: { mode: 'unanswerable' } };
export const PassagesOnly: Story = { args: { mode: 'passages-only' } };
